"""Provider-neutral, bounded subprocess execution owned by SSSF.

The supervisor deliberately accepts argv and an exact environment mapping.  It
never invokes a shell, inherits stdin, or consults the caller's environment.
Unix children get a new process group.  Windows is refused until a Job Object
implementation can make the same descendant-cleanup claim honestly.
"""

from __future__ import annotations

import errno
import ctypes
import hashlib
import io
import json
import multiprocessing
import os
import re
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field, replace
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
    custodian_pid: int | None = None


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


# BOUNDEDNESS-OWNER: sssf.supervisor.attempt_budget
class AttemptBudget:
    """Thread-safe shared native-process budget.

    ``claim`` returns ``None`` once ``total`` attempts are spent: the declared
    boundary behaviour is REJECT, and spent work is never uncharged to make the
    accounting pass.
    """

    def __init__(self, total: int) -> None:
        if not isinstance(total, int) or isinstance(total, bool) or total < 1:
            # bool is an int in Python, and AttemptBudget(True) would be a
            # one-attempt budget nobody meant to ask for.
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


def correction_attempt_budget(retries: int) -> int:
    return 3 * (max(0, retries) + 1)


@dataclass(frozen=True)
class SupervisorRequest:
    argv: Sequence[str]
    cwd: str
    environment: Mapping[str, str]
    environment_allowlist: frozenset[str]
    # BOUNDEDNESS-OWNER: sssf.supervisor.child_wall_clock
    timeout_seconds: float
    term_grace_seconds: float = 1.0
    verification_grace_seconds: float = 1.0
    # BOUNDEDNESS-OWNER: sssf.supervisor.stdout_capture
    max_stdout_bytes: int = 4 * 1024 * 1024
    # BOUNDEDNESS-OWNER: sssf.supervisor.stderr_capture
    max_stderr_bytes: int = 1024 * 1024
    poll_interval_seconds: float = 0.02
    # Test-only platform injection also makes the refusal contract executable
    # on Linux. Production callers leave this unset.
    platform_name: str | None = None
    custodian_fault: str | None = None


_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_EMPTY_DIGEST = hashlib.sha256(b"").hexdigest()
_PR_SET_CHILD_SUBREAPER = 36
_PR_GET_CHILD_SUBREAPER = 37


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


