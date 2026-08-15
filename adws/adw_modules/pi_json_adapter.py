"""Strict Pi JSON/print adapter on top of the SSSF subprocess supervisor.

This module is intentionally standard-library-only so its provider-free
fixtures run on stock Python in Linux and Windows CI.  It does not discover
models, credentials, user settings, sessions, or Pi resources.  Requested
provider/model pairs are exact launch targets; there is no fallback path.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .subprocess_supervisor import (
    AttemptBudget,
    CleanupResult,
    FailureReason,
    Observation,
    ProcessIdentity,
    SupervisorRequest,
    TerminalState,
    supervise,
)


BUILTIN_TOOLS = frozenset({"read", "bash", "edit", "write", "grep", "find", "ls"})
THINKING_LEVELS = frozenset({"off", "minimal", "low", "medium", "high", "xhigh", "max"})
SAFE_INHERITED_ENV_NAMES = frozenset(
    {
        "PATH",
        "LANG",
        "LANGUAGE",
        "LC_ALL",
        "LC_CTYPE",
        "TMPDIR",
        "TEMP",
        "TMP",
        "SYSTEMROOT",
        "WINDIR",
        "PATHEXT",
        "COMSPEC",
    }
)
PI_OWNED_ENV_NAMES = frozenset(
    {
        "PI_CODING_AGENT_DIR",
        "PI_CODING_AGENT_SESSION_DIR",
        "PI_OFFLINE",
        "PI_SKIP_VERSION_CHECK",
        "PI_TELEMETRY",
    }
)
_PROVIDER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_EVIDENCE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SENSITIVE_ENV_FRAGMENTS = ("KEY", "TOKEN", "CREDENTIAL", "AUTH", "COOKIE", "HOME")
_EMPTY_DIGEST = hashlib.sha256(b"").hexdigest()


@dataclass(frozen=True)
class PiAdapterRequest:
    prompt: str
    system_prompt: str
    provider_model: str
    thinking: str
    tools: Sequence[str] | None
    cwd: str
    raw_event_path: str
    execution_id: str
    phase_id: str
    attempt_number: int
    pi_argv0: str = "pi"
    timeout_seconds: float = 120.0
    term_grace_seconds: float = 1.0
    verification_grace_seconds: float = 1.0
    max_stdout_bytes: int = 4 * 1024 * 1024
    max_stderr_bytes: int = 1024 * 1024
    max_event_bytes: int = 4 * 1024 * 1024
    total_attempt_budget: int = 1
    environment: Mapping[str, str] = field(default_factory=dict)
    environment_allowlist: frozenset[str] = SAFE_INHERITED_ENV_NAMES
    platform_name: str | None = None
    custodian_fault: str | None = None
    evidence_fault: str | None = None


@dataclass(frozen=True)
class UsageCost:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    usage_source_class: str = "unavailable"
    cost_source_class: str = "unavailable"


@dataclass(frozen=True)
class AttemptAccounting:
    budget: int
    native_attempts: int
    supervisor_attempt: int | None
    native_retry_events: int
    fully_observable: bool


@dataclass(frozen=True)
class PiEvidenceDigests:
    stdout_sha256: str
    stderr_sha256: str
    raw_events_sha256: str | None


@dataclass(frozen=True)
class ResolvedTargetEvidence:
    event_index: int
    message_index: int
    provider: str | None
    model: str | None
    effort: str | None


@dataclass(frozen=True)
class PiTerminalResult:
    terminal_state: TerminalState
    reason: FailureReason | None
    returncode: int | None
    text: str
    requested_provider: str
    requested_model: str
    requested_effort: str
    resolved_provider: str | None
    resolved_model: str | None
    resolved_effort: str | None
    terminal_stop: str | None
    terminal_error: str | None
    usage: UsageCost
    attempts: AttemptAccounting
    timed_out: bool
    cancelled: bool
    process: ProcessIdentity | None
    cleanup: CleanupResult
    evidence: PiEvidenceDigests
    stdout_bytes_seen: int
    stderr_bytes_seen: int
    event_bytes_preserved: int
    events: tuple[dict, ...] = ()
    primary_terminal_state: TerminalState | None = None
    primary_reason: FailureReason | None = None
    observation_delivery_error: str | None = None
    evidence_persisted: bool = False
    provider_launched: bool = False
    evidence_error: str | None = None
    resolved_targets: tuple[ResolvedTargetEvidence, ...] = ()

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class _ParsedEvents:
    events: tuple[dict, ...]
    malformed_lines: int
    terminal_count: int
    terminal_stop: str | None
    terminal_error: str | None
    text: str
    usage: UsageCost
    native_retry_starts: int
    retry_protocol_observable: bool
    resolved_provider: str | None
    resolved_model: str | None
    resolved_effort: str | None
    resolved_targets: tuple[ResolvedTargetEvidence, ...]
    target_failure: FailureReason | None


def safe_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Copy only non-secret process mechanics, never auth or home variables."""
    source = os.environ if source is None else source
    return {name: source[name] for name in SAFE_INHERITED_ENV_NAMES if name in source}


