"""Provider-neutral, bounded subprocess execution owned by SSSF.

The supervisor deliberately accepts argv and an exact environment mapping.  It
never invokes a shell, inherits stdin, or consults the caller's environment.
Unix children get a new process group.  Windows is refused until a Job Object
implementation can make the same descendant-cleanup claim honestly.
"""

from __future__ import annotations

import errno
import hashlib
import os
import re
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Sequence


class Observation(str, Enum):
    OBSERVED_GOOD = "observed-good"
    OBSERVED_BAD = "observed-bad"
    COULD_NOT_OBSERVE = "could-not-observe"


class TerminalState(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUSED = "refused"


@dataclass(frozen=True)
class FailureReason:
    code: str
    observation: Observation
    detail: str


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    process_group_id: int | None
    start_token: str | None


@dataclass(frozen=True)
class CleanupResult:
    attempted: bool
    term_sent: bool
    kill_sent: bool
    reaped: bool
    group_absent: bool | None
    descendants_seen: tuple[ProcessIdentity, ...] = ()
    survivors: tuple[ProcessIdentity, ...] = ()
    detail: str = ""


@dataclass(frozen=True)
class EvidenceDigests:
    stdout_sha256: str
    stderr_sha256: str


@dataclass(frozen=True)
class SupervisedResult:
    terminal_state: TerminalState
    reason: FailureReason | None
    returncode: int | None
    stdout: bytes
    stderr: bytes
    stdout_bytes_seen: int
    stderr_bytes_seen: int
    started_monotonic: float
    ended_monotonic: float
    timed_out: bool
    cancelled: bool
    output_overflowed: bool
    attempt_number: int | None
    attempt_budget: int
    process: ProcessIdentity | None
    cleanup: CleanupResult
    evidence: EvidenceDigests

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.ended_monotonic - self.started_monotonic)


class AttemptBudget:
    """Thread-safe shared native-process budget."""

    def __init__(self, total: int) -> None:
        if not isinstance(total, int) or total < 1:
            raise ValueError("attempt budget must be a positive integer")
        self.total = total
        self._used = 0
        self._lock = threading.Lock()

    @property
    def used(self) -> int:
        with self._lock:
            return self._used

    def claim(self) -> int | None:
        with self._lock:
            if self._used >= self.total:
                return None
            self._used += 1
            return self._used

    def charge_observed_native_attempts(self, count: int) -> bool:
        """Charge attempts made inside a child after the outer launch.

        Returns false when the child exceeded the common budget.  The attempts
        remain charged: spent work is never erased to make accounting pass.
        """
        if count < 0:
            raise ValueError("native attempt charge cannot be negative")
        with self._lock:
            self._used += count
            return self._used <= self.total


@dataclass(frozen=True)
class SupervisorRequest:
    argv: Sequence[str]
    cwd: str
    environment: Mapping[str, str]
    environment_allowlist: frozenset[str]
    timeout_seconds: float
    term_grace_seconds: float = 1.0
    verification_grace_seconds: float = 1.0
    max_stdout_bytes: int = 4 * 1024 * 1024
    max_stderr_bytes: int = 1024 * 1024
    poll_interval_seconds: float = 0.02
    # Test-only platform injection also makes the refusal contract executable
    # on Linux. Production callers leave this unset.
    platform_name: str | None = None


_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_EMPTY_DIGEST = hashlib.sha256(b"").hexdigest()


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _empty_cleanup(detail: str = "not launched") -> CleanupResult:
    return CleanupResult(False, False, False, False, None, detail=detail)


def _refusal(code: str, detail: str, started: float, budget: AttemptBudget) -> SupervisedResult:
    ended = time.monotonic()
    return SupervisedResult(
        TerminalState.REFUSED,
        FailureReason(code, Observation.COULD_NOT_OBSERVE, detail),
        None,
        b"",
        b"",
        0,
        0,
        started,
        ended,
        False,
        False,
        False,
        None,
        budget.total,
        None,
        _empty_cleanup(),
        EvidenceDigests(_EMPTY_DIGEST, _EMPTY_DIGEST),
    )