def _cancelled_before_launch(detail: str, started: float, budget: AttemptBudget, attempt_number: int | None) -> SupervisedResult:
    """Refuse a launch that cancellation preempted, with explicit accounting.

    A cancellation observed before any claim leaves the budget untouched and
    reports no attempt.  A claim already taken stays taken: spent budget is
    never refunded to make accounting look cheaper.
    """
    return replace(
        _refusal("cancelled-before-launch", detail, started, budget),
        cancelled=True,
        attempt_number=attempt_number,
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


# BOUNDEDNESS-POLICY: sssf.policy.bounded-stream-capture.v1
@dataclass
class BoundedStreamCapture:
    """One retained-byte ceiling for a child stream, with explicit overflow.

    This is the repository's single owner of "hold at most N bytes of a child
    process stream".  ``limit`` bounds what is RETAINED; ``seen`` keeps counting
    what actually arrived, so a truncated capture can never be mistaken for a
    complete one.  Reaching the ceiling sets ``overflowed`` — the declared
    boundary behaviour is TRUNCATE_WITH_EXPLICIT_STATUS, never a silent drop.

    Callers that stream a child's output themselves (quality checks, the pi
    turn, the CI gate) bind their ceiling here rather than growing a private
    unbounded buffer.
    """

    limit: int
    data: bytearray = field(default_factory=bytearray)
    seen: int = 0
    overflowed: threading.Event = field(default_factory=threading.Event)

    def __post_init__(self) -> None:
        if not isinstance(self.limit, int) or isinstance(self.limit, bool) or self.limit < 1:
            raise ValueError("bounded stream capture limit must be a positive integer")

    def feed(self, chunk: bytes) -> None:
        """Admit one chunk against the ceiling.  Overflow is recorded, not hidden."""
        if not chunk:
            return
        self.seen += len(chunk)
        remaining = self.limit - len(self.data)
        if remaining > 0:
            self.data.extend(chunk[:remaining])
        if len(chunk) > remaining:
            self.overflowed.set()

    @property
    def truncated(self) -> bool:
        return self.overflowed.is_set()

    def status(self) -> dict[str, object]:
        """The facts a caller must carry so truncation is never silent."""
        return {
            "limit_bytes": self.limit,
            "retained_bytes": len(self.data),
            "bytes_seen": self.seen,
            "truncated": self.truncated,
            "on_limit_behavior": "TRUNCATE_WITH_EXPLICIT_STATUS",
        }

    def read_from(self, pipe) -> None:
        try:
            while True:
                chunk = pipe.read(65536)
                if not chunk:
                    break
                self.feed(chunk)
        finally:
            pipe.close()


# Retained for the internal call sites that predate the public name.
_Capture = BoundedStreamCapture


# BOUNDEDNESS-POLICY: sssf.policy.bounded-journal.v1
class BoundedJournalWriter:
    """An append-only child-output journal with a finite byte ceiling.

    A raw agent journal grows with whatever the child decides to emit, so the
    file needs its own bound rather than inheriting the child's appetite.  At
    the ceiling the writer stops appending payload and writes ONE terminal
    record naming the limit and the bytes it stopped accepting, so a reader can
    always tell a complete journal from a bounded one.
    """

    TRUNCATION_TYPE = "sssf_journal_truncated"

    @classmethod
    def _terminal_record(cls, limit: int, payload_bytes: int) -> str:
        return json.dumps(
            {
                "type": cls.TRUNCATION_TYPE,
                "limit_bytes": limit,
                "payload_bytes": payload_bytes,
                "on_limit_behavior": "TRUNCATE_WITH_EXPLICIT_STATUS",
            },
            separators=(",", ":"),
        ) + "\n"

    def __init__(self, handle, limit_bytes: int) -> None:
        if not isinstance(limit_bytes, int) or isinstance(limit_bytes, bool) or limit_bytes < 1:
            raise ValueError("bounded journal limit must be a positive integer")
        self._handle = handle
        self.limit = limit_bytes
        self.terminal_reserve = len(
            self._terminal_record(limit_bytes, limit_bytes).encode("utf-8")
        )
        if self.terminal_reserve >= self.limit:
            raise ValueError("bounded journal limit cannot hold its terminal record")
        self.payload_limit = self.limit - self.terminal_reserve
        handle.seek(0, os.SEEK_END)
        self.written = handle.tell()
        self.seen = self.written
        self.truncated = self.written >= self.limit
        if self.written:
            tail_size = min(self.written, 4096)
            try:
                handle.seek(self.written - tail_size)
                self.truncated = self.truncated or self.TRUNCATION_TYPE in handle.read(tail_size)
            except (OSError, io.UnsupportedOperation):
                pass
            finally:
                handle.seek(0, os.SEEK_END)

    def append(self, line: str) -> bool:
        """Append one line.  Returns whether the payload was admitted."""
        encoded = len(line.encode("utf-8", "replace"))
        self.seen += encoded
        if self.truncated or self.written + encoded > self.payload_limit:
            self._close_out()
            return False
        self._handle.write(line)
        self._handle.flush()
        self.written += encoded
        return True

    def _close_out(self) -> None:
        if self.truncated:
            return
        self.truncated = True
        record = self._terminal_record(self.limit, self.written)
        encoded = len(record.encode("utf-8"))
        if self.written + encoded <= self.limit:
            self._handle.write(record)
            self._handle.flush()
            self.written += encoded

    def status(self) -> dict[str, object]:
        return {
            "limit_bytes": self.limit,
            "retained_bytes": self.written,
            "payload_limit_bytes": self.payload_limit,
            "bytes_seen": self.seen,
            "truncated": self.truncated,
            "on_limit_behavior": "TRUNCATE_WITH_EXPLICIT_STATUS",
        }


def process_group_popen_kwargs() -> dict[str, object]:
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def stop_process_group(process: subprocess.Popen, grace_seconds: float = 2.0) -> bool:
    if os.name == "nt":
        cleanup_succeeded = False
        try:
            completed = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=max(1.0, grace_seconds),
                check=False,
            )
            cleanup_succeeded = completed.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            cleanup_succeeded = False
        if not cleanup_succeeded and process.poll() is None:
            process.kill()
    else:
        group_found = True
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            group_found = False
            if process.poll() is None:
                process.terminate()
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            pass
        if not group_found:
            if process.poll() is None:
                process.kill()
            process.wait()
            return True
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            return True
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    try:
        process.wait(timeout=max(1.0, grace_seconds))
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    return cleanup_succeeded if os.name == "nt" else True