def _split_provider_model(value: str) -> tuple[str, str] | None:
    if not isinstance(value, str) or value.count("/") < 1:
        return None
    provider, model = value.split("/", 1)
    if not _PROVIDER.fullmatch(provider) or not model or model != model.strip():
        return None
    if any(character in model for character in ("\0", "*", "?", "[", "]")):
        return None
    return provider, model


def _tool_args(tools: Sequence[str] | None) -> list[str] | None:
    if tools is None:
        return None
    normalized = list(tools)
    if len(normalized) != len(set(normalized)):
        return None
    if any(tool not in BUILTIN_TOOLS for tool in normalized):
        return None
    if not normalized:
        return ["--no-tools"]
    return ["--tools", ",".join(normalized)]


def build_argv(request: PiAdapterRequest) -> tuple[list[str] | None, FailureReason | None]:
    target = _split_provider_model(request.provider_model)
    if target is None:
        return None, FailureReason(
            "pi-target-not-fully-qualified",
            Observation.COULD_NOT_OBSERVE,
            "Pi requires an exact provider/model target; patterns and bare models are refused",
        )
    if request.thinking not in THINKING_LEVELS:
        return None, FailureReason(
            "pi-thinking-not-explicit",
            Observation.COULD_NOT_OBSERVE,
            "Pi thinking must be one explicit supported level",
        )
    tool_args = _tool_args(request.tools)
    if tool_args is None:
        return None, FailureReason(
            "pi-tool-policy-not-exact",
            Observation.COULD_NOT_OBSERVE,
            "Pi tools must be an explicit unique allowlist of built-in tool names",
        )
    provider, model = target
    argv = [
        request.pi_argv0,
        "--print",
        "--mode",
        "json",
        "--provider",
        provider,
        "--model",
        model,
        "--thinking",
        request.thinking,
        "--no-session",
        "--no-extensions",
        "--no-skills",
        "--no-prompt-templates",
        "--no-context-files",
        "--no-approve",
        *tool_args,
        "--system-prompt",
        request.system_prompt,
        request.prompt,
    ]
    return argv, None


def _number(value, integer: bool = True):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        return None
    return int(value) if integer else float(value)


def _assistant_messages(event: dict) -> list[dict]:
    messages: list[dict] = []
    message = event.get("message")
    if isinstance(message, dict) and message.get("role") == "assistant":
        messages.append(message)
    if event.get("type") == "agent_end" and isinstance(event.get("messages"), list):
        for item in event["messages"]:
            if isinstance(item, dict) and item.get("role") == "assistant":
                messages.append(item)
    return messages


def _message_text(message: dict) -> str:
    content = message.get("content")
    if not isinstance(content, list):
        return ""
    return "".join(
        part.get("text", "")
        for part in content
        if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text", ""), str)
    )