def _validate(request: SupervisorRequest) -> str | None:
    if not request.argv or any(not isinstance(arg, str) or not arg or "\0" in arg for arg in request.argv):
        return "argv must be a nonempty array of nonempty NUL-free strings"
    cwd = Path(request.cwd)
    if not cwd.is_absolute() or not cwd.is_dir():
        return "cwd must be an existing absolute directory"
    if request.timeout_seconds <= 0:
        return "timeout_seconds must be positive"
    if request.term_grace_seconds < 0 or request.verification_grace_seconds < 0:
        return "cleanup grace periods cannot be negative"
    if request.poll_interval_seconds <= 0:
        return "poll_interval_seconds must be positive"
    if request.max_stdout_bytes < 1 or request.max_stderr_bytes < 1:
        return "output limits must be positive"
    for name, value in request.environment.items():
        if not isinstance(name, str) or not _ENV_NAME.fullmatch(name):
            return f"invalid environment name: {name!r}"
        if name not in request.environment_allowlist:
            return f"environment name is not allowlisted: {name}"
        if not isinstance(value, str) or "\0" in value:
            return f"environment value for {name} must be a NUL-free string"
    return None


@dataclass
class _Capture:
    limit: int
    data: bytearray = field(default_factory=bytearray)
    seen: int = 0
    overflowed: threading.Event = field(default_factory=threading.Event)

    def read_from(self, pipe) -> None:
        try:
            while True:
                chunk = pipe.read(65536)
                if not chunk:
                    break
                self.seen += len(chunk)
                remaining = self.limit - len(self.data)
                if remaining > 0:
                    self.data.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    self.overflowed.set()
        finally:
            pipe.close()


def _linux_identity(pid: int) -> ProcessIdentity | None:
    """Read a PID plus kernel start ticks, avoiding PID-reuse mistakes."""
    try:
        text = Path(f"/proc/{pid}/stat").read_text()
        close = text.rfind(")")
        fields = text[close + 2 :].split()
        # fields begins at proc stat field 3; pgrp=5 and starttime=22.
        return ProcessIdentity(pid, int(fields[2]), fields[19])
    except (OSError, ValueError, IndexError):
        return None


def _linux_ppids() -> dict[int, int]:
    found: dict[int, int] = {}
    try:
        entries = os.scandir("/proc")
    except OSError:
        return found
    with entries:
        for entry in entries:
            if not entry.name.isdigit():
                continue
            try:
                text = Path(entry.path, "stat").read_text()
                close = text.rfind(")")
                fields = text[close + 2 :].split()
                found[int(entry.name)] = int(fields[1])
            except (OSError, ValueError, IndexError):
                continue
    return found


def _descendants(root_pid: int) -> list[ProcessIdentity]:
    if not sys_platform_linux():
        return []
    ppids = _linux_ppids()
    frontier = {root_pid}
    child_pids: set[int] = set()
    while frontier:
        next_frontier = {pid for pid, ppid in ppids.items() if ppid in frontier and pid not in child_pids}
        child_pids.update(next_frontier)
        frontier = next_frontier
    return [identity for pid in sorted(child_pids) if (identity := _linux_identity(pid))]


def sys_platform_linux() -> bool:
    return os.name == "posix" and Path("/proc/self/stat").exists()