# BOUNDEDNESS-POLICY: sssf.policy.child-wall-clock.v1
class ChildDeadline:
    """A finite wall clock for a child a caller streams itself.

    ``supervise`` owns the deadline for children it launches; a caller that
    reads a child's pipes directly (the pi turn, a quality check) still needs
    one, because an agent that never terminates is unbounded duration.  At the
    deadline the child is asked to stop (SIGTERM), then made to (SIGKILL), and
    ``expired`` records that the outcome is a CANCEL rather than a completion.
    """

    def __init__(self, seconds: float) -> None:
        if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or seconds <= 0:
            raise ValueError("child deadline must be a positive number of seconds")
        self.seconds = float(seconds)
        self.expired = threading.Event()
        self.cleanup_failed = threading.Event()
        self._timer: threading.Timer | None = None

    def arm(self, process) -> "ChildDeadline":
        def fire() -> None:
            self.expired.set()
            try:
                if not stop_process_group(process, 1.0):
                    self.cleanup_failed.set()
            except (OSError, ValueError):
                pass

        self._timer = threading.Timer(self.seconds, fire)
        self._timer.daemon = True
        self._timer.start()
        return self

    def cancel(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def status(self) -> dict[str, object]:
        return {
            "limit_seconds": self.seconds,
            "expired": self.expired.is_set(),
            "cleanup_failed": self.cleanup_failed.is_set(),
            "on_limit_behavior": "CANCEL",
        }


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


# BOUNDEDNESS-OWNER: sssf.supervisor.descendant_custody_set
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


def _custodied_descendants(root_pid: int) -> list[ProcessIdentity]:
    identities = {(item.pid, item.start_token): item for item in _descendants(root_pid)}
    for pid, ppid in _linux_ppids().items():
        if ppid == os.getpid() and pid != root_pid:
            identity = _linux_identity(pid)
            if identity is not None:
                identities[(identity.pid, identity.start_token)] = identity
    return list(identities.values())


def _set_subreaper(enabled: bool) -> bool:
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        return libc.prctl(_PR_SET_CHILD_SUBREAPER, int(enabled), 0, 0, 0) == 0
    except (AttributeError, OSError):
        return False


def _get_subreaper() -> bool | None:
    try:
        value = ctypes.c_int()
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(_PR_GET_CHILD_SUBREAPER, ctypes.byref(value), 0, 0, 0) != 0:
            return None
        return bool(value.value)
    except (AttributeError, OSError):
        return None


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
    rescan: Callable[[], list[ProcessIdentity]],
) -> CleanupResult:
    pgid = identity.process_group_id
    term_sent = False
    kill_sent = False
    attempted = required

    def reap_custodied() -> None:
        for item in descendants.values():
            try:
                os.waitpid(item.pid, os.WNOHANG)
            except (ChildProcessError, OSError):
                pass

    def refresh() -> None:
        for item in rescan():
            descendants[(item.pid, item.start_token)] = item

    def live_descendants() -> list[ProcessIdentity]:
        return [item for item in descendants.values() if _same_process(item)]

    if required:
        refresh()
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
            refresh()
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
    empty_scans = 0
    while time.monotonic() < verify_deadline:
        refresh()
        reap_custodied()
        group_absent = pgid is None or not _group_alive(pgid)
        survivors = live_descendants()
        if group_absent and not survivors:
            empty_scans += 1
            if empty_scans >= 2:
                break
        else:
            empty_scans = 0
        time.sleep(min(request.poll_interval_seconds, max(0.0, verify_deadline - time.monotonic())))
    refresh()
    reap_custodied()
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


def _supervise_linux(
    request: SupervisorRequest,
    *,
    budget: AttemptBudget,
    cancel_event: threading.Event | None = None,
    on_spawn: Callable[[int], None] | None = None,
    on_exit: Callable[[int], None] | None = None,
    claimed_attempt: int | None = None,
) -> SupervisedResult:
    """Launch and fully account for one native child attempt."""
    started = time.monotonic()
    invalid = _validate(request)
    if invalid:
        return _refusal("invalid-launch-contract", invalid, started, budget)
    attempt_number = claimed_attempt if claimed_attempt is not None else budget.claim()
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
        for item in _custodied_descendants(process.pid):
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
    cleanup = _cleanup(
        process,
        process_identity,
        descendants,
        request,
        trigger is not None or descendant_leak,
        lambda: _custodied_descendants(process.pid),
    )
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


