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


def correction_attempt_budget(retries: int) -> int:
    return 3 * (max(0, retries) + 1)


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