def _same_process(identity: ProcessIdentity) -> bool:
    if sys_platform_linux() and identity.start_token is not None:
        current = _linux_identity(identity.pid)
        return current is not None and current.start_token == identity.start_token
    try:
        os.kill(identity.pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _signal_identity(identity: ProcessIdentity, sig: int) -> bool:
    if not _same_process(identity):
        return False
    try:
        os.kill(identity.pid, sig)
        return True
    except ProcessLookupError:
        return False


def _cleanup(
    process: subprocess.Popen[bytes],
    identity: ProcessIdentity,
    descendants: dict[tuple[int, str | None], ProcessIdentity],
    request: SupervisorRequest,
    required: bool,
) -> CleanupResult:
    pgid = identity.process_group_id
    term_sent = False
    kill_sent = False
    attempted = required

    def live_descendants() -> list[ProcessIdentity]:
        return [item for item in descendants.values() if _same_process(item)]

    if required:
        if pgid is not None and _group_alive(pgid):
            try:
                os.killpg(pgid, signal.SIGTERM)
                term_sent = True
            except ProcessLookupError:
                pass
        for item in live_descendants():
            # This also catches descendants that escaped the original group.
            term_sent = _signal_identity(item, signal.SIGTERM) or term_sent
        deadline = time.monotonic() + request.term_grace_seconds
        while time.monotonic() < deadline:
            if process.poll() is not None and (pgid is None or not _group_alive(pgid)) and not live_descendants():
                break
            time.sleep(min(request.poll_interval_seconds, max(0.0, deadline - time.monotonic())))
        if (pgid is not None and _group_alive(pgid)) or live_descendants() or process.poll() is None:
            if pgid is not None and _group_alive(pgid):
                try:
                    os.killpg(pgid, signal.SIGKILL)
                    kill_sent = True
                except ProcessLookupError:
                    pass
            for item in live_descendants():
                kill_sent = _signal_identity(item, signal.SIGKILL) or kill_sent

    reaped = False
    try:
        process.wait(timeout=max(0.1, request.verification_grace_seconds))
        reaped = True
    except subprocess.TimeoutExpired:
        # A direct child that survived cleanup is always an unverifiable result.
        try:
            process.kill()
            kill_sent = True
            process.wait(timeout=max(0.1, request.verification_grace_seconds))
            reaped = True
        except (OSError, subprocess.TimeoutExpired):
            reaped = False

    verify_deadline = time.monotonic() + request.verification_grace_seconds
    while time.monotonic() < verify_deadline:
        group_absent = pgid is None or not _group_alive(pgid)
        survivors = live_descendants()
        if group_absent and not survivors:
            break
        time.sleep(min(request.poll_interval_seconds, max(0.0, verify_deadline - time.monotonic())))
    group_absent = pgid is None or not _group_alive(pgid)
    survivors = live_descendants()
    detail = "cleanup verified" if reaped and group_absent and not survivors else "cleanup could not verify an empty process tree"
    return CleanupResult(
        attempted,
        term_sent,
        kill_sent,
        reaped,
        group_absent,
        tuple(sorted(descendants.values(), key=lambda item: item.pid)),
        tuple(sorted(survivors, key=lambda item: item.pid)),
        detail,
    )


def supervise(
    request: SupervisorRequest,
    *,
    budget: AttemptBudget,
    cancel_event: threading.Event | None = None,
    on_spawn: Callable[[int], None] | None = None,
    on_exit: Callable[[int], None] | None = None,
) -> SupervisedResult:
    """Launch and fully account for one native child attempt."""
    started = time.monotonic()
    platform_name = request.platform_name or ("windows" if os.name == "nt" else "unix")
    if platform_name == "windows":
        return _refusal(
            "windows-job-object-unavailable",
            "Windows launch refused: SSSF has no proven Job Object assign/kill/verify path",
            started,
            budget,
        )
    if os.name != "posix":
        return _refusal("unsupported-process-platform", f"unsupported process platform: {os.name}", started, budget)
    invalid = _validate(request)
    if invalid:
        return _refusal("invalid-launch-contract", invalid, started, budget)
    attempt_number = budget.claim()
    if attempt_number is None:
        return _refusal("attempt-budget-exhausted", "total native attempt budget was already spent", started, budget)

    try:
        process = subprocess.Popen(
            list(request.argv),
            cwd=request.cwd,
            env=dict(request.environment),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=True,
        )
    except OSError as error:
        ended = time.monotonic()
        return SupervisedResult(
            TerminalState.REFUSED,
            FailureReason("launch-failed", Observation.COULD_NOT_OBSERVE, f"{type(error).__name__}: {error}"),
            None,
            b"",
            b"",
            0,
            0,
            started,
            ended,
            False,
            False,
            False,
            attempt_number,
            budget.total,
            None,
            _empty_cleanup("launch failed before a process existed"),
            EvidenceDigests(_EMPTY_DIGEST, _EMPTY_DIGEST),
        )

    process_identity = _linux_identity(process.pid) or ProcessIdentity(process.pid, process.pid, None)
    if process_identity.process_group_id is None:
        process_identity = ProcessIdentity(process_identity.pid, process.pid, process_identity.start_token)
    if on_spawn:
        on_spawn(process.pid)
    assert process.stdout is not None and process.stderr is not None
    stdout_capture = _Capture(request.max_stdout_bytes)
    stderr_capture = _Capture(request.max_stderr_bytes)
    stdout_thread = threading.Thread(target=stdout_capture.read_from, args=(process.stdout,), daemon=True)
    stderr_thread = threading.Thread(target=stderr_capture.read_from, args=(process.stderr,), daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    descendants: dict[tuple[int, str | None], ProcessIdentity] = {}
    deadline = started + request.timeout_seconds
    trigger: str | None = None
    while True:
        # Completion wins a same-tick cancellation race: no live process remains
        # for cancellation to affect.
        returncode = process.poll()
        for item in _descendants(process.pid):
            descendants[(item.pid, item.start_token)] = item
        if returncode is not None:
            break
        now = time.monotonic()
        if stdout_capture.overflowed.is_set() or stderr_capture.overflowed.is_set():
            trigger = "output-overflow"
            break
        if cancel_event is not None and cancel_event.is_set():
            trigger = "cancelled"
            break
        if now >= deadline:
            trigger = "timeout"
            break
        time.sleep(min(request.poll_interval_seconds, max(0.0, deadline - now)))

    pgid = process_identity.process_group_id
    tree_remains = (pgid is not None and _group_alive(pgid)) or any(
        _same_process(item) for item in descendants.values()
    )
    descendant_leak = trigger is None and tree_remains
    cleanup = _cleanup(process, process_identity, descendants, request, trigger is not None or descendant_leak)
    stdout_thread.join(timeout=max(0.1, request.verification_grace_seconds))
    stderr_thread.join(timeout=max(0.1, request.verification_grace_seconds))
    if on_exit:
        on_exit(process.pid)

    stdout = bytes(stdout_capture.data)
    stderr = bytes(stderr_capture.data)
    ended = time.monotonic()
    overflow = stdout_capture.overflowed.is_set() or stderr_capture.overflowed.is_set()
    timed_out = trigger == "timeout"
    cancelled = trigger == "cancelled"
    reason: FailureReason | None
    state: TerminalState
    if not cleanup.reaped or cleanup.group_absent is not True or cleanup.survivors:
        state = TerminalState.FAILED
        reason = FailureReason("cleanup-unverified", Observation.COULD_NOT_OBSERVE, cleanup.detail)
    elif overflow:
        state = TerminalState.FAILED
        reason = FailureReason("output-overflow", Observation.COULD_NOT_OBSERVE, "stdout or stderr exceeded its byte bound")
    elif timed_out:
        state = TerminalState.FAILED
        reason = FailureReason("wall-timeout", Observation.COULD_NOT_OBSERVE, "monotonic wall timeout expired")
    elif cancelled:
        state = TerminalState.FAILED
        reason = FailureReason("cancelled", Observation.COULD_NOT_OBSERVE, "cancellation was observed while the child was live")
    elif descendant_leak:
        state = TerminalState.FAILED
        reason = FailureReason("descendant-outlived-parent", Observation.OBSERVED_BAD, "child exit did not end its process tree")
    elif process.returncode != 0:
        state = TerminalState.FAILED
        reason = FailureReason("nonzero-exit", Observation.OBSERVED_BAD, f"process exited {process.returncode}")
    else:
        state = TerminalState.SUCCEEDED
        reason = None

    return SupervisedResult(
        state,
        reason,
        process.returncode,
        stdout,
        stderr,
        stdout_capture.seen,
        stderr_capture.seen,
        started,
        ended,
        timed_out,
        cancelled,
        overflow,
        attempt_number,
        budget.total,
        process_identity,
        cleanup,
        EvidenceDigests(_digest(stdout), _digest(stderr)),
    )