def _custodian_main(connection, request: SupervisorRequest, total: int, attempt_number: int, cancel_event) -> None:
    budget = AttemptBudget(total)
    if not _set_subreaper(True):
        try:
            connection.send(("error", "child subreaper custody could not be established"))
        except (BrokenPipeError, EOFError, OSError):
            pass
        connection.close()
        return
    cleanup_requested = threading.Event()

    def receive_commands() -> None:
        while True:
            try:
                if connection.poll(0.05):
                    message = connection.recv()
                    if message == "cleanup":
                        cleanup_requested.set()
                        cancel_event.set()
                if cleanup_requested.is_set():
                    return
            except (BrokenPipeError, EOFError, OSError):
                cleanup_requested.set()
                cancel_event.set()
                return

    def watchdog() -> None:
        deadline = time.monotonic() + request.timeout_seconds + max(0.1, request.poll_interval_seconds * 2)
        while not cancel_event.is_set() and time.monotonic() < deadline:
            time.sleep(min(request.poll_interval_seconds, max(0.0, deadline - time.monotonic())))
        if time.monotonic() >= deadline:
            cancel_event.set()

    threading.Thread(target=receive_commands, daemon=True).start()
    threading.Thread(target=watchdog, daemon=True).start()

    def announce(pid: int) -> None:
        try:
            connection.send(("spawn", pid))
            if request.custodian_fault == "broken-ipc":
                connection.close()
                cleanup_requested.set()
                cancel_event.set()
        except (BrokenPipeError, EOFError, OSError):
            cleanup_requested.set()
            cancel_event.set()

    try:
        result = _supervise_linux(
            request,
            budget=budget,
            cancel_event=cancel_event,
            on_spawn=announce,
            claimed_attempt=attempt_number,
        )
        result = replace(result, cleanup=replace(result.cleanup, custodian_pid=os.getpid()))
        try:
            connection.send(("cleanup-ack", result.cleanup, result.process))
            connection.send(("result", result))
        except (BrokenPipeError, EOFError, OSError):
            pass
    except BaseException as error:
        try:
            connection.send(("error", f"{type(error).__name__}: {error}"))
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        connection.close()