def _parse_events(raw: bytes, expected_target: tuple[str, str, str]) -> _ParsedEvents:
    events: list[dict] = []
    malformed = 0
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            malformed += 1
            continue
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            malformed += 1
            continue
        events.append(event)

    terminal_count = sum(event.get("type") == "agent_end" for event in events)
    retry_starts = sum(event.get("type") == "auto_retry_start" for event in events)
    retry_ends = sum(event.get("type") == "auto_retry_end" for event in events)
    retry_protocol_observable = retry_starts == retry_ends
    terminal_stop = None
    terminal_error = None
    text = ""
    resolved_provider = None
    resolved_model = None
    resolved_effort = None
    resolved_targets: list[ResolvedTargetEvidence] = []
    target_failure = None
    input_tokens = output_tokens = cache_read = cache_write = reasoning = total_tokens = 0
    total_cost = 0.0
    usage_seen = False
    cost_seen = False

    # message_end is the accounting source. agent_end repeats message history
    # and must not double-charge it.
    for event_index, event in enumerate(events):
        if event.get("type") == "message_end":
            messages = _assistant_messages(event)
            for message_index, message in enumerate(messages):
                stop = message.get("stopReason")
                if isinstance(stop, str):
                    terminal_stop = stop
                error = message.get("errorMessage")
                if isinstance(error, str) and error:
                    terminal_error = error
                body = _message_text(message)
                if body:
                    text = body
                values = tuple(
                    value if isinstance(value, str) and value else None
                    for value in (
                        message.get("provider"),
                        message.get("model"),
                        message.get("thinkingLevel"),
                    )
                )
                evidence = ResolvedTargetEvidence(event_index, message_index, *values)
                resolved_targets.append(evidence)
                resolved_provider, resolved_model, resolved_effort = values
                if target_failure is None:
                    if None in values:
                        target_failure = FailureReason(
                            "resolved-target-unverified",
                            Observation.COULD_NOT_OBSERVE,
                            f"Pi message_end target was incomplete at event {event_index}, message {message_index}",
                        )
                    elif values != expected_target:
                        target_failure = FailureReason(
                            "resolved-target-mismatch",
                            Observation.OBSERVED_BAD,
                            f"Pi message_end target drifted at event {event_index}, message {message_index}",
                        )
                usage = message.get("usage")
                if isinstance(usage, dict):
                    fields = {
                        "input": _number(usage.get("input")),
                        "output": _number(usage.get("output")),
                        "cacheRead": _number(usage.get("cacheRead")),
                        "cacheWrite": _number(usage.get("cacheWrite")),
                        "reasoning": _number(usage.get("reasoning")),
                    }
                    if all(value is not None for value in fields.values()):
                        usage_seen = True
                        input_tokens += fields["input"]
                        output_tokens += fields["output"]
                        cache_read += fields["cacheRead"]
                        cache_write += fields["cacheWrite"]
                        reasoning += fields["reasoning"]
                        reported_total = _number(usage.get("totalTokens"))
                        total_tokens += reported_total if reported_total is not None else sum(fields.values()) - reasoning
                    cost = usage.get("cost")
                    if isinstance(cost, dict):
                        value = _number(cost.get("total"), integer=False)
                        if value is not None:
                            cost_seen = True
                            total_cost += value

    if target_failure is None and not resolved_targets:
        target_failure = FailureReason(
            "resolved-target-unverified",
            Observation.COULD_NOT_OBSERVE,
            "Pi emitted no assistant message_end target evidence",
        )

    # A terminal agent_end can carry the only final error in a fixture or a
    # future Pi version. It affects verdict/text but never usage accounting.
    for event in events:
        if event.get("type") != "agent_end":
            continue
        for message in _assistant_messages(event):
            stop = message.get("stopReason")
            if isinstance(stop, str):
                terminal_stop = stop
            error = message.get("errorMessage")
            if isinstance(error, str) and error:
                terminal_error = error
            body = _message_text(message)
            if body:
                text = body

    usage = UsageCost(
        input_tokens,
        output_tokens,
        cache_read,
        cache_write,
        reasoning,
        total_tokens,
        total_cost,
        "provider-reported" if usage_seen else "unavailable",
        "provider-reported" if cost_seen else "unavailable",
    )
    return _ParsedEvents(
        tuple(events),
        malformed,
        terminal_count,
        terminal_stop,
        terminal_error,
        text,
        usage,
        retry_starts,
        retry_protocol_observable,
        resolved_provider,
        resolved_model,
        resolved_effort,
        tuple(resolved_targets),
        target_failure,
    )


def _settings(runtime_dir: Path) -> None:
    runtime_dir.mkdir(parents=True, exist_ok=False)
    settings = {
        "enableInstallTelemetry": False,
        "defaultProjectTrust": "never",
        "compaction": {"enabled": False},
        "retry": {
            "enabled": False,
            "maxRetries": 0,
            "provider": {"maxRetries": 0, "maxRetryDelayMs": 0},
        },
        "packages": [],
        "extensions": [],
        "skills": [],
        "prompts": [],
    }
    (runtime_dir / "settings.json").write_text(json.dumps(settings, sort_keys=True) + "\n")


def _refused_result(request: PiAdapterRequest, reason: FailureReason) -> PiTerminalResult:
    target = _split_provider_model(request.provider_model) or ("", "")
    empty = hashlib.sha256(b"").hexdigest()
    return PiTerminalResult(
        TerminalState.REFUSED,
        reason,
        None,
        "",
        target[0],
        target[1],
        request.thinking,
        None,
        None,
        None,
        None,
        None,
        UsageCost(),
        AttemptAccounting(request.total_attempt_budget, 0, None, 0, False),
        False,
        False,
        None,
        CleanupResult(False, False, False, False, None, detail="not launched"),
        PiEvidenceDigests(empty, empty, empty),
        0,
        0,
        0,
    )


def _evidence_setup_failure(request: PiAdapterRequest, error: OSError) -> PiTerminalResult:
    return replace(
        _refused_result(
            request,
            FailureReason("evidence-setup-unobservable", Observation.COULD_NOT_OBSERVE, f"raw evidence reservation failed: {type(error).__name__}: {error}"),
        ),
        evidence=PiEvidenceDigests(_EMPTY_DIGEST, _EMPTY_DIGEST, None),
        evidence_error=f"{type(error).__name__}: {error}",
    )


def _evidence_persistence_failure(
    request: PiAdapterRequest,
    process_result,
    budget: AttemptBudget,
    error: OSError,
) -> PiTerminalResult:
    target = _split_provider_model(request.provider_model) or ("", "")
    detail = f"raw evidence persistence failed: {type(error).__name__}: {error}"
    return PiTerminalResult(
        TerminalState.FAILED,
        FailureReason("evidence-persistence-unobservable", Observation.COULD_NOT_OBSERVE, detail),
        process_result.returncode,
        "",
        target[0],
        target[1],
        request.thinking,
        None,
        None,
        None,
        None,
        None,
        UsageCost(),
        AttemptAccounting(
            budget.total,
            1 if process_result.attempt_number is not None else 0,
            process_result.attempt_number,
            0,
            False,
        ),
        process_result.timed_out,
        process_result.cancelled,
        process_result.process,
        process_result.cleanup,
        PiEvidenceDigests(process_result.evidence.stdout_sha256, process_result.evidence.stderr_sha256, None),
        process_result.stdout_bytes_seen,
        process_result.stderr_bytes_seen,
        0,
        (),
        process_result.terminal_state,
        process_result.reason,
        None,
        False,
        process_result.process is not None,
        f"{type(error).__name__}: {error}",
    )