def supervise(
    request: SupervisorRequest,
    *,
    budget: AttemptBudget,
    cancel_event: threading.Event | None = None,
    on_spawn: Callable[[int], None] | None = None,
    on_exit: Callable[[int], None] | None = None,
) -> SupervisedResult:
    started = time.monotonic()
    platform_name = request.platform_name or ("windows" if os.name == "nt" else "unix")
    if platform_name == "windows":
        return _refusal("windows-job-object-unavailable", "Windows launch refused: SSSF has no proven Job Object assign/kill/verify path", started, budget)
    if not sys_platform_linux():
        return _refusal("linux-subprocess-custody-unavailable", "launch refused: proven descendant custody requires Linux subreaper support", started, budget)
    invalid = _validate(request)
    if invalid:
        return _refusal("invalid-launch-contract", invalid, started, budget)
    # Cancellation is observed before the budget is touched.  Platform and
    # contract refusals keep precedence because they are pure and name a more
    # specific defect, but neither claims an attempt, so no spend precedes this.
    if cancel_event is not None and cancel_event.is_set():
        return _cancelled_before_launch(
            "cancellation was already observed before any native attempt was claimed",
            started,
            budget,
            None,
        )
    attempt_number = budget.claim()
    if attempt_number is None:
        return _refusal("attempt-budget-exhausted", "total native attempt budget was already spent", started, budget)
    context = multiprocessing.get_context("spawn")
    parent_connection = None
    child_connection = None
    helper = None
    helper_cancel = None
    result = None
    error = None
    cleanup_ack = None
    provider_identity = None
    cleanup_requested = False
    helper_deadline = started + request.timeout_seconds + request.term_grace_seconds + request.verification_grace_seconds + 2.0
    try:
        if request.custodian_fault == "startup":
            raise OSError("injected custodian startup failure")
        parent_connection, child_connection = context.Pipe(duplex=True)
        helper_cancel = context.Event()
        helper = context.Process(
            target=_custodian_main,
            args=(child_connection, request, budget.total, attempt_number, helper_cancel),
            daemon=False,
        )
        # Recheck immediately before the custodian exists: a cancellation that
        # arrived during pre-launch setup fails closed here rather than
        # proceeding into an avoidable helper and provider launch.  The claim
        # taken above is still spent and is reported as such.
        if cancel_event is not None and cancel_event.is_set():
            helper = None
            return _cancelled_before_launch(
                "cancellation was observed during pre-launch setup, before the custodian was started",
                started,
                budget,
                attempt_number,
            )
        helper.start()
        child_connection.close()
        child_connection = None
        while time.monotonic() < helper_deadline:
            if cancel_event is not None and cancel_event.is_set() and not cleanup_requested:
                parent_connection.send("cleanup")
                cleanup_requested = True
            if parent_connection.poll(request.poll_interval_seconds):
                message = parent_connection.recv()
                if message[0] == "spawn":
                    provider_identity = ProcessIdentity(message[1], message[1], None)
                    if on_spawn:
                        on_spawn(message[1])
                elif message[0] == "cleanup-ack":
                    cleanup_ack, provider_identity = message[1], message[2]
                elif message[0] == "result":
                    result = message[1]
                    break
                elif message[0] == "error":
                    error = message[1]
                    break
            if not helper.is_alive() and not parent_connection.poll():
                error = "custodian exited without a terminal IPC result"
                break
    except (BrokenPipeError, EOFError, OSError, RuntimeError) as failure:
        error = f"custodian protocol failure: {type(failure).__name__}: {failure}"
    except BaseException as failure:
        error = f"custodian callback failure: {type(failure).__name__}: {failure}"
    finally:
        if helper is not None and helper.is_alive() and result is None:
            try:
                if parent_connection is not None and not cleanup_requested:
                    parent_connection.send("cleanup")
                    cleanup_requested = True
            except (BrokenPipeError, EOFError, OSError):
                pass
            ack_deadline = time.monotonic() + request.term_grace_seconds + request.verification_grace_seconds + 1.0
            while cleanup_ack is None and time.monotonic() < ack_deadline:
                try:
                    if parent_connection is not None and parent_connection.poll(request.poll_interval_seconds):
                        message = parent_connection.recv()
                        if message[0] == "cleanup-ack":
                            cleanup_ack, provider_identity = message[1], message[2]
                        elif message[0] == "result":
                            result = message[1]
                except (BrokenPipeError, EOFError, OSError):
                    break
            if cleanup_ack is not None:
                helper.join(timeout=max(0.1, request.verification_grace_seconds))
        if child_connection is not None:
            child_connection.close()
        if parent_connection is not None:
            parent_connection.close()
    if error is not None and result is not None:
        result = replace(
            result,
            terminal_state=TerminalState.FAILED,
            reason=FailureReason("cleanup-unverified", Observation.COULD_NOT_OBSERVE, error),
        )
    if result is None:
        ended = time.monotonic()
        helper_pid = helper.pid if helper is not None else None
        cleanup = cleanup_ack or CleanupResult(
            helper is not None,
            cleanup_requested,
            False,
            False,
            None,
            detail=f"custodian {helper_pid} retained custody; cleanup acknowledgement was not observable",
            custodian_pid=helper_pid,
        )
        return SupervisedResult(
            TerminalState.FAILED,
            FailureReason("cleanup-unverified", Observation.COULD_NOT_OBSERVE, error or "custodian IPC deadline expired"),
            None,
            b"",
            b"",
            0,
            0,
            started,
            ended,
            False,
            bool(cancel_event is not None and cancel_event.is_set()),
            False,
            attempt_number,
            budget.total,
            provider_identity,
            cleanup,
            EvidenceDigests(_EMPTY_DIGEST, _EMPTY_DIGEST),
        )
    if result.process is not None and on_exit:
        try:
            on_exit(result.process.pid)
        except BaseException as failure:
            return replace(
                result,
                terminal_state=TerminalState.FAILED,
                reason=FailureReason("cleanup-unverified", Observation.COULD_NOT_OBSERVE, f"custodian callback failure: {type(failure).__name__}: {failure}"),
            )
    return result