def run_pi_json(
    request: PiAdapterRequest,
    *,
    budget: AttemptBudget | None = None,
    cancel_event: threading.Event | None = None,
    on_event: Callable[[dict], None] | None = None,
    on_spawn: Callable[[int], None] | None = None,
    on_exit: Callable[[int], None] | None = None,
) -> PiTerminalResult:
    """Run one strict, noninteractive Pi attempt and return a typed terminal result."""
    argv, refusal = build_argv(request)
    if refusal is not None or argv is None:
        return _refused_result(request, refusal or FailureReason("pi-launch-refused", Observation.COULD_NOT_OBSERVE, "invalid launch"))
    target = _split_provider_model(request.provider_model)
    assert target is not None
    provider, model = target
    if request.total_attempt_budget < 1:
        return _refused_result(
            request,
            FailureReason("invalid-attempt-budget", Observation.COULD_NOT_OBSERVE, "attempt budget must be positive"),
        )
    budget = budget or AttemptBudget(request.total_attempt_budget)
    if budget.total != request.total_attempt_budget:
        return _refused_result(
            request,
            FailureReason("attempt-budget-mismatch", Observation.COULD_NOT_OBSERVE, "shared and requested budgets differ"),
        )
    if request.max_event_bytes < 1 or request.max_event_bytes > request.max_stdout_bytes:
        return _refused_result(
            request,
            FailureReason("invalid-event-bound", Observation.COULD_NOT_OBSERVE, "event bound must be positive and no larger than stdout bound"),
        )
    if set(request.environment) - set(request.environment_allowlist):
        return _refused_result(
            request,
            FailureReason("pi-environment-not-allowlisted", Observation.COULD_NOT_OBSERVE, "environment contains a name outside the explicit allowlist"),
        )
    sensitive_names = [
        name
        for name in set(request.environment) | set(request.environment_allowlist)
        if any(fragment in name.upper() for fragment in _SENSITIVE_ENV_FRAGMENTS)
    ]
    if sensitive_names:
        return _refused_result(
            request,
            FailureReason(
                "pi-sensitive-environment-refused",
                Observation.COULD_NOT_OBSERVE,
                "credential, auth-home, cookie, and token environment names require a separate transport increment",
            ),
        )

    if (
        not _EVIDENCE_ID.fullmatch(request.execution_id)
        or not _EVIDENCE_ID.fullmatch(request.phase_id)
        or not isinstance(request.attempt_number, int)
        or request.attempt_number < 1
    ):
        return _refused_result(
            request,
            FailureReason("invalid-raw-evidence-identity", Observation.COULD_NOT_OBSERVE, "execution, phase, and attempt evidence identities must be explicit and valid"),
        )
    raw_path = Path(request.raw_event_path) / request.execution_id / request.phase_id / f"attempt-{request.attempt_number:03d}.jsonl"
    try:
        if request.evidence_fault == "mkdir":
            raise OSError("injected evidence mkdir failure")
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        if request.evidence_fault == "create":
            raise OSError("injected evidence create failure")
        reservation = raw_path.open("xb")
        reservation.close()
        if request.evidence_fault == "reserve-close":
            raise OSError("injected evidence reservation close failure")
    except FileExistsError:
        return _refused_result(
            request,
            FailureReason("raw-evidence-identity-collision", Observation.COULD_NOT_OBSERVE, "raw event evidence target already exists"),
        )
    except OSError as error:
        return _evidence_setup_failure(request, error)
    process_result = None
    try:
        with tempfile.TemporaryDirectory(prefix="sssf-pi-", dir=str(raw_path.parent)) as temporary:
            runtime_dir = Path(temporary) / "runtime"
            _settings(runtime_dir)
            environment = dict(request.environment)
            environment.update(
                {
                    "PI_CODING_AGENT_DIR": str(runtime_dir),
                    "PI_OFFLINE": "1",
                    "PI_SKIP_VERSION_CHECK": "1",
                    "PI_TELEMETRY": "0",
                }
            )
            allowlist = frozenset(request.environment_allowlist | PI_OWNED_ENV_NAMES)
            process_result = supervise(
                SupervisorRequest(
                    argv=argv,
                    cwd=request.cwd,
                    environment=environment,
                    environment_allowlist=allowlist,
                    timeout_seconds=request.timeout_seconds,
                    term_grace_seconds=request.term_grace_seconds,
                    verification_grace_seconds=request.verification_grace_seconds,
                    max_stdout_bytes=request.max_stdout_bytes,
                    max_stderr_bytes=request.max_stderr_bytes,
                    platform_name=request.platform_name,
                    custodian_fault=request.custodian_fault,
                ),
                budget=budget,
                cancel_event=cancel_event,
                on_spawn=on_spawn,
                on_exit=on_exit,
            )
    except OSError as error:
        if process_result is None:
            return _evidence_setup_failure(request, error)
        return _evidence_persistence_failure(request, process_result, budget, error)

    raw_file = None
    try:
        if request.evidence_fault == "reopen":
            raise OSError("injected evidence reopen failure")
        raw_file = raw_path.open("r+b")
        if request.evidence_fault == "write":
            raise OSError("injected evidence write failure")
        raw_file.write(process_result.stdout)
        if request.evidence_fault == "flush":
            raise OSError("injected evidence flush failure")
        raw_file.flush()
        if request.evidence_fault == "fsync":
            raise OSError("injected evidence fsync failure")
        os.fsync(raw_file.fileno())
        raw_file.close()
        raw_file = None
        if request.evidence_fault == "final-close":
            raise OSError("injected evidence final close failure")
    except OSError as error:
        if raw_file is not None:
            try:
                raw_file.close()
            except OSError:
                pass
        return _evidence_persistence_failure(request, process_result, budget, error)
    raw_digest = hashlib.sha256(process_result.stdout).hexdigest()
    parsed = _parse_events(process_result.stdout, (provider, model, request.thinking))
    callback_error = None
    for event in parsed.events:
        if on_event and callback_error is None:
            try:
                on_event(event)
            except BaseException as error:
                callback_error = f"{type(error).__name__}: {error}"

    extra_native_attempts = parsed.native_retry_starts
    within_budget = budget.charge_observed_native_attempts(extra_native_attempts)
    attempts = AttemptAccounting(
        budget.total,
        1 + extra_native_attempts if process_result.attempt_number is not None else 0,
        process_result.attempt_number,
        extra_native_attempts,
        parsed.retry_protocol_observable,
    )
    reason = process_result.reason
    state = process_result.terminal_state
    if state == TerminalState.SUCCEEDED:
        if len(process_result.stdout) > request.max_event_bytes:
            state = TerminalState.FAILED
            reason = FailureReason("event-overflow", Observation.COULD_NOT_OBSERVE, "raw event bytes exceeded their separate bound")
        elif parsed.malformed_lines:
            state = TerminalState.FAILED
            reason = FailureReason("malformed-json-event", Observation.COULD_NOT_OBSERVE, f"{parsed.malformed_lines} event line(s) could not be parsed")
        elif parsed.terminal_count == 0:
            state = TerminalState.FAILED
            reason = FailureReason("missing-terminal-event", Observation.COULD_NOT_OBSERVE, "Pi emitted no agent_end terminal event")
        elif parsed.terminal_count > 1:
            state = TerminalState.FAILED
            reason = FailureReason("duplicate-terminal-event", Observation.OBSERVED_BAD, "Pi emitted more than one agent_end terminal event")
        elif not parsed.retry_protocol_observable:
            state = TerminalState.FAILED
            reason = FailureReason("native-retry-unobservable", Observation.COULD_NOT_OBSERVE, "native retry start/end events did not reconcile")
        elif parsed.native_retry_starts:
            state = TerminalState.FAILED
            reason = FailureReason("native-retry-policy-violation", Observation.OBSERVED_BAD, "Pi retried despite the disabled native retry policy")
        elif not within_budget:
            state = TerminalState.FAILED
            reason = FailureReason("attempt-budget-exhausted", Observation.OBSERVED_BAD, "observed native attempts exceeded the common budget")
        elif parsed.target_failure is not None:
            state = TerminalState.FAILED
            reason = parsed.target_failure
        elif parsed.terminal_stop in {"error", "aborted"} or parsed.terminal_error:
            state = TerminalState.FAILED
            reason = FailureReason(
                "structured-provider-error",
                Observation.OBSERVED_BAD,
                parsed.terminal_error or f"Pi terminal stop was {parsed.terminal_stop}",
            )
        elif parsed.terminal_stop != "stop":
            state = TerminalState.FAILED
            reason = FailureReason("terminal-stop-unverified", Observation.COULD_NOT_OBSERVE, f"unexpected terminal stop: {parsed.terminal_stop!r}")

    primary_state = state
    primary_reason = reason
    if callback_error is not None:
        state = TerminalState.FAILED
        reason = FailureReason(
            "observation-delivery-failed",
            Observation.COULD_NOT_OBSERVE,
            f"durable event callback failed: {callback_error}",
        )

    return PiTerminalResult(
        state,
        reason,
        process_result.returncode,
        parsed.text,
        provider,
        model,
        request.thinking,
        parsed.resolved_provider,
        parsed.resolved_model,
        parsed.resolved_effort,
        parsed.terminal_stop,
        parsed.terminal_error,
        parsed.usage,
        attempts,
        process_result.timed_out,
        process_result.cancelled,
        process_result.process,
        process_result.cleanup,
        PiEvidenceDigests(process_result.evidence.stdout_sha256, process_result.evidence.stderr_sha256, raw_digest),
        process_result.stdout_bytes_seen,
        process_result.stderr_bytes_seen,
        len(process_result.stdout),
        parsed.events,
        primary_state,
        primary_reason,
        callback_error,
        True,
        process_result.process is not None,
        None,
        parsed.resolved_targets,
    )
