#!/usr/bin/env python3
"""Provider-free positive and watched-red proof for the SSSF executor/Pi seam."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from adws.adw_modules.pi_json_adapter import (  # noqa: E402
    PI_OWNED_ENV_NAMES,
    PiAdapterRequest,
    build_argv,
    run_pi_json,
    safe_environment,
)
from adws.adw_modules.subprocess_supervisor import (  # noqa: E402
    AttemptBudget,
    Observation,
    SupervisorRequest,
    TerminalState,
    correction_attempt_budget,
    supervise,
)

FIXTURE = ROOT / "docs" / "validation" / "fixtures" / "fake_pi_child.py"
TYPED_TAIL = "typed-parent-tail-marker"


class DeferredCancellation:
    """Cancellation that becomes set after its first observation.

    This drives the pre-launch setup window deterministically: the first
    observation, before the attempt is claimed, sees no cancellation, and every
    later observation sees one. It is a race driver, not an expected answer.
    """

    def __init__(self) -> None:
        self.observations = 0

    def is_set(self) -> bool:
        self.observations += 1
        return self.observations > 1


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def request(temp: Path, mode: str, **overrides) -> PiAdapterRequest:
    values = {
        "prompt": mode,
        "system_prompt": "fixture system prompt",
        "provider_model": "fixture/deterministic",
        "thinking": "high",
        "tools": ["read"],
        "cwd": str(ROOT),
        "raw_event_path": str(temp / f"{mode.replace('/', '_').replace(':', '_')}.jsonl"),
        "execution_id": "fixture-run",
        "phase_id": mode.replace("/", "_").replace(":", "_")[:128],
        "attempt_number": 1,
        "pi_argv0": str(FIXTURE),
        "timeout_seconds": 2.0,
        "term_grace_seconds": 0.15,
        "verification_grace_seconds": 0.6,
        "max_stdout_bytes": 100_000,
        "max_stderr_bytes": 20_000,
        "max_event_bytes": 100_000,
        "total_attempt_budget": 1,
        "environment": safe_environment(),
    }
    values.update(overrides)
    return PiAdapterRequest(**values)


def evidence_path(candidate: PiAdapterRequest) -> Path:
    return Path(candidate.raw_event_path) / candidate.execution_id / candidate.phase_id / f"attempt-{candidate.attempt_number:03d}.jsonl"


def assert_reason(result, code: str, observation: Observation, errors: list[str]) -> None:
    check(result.terminal_state != TerminalState.SUCCEEDED, f"{code}: unexpectedly succeeded", errors)
    check(result.reason is not None, f"{code}: missing typed reason", errors)
    if result.reason:
        check(result.reason.code == code, f"{code}: got reason {result.reason.code}", errors)
        check(result.reason.observation == observation, f"{code}: wrong observation {result.reason.observation}", errors)


def process_absent(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return False
    except ProcessLookupError:
        return True
    except PermissionError:
        return False


def run_heredoc_parent(unsafe: bool) -> int:
    """Act like a line-driven heredoc parent whose unread tail must survive."""
    with tempfile.TemporaryDirectory(prefix="sssf-stdin-parent-") as directory:
        temp = Path(directory)
        if unsafe:
            subprocess.run(
                [str(FIXTURE), "--print", "--mode", "json", "stdin-consumption"],
                cwd=ROOT,
                env=safe_environment(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            result = run_pi_json(request(temp, "stdin-consumption"))
            if result.terminal_state != TerminalState.SUCCEEDED or result.text != "typed-success-marker":
                return 3
        tail = sys.stdin.buffer.readline().decode(errors="replace").strip()
        if tail == TYPED_TAIL:
            print(f"typed-marker:{TYPED_TAIL}")
            return 0
        print("typed-marker:missing")
        return 4


def stdin_regression(errors: list[str]) -> None:
    command = f"{shlex.quote(sys.executable)} {shlex.quote(str(Path(__file__).resolve()))} --heredoc-parent"

    def drive(mode: str) -> subprocess.CompletedProcess[bytes]:
        # The tested parent itself is fed by a real shell heredoc. Its child is
        # one level beneath that driver, matching the original failure shape.
        script = f"{command} {mode} <<'SSSF_PARENT_TAIL'\n{TYPED_TAIL}\nSSSF_PARENT_TAIL\n"
        return subprocess.run(
            ["sh", "-c", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            cwd=ROOT,
        )

    unsafe = drive("unsafe")
    check(unsafe.returncode != 0, "stdin watched-red control did not suppress the parent tail", errors)
    check(b"typed-marker:missing" in unsafe.stdout, "stdin watched-red control lacked missing typed marker", errors)

    safe = drive("safe")
    check(safe.returncode == 0, f"closed-stdin regression failed: {safe.stderr.decode(errors='replace')}", errors)
    check(f"typed-marker:{TYPED_TAIL}".encode() in safe.stdout, "closed stdin suppressed the required typed marker", errors)


def static_contract(errors: list[str]) -> None:
    check(correction_attempt_budget(0) == 3, "zero-retry correction budget is not three launches", errors)
    check(correction_attempt_budget(2) == 9, "multi-round correction budget does not bound every send", errors)
    with tempfile.TemporaryDirectory(prefix="sssf-static-") as directory:
        temp = Path(directory)
        candidate = request(temp, "success", tools=[])
        argv, refusal = build_argv(candidate)
        check(refusal is None and argv is not None, "strict Pi argv was refused", errors)
        if argv:
            required = {
                "--print",
                "--no-session",
                "--no-extensions",
                "--no-skills",
                "--no-prompt-templates",
                "--no-context-files",
                "--no-approve",
                "--no-tools",
            }
            check(required <= set(argv), f"strict Pi argv missing {sorted(required - set(argv))}", errors)
            check(argv[argv.index("--mode") + 1] == "json", "Pi mode is not JSON", errors)
            check(argv[argv.index("--provider") + 1] == "fixture", "Pi provider drifted", errors)
            check(argv[argv.index("--model") + 1] == "deterministic", "Pi model drifted", errors)
            check(argv[argv.index("--thinking") + 1] == "high", "Pi effort drifted", errors)
            check("--models" not in argv and "--continue" not in argv and "--resume" not in argv, "Pi fallback/session flag present", errors)
        forbidden = ("KEY", "TOKEN", "CREDENTIAL", "AUTH", "COOKIE", "HOME", "PASSWORD", "SECRET")
        exposed_names = set(candidate.environment) | set(candidate.environment_allowlist) | set(PI_OWNED_ENV_NAMES)
        check(not [name for name in exposed_names if any(word in name.upper() for word in forbidden)], "credential/auth-home environment name entered adapter contract", errors)
        check(all("secret" not in arg.lower() for arg in (argv or [])), "credential-like value entered argv", errors)

        for bad, code in (
            (request(temp, "success", provider_model="deterministic"), "pi-target-not-fully-qualified"),
            (request(temp, "success", provider_model="fixture/*"), "pi-target-not-fully-qualified"),
            (request(temp, "success", thinking="default"), "pi-thinking-not-explicit"),
            (request(temp, "success", tools=None), "pi-tool-policy-not-exact"),
            (request(temp, "success", tools=["read", "read"]), "pi-tool-policy-not-exact"),
            (
                request(
                    temp,
                    "success",
                    environment={"PROVIDER_TOKEN": "fixture-not-a-secret"},
                    environment_allowlist=frozenset({"PROVIDER_TOKEN"}),
                ),
                "pi-sensitive-environment-refused",
            ),
            (
                request(
                    temp,
                    "success",
                    environment={"DATABASE_PASSWORD": "fixture-not-a-secret"},
                    environment_allowlist=frozenset({"DATABASE_PASSWORD"}),
                ),
                "pi-sensitive-environment-refused",
            ),
            (
                request(
                    temp,
                    "success",
                    environment={"CUSTOM_MODE": "fixture"},
                    environment_allowlist=frozenset({"CUSTOM_MODE"}),
                ),
                "pi-environment-not-allowlisted",
            ),
        ):
            result = run_pi_json(bad)
            assert_reason(result, code, Observation.COULD_NOT_OBSERVE, errors)
            check(result.process is None, f"{code}: refusal launched a child", errors)


def platform_refusal(errors: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="sssf-windows-refusal-") as directory:
        result = run_pi_json(request(Path(directory), "success", platform_name="windows"))
    assert_reason(result, "windows-job-object-unavailable", Observation.COULD_NOT_OBSERVE, errors)
    check(result.process is None, "Windows refusal launched an uncontained process", errors)


def runtime_fixtures(errors: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="sssf-executor-") as directory:
        temp = Path(directory)
        success_request = request(temp, "success")
        success = run_pi_json(success_request)
        check(success.terminal_state == TerminalState.SUCCEEDED, f"success fixture failed: {success.reason}", errors)
        check(success.text == "typed-success-marker", "success text marker missing", errors)
        check(success.requested_provider == "fixture" and success.requested_model == "deterministic", "requested target missing", errors)
        check(success.resolved_provider == "fixture" and success.resolved_model == "deterministic", "resolved target missing", errors)
        check(success.requested_effort == "high" and success.resolved_effort == "high", "effort evidence missing", errors)
        check(success.terminal_stop == "stop" and success.terminal_error is None, "terminal stop evidence wrong", errors)
        check(success.usage.usage_source_class == "provider-reported", "usage source class missing", errors)
        check(success.usage.cost_source_class == "provider-reported" and success.usage.total_cost == 0.125, "cost source class missing", errors)
        check(success.attempts.native_attempts == 1 and success.attempts.budget == 1, "native attempt accounting wrong", errors)
        check(success.process is not None and success.cleanup.reaped and success.cleanup.group_absent is True, "process identity/cleanup proof missing", errors)
        check(success.evidence.stdout_sha256 == success.evidence.raw_events_sha256, "raw event digest does not reconcile", errors)
        raw = evidence_path(success_request)
        check(raw.is_file() and raw.stat().st_size > 0, "bounded raw events were not preserved", errors)

        structured = run_pi_json(request(temp, "structured-error"))
        assert_reason(structured, "structured-provider-error", Observation.OBSERVED_BAD, errors)
        check(structured.returncode == 0, "structured error fixture did not exit shell zero", errors)
        check(structured.terminal_error == "deterministic provider rejection", "structured terminal error missing", errors)

        for target_mode, target_code, target_observation in (
            ("missing", "resolved-target-unverified", Observation.COULD_NOT_OBSERVE),
            ("incomplete", "resolved-target-unverified", Observation.COULD_NOT_OBSERVE),
            ("drifting", "resolved-target-mismatch", Observation.OBSERVED_BAD),
        ):
            provider_error = run_pi_json(request(temp, f"structured-error-{target_mode}"))
            assert_reason(provider_error, "structured-provider-error", Observation.OBSERVED_BAD, errors)
            check(provider_error.returncode == 0, f"structured-error-{target_mode}: shell exit was not zero", errors)
            check(
                provider_error.primary_reason is not None
                and provider_error.primary_reason.code == "structured-provider-error",
                f"structured-error-{target_mode}: provider error was not the primary verdict",
                errors,
            )
            check(
                len(provider_error.resolved_targets) == 1
                and provider_error.resolved_targets[0].failure is not None
                and provider_error.resolved_targets[0].failure.code == target_code
                and provider_error.resolved_targets[0].failure.observation == target_observation,
                f"structured-error-{target_mode}: secondary target evidence was not retained",
                errors,
            )

        mismatch = run_pi_json(request(temp, "success", provider_model="fixture/other", phase_id="target-mismatch"))
        assert_reason(mismatch, "resolved-target-mismatch", Observation.OBSERVED_BAD, errors)

        fallback = run_pi_json(request(temp, "early-fallback-then-success"))
        assert_reason(fallback, "resolved-target-mismatch", Observation.OBSERVED_BAD, errors)
        check(len(fallback.resolved_targets) == 2, "target drift did not retain both message_end identities", errors)
        check(
            fallback.resolved_targets[0].event_index == 0
            and fallback.resolved_targets[0].provider == "fallback"
            and fallback.resolved_targets[0].failure is not None
            and fallback.resolved_targets[0].failure.code == "resolved-target-mismatch"
            and fallback.resolved_targets[1].event_index == 2
            and fallback.resolved_targets[1].provider == "fixture",
            "later matching target overwrote earlier drift evidence",
            errors,
        )

        incomplete = run_pi_json(request(temp, "incomplete-then-success"))
        assert_reason(incomplete, "resolved-target-unverified", Observation.COULD_NOT_OBSERVE, errors)
        check(
            len(incomplete.resolved_targets) == 2
            and incomplete.resolved_targets[0].effort is None
            and incomplete.resolved_targets[0].failure is not None
            and incomplete.resolved_targets[0].failure.code == "resolved-target-unverified"
            and incomplete.resolved_targets[1].effort == "high",
            "later complete target cured or erased incomplete target evidence",
            errors,
        )

        collision = run_pi_json(success_request)
        assert_reason(collision, "raw-evidence-identity-collision", Observation.COULD_NOT_OBSERVE, errors)
        other_phase = request(temp, "success", phase_id="other-phase")
        check(run_pi_json(other_phase).terminal_state == TerminalState.SUCCEEDED, "phase-scoped evidence identity collided", errors)
        check(evidence_path(other_phase) != raw and evidence_path(other_phase).is_file(), "multi-phase evidence was not preserved separately", errors)

        for mode, code, observation in (
            ("malformed", "malformed-json-event", Observation.COULD_NOT_OBSERVE),
            ("missing-terminal", "missing-terminal-event", Observation.COULD_NOT_OBSERVE),
            ("duplicate-terminal", "duplicate-terminal-event", Observation.OBSERVED_BAD),
        ):
            assert_reason(run_pi_json(request(temp, mode)), code, observation, errors)

        retry = run_pi_json(request(temp, "hidden-retry", total_attempt_budget=2))
        assert_reason(retry, "native-retry-policy-violation", Observation.OBSERVED_BAD, errors)
        check(retry.attempts.native_attempts == 2 and retry.attempts.native_retry_events == 1, "hidden retry was not individually observed/charged", errors)

        shared_budget = AttemptBudget(1)
        first = run_pi_json(request(temp, "success", phase_id="shared-budget", attempt_number=1), budget=shared_budget)
        second = run_pi_json(request(temp, "success", phase_id="shared-budget", attempt_number=2), budget=shared_budget)
        check(first.terminal_state == TerminalState.SUCCEEDED, "shared-budget first attempt failed", errors)
        assert_reason(second, "attempt-budget-exhausted", Observation.COULD_NOT_OBSERVE, errors)
        check(second.process is None and shared_budget.used == 1, "spent total attempt budget launched again", errors)

        timeout = run_pi_json(request(temp, "timeout", timeout_seconds=0.15))
        assert_reason(timeout, "wall-timeout", Observation.COULD_NOT_OBSERVE, errors)
        check(timeout.timed_out and timeout.cleanup.reaped and timeout.cleanup.group_absent is True, "timeout cleanup incomplete", errors)

        ignored = run_pi_json(request(temp, "ignored-term", timeout_seconds=0.15))
        assert_reason(ignored, "wall-timeout", Observation.COULD_NOT_OBSERVE, errors)
        check(ignored.cleanup.term_sent and ignored.cleanup.kill_sent, "ignored TERM did not escalate to KILL", errors)

        pid_path = temp / "descendant.pid"
        descendant = run_pi_json(request(temp, f"descendant:{pid_path}"))
        assert_reason(descendant, "descendant-outlived-parent", Observation.OBSERVED_BAD, errors)
        check(descendant.cleanup.descendants_seen and not descendant.cleanup.survivors, "descendant was not tracked and verified absent", errors)
        if pid_path.is_file():
            child_pid = int(pid_path.read_text())
            check(process_absent(child_pid), "escaped descendant survived cleanup", errors)
        else:
            errors.append("descendant fixture did not record its PID")

        instant_pid_path = temp / "instant-descendant.pid"
        instant = run_pi_json(request(temp, f"instant-descendant:{instant_pid_path}"))
        assert_reason(instant, "descendant-outlived-parent", Observation.OBSERVED_BAD, errors)
        check(instant.cleanup.descendants_seen and not instant.cleanup.survivors, "immediate-parent-exit descendant escaped custody", errors)
        if instant_pid_path.is_file():
            check(process_absent(int(instant_pid_path.read_text())), "immediate-parent-exit descendant survived cleanup", errors)
        else:
            errors.append("immediate-parent-exit fixture did not record its PID")

        late_pid_path = temp / "late-fork.pid"
        late_fork = run_pi_json(request(temp, f"late-fork:{late_pid_path}", timeout_seconds=0.15))
        assert_reason(late_fork, "wall-timeout", Observation.COULD_NOT_OBSERVE, errors)
        check(late_fork.cleanup.descendants_seen and not late_fork.cleanup.survivors, "TERM-handler descendant escaped cleanup rescan", errors)
        if late_pid_path.is_file():
            check(process_absent(int(late_pid_path.read_text())), "late-forked descendant survived cleanup", errors)
        else:
            errors.append("late-fork fixture did not record its PID")

        overflow = run_pi_json(request(temp, "overflow", max_stdout_bytes=4096, max_event_bytes=4096))
        assert_reason(overflow, "output-overflow", Observation.COULD_NOT_OBSERVE, errors)
        check(overflow.stdout_bytes_seen > 4096 and overflow.event_bytes_preserved == 4096, "output bound was not enforced", errors)

        event_overflow = run_pi_json(request(temp, "success", phase_id="event-overflow", max_event_bytes=100))
        assert_reason(event_overflow, "event-overflow", Observation.COULD_NOT_OBSERVE, errors)

        live_cancel = threading.Event()
        timer = threading.Timer(0.08, live_cancel.set)
        timer.start()
        cancelled = run_pi_json(request(temp, "slow-success"), cancel_event=live_cancel)
        timer.join()
        assert_reason(cancelled, "cancelled", Observation.COULD_NOT_OBSERVE, errors)
        check(cancelled.cancelled and cancelled.cleanup.reaped, "live cancellation cleanup incomplete", errors)

        # Cancellation after a claim keeps its spent attempt: the claim is real
        # work and is never refunded to make accounting look cheaper.
        after_claim_budget = AttemptBudget(1)
        after_claim_cancel = threading.Event()
        timer = threading.Timer(0.08, after_claim_cancel.set)
        timer.start()
        after_claim = run_pi_json(
            request(temp, "slow-success", phase_id="cancel-after-claim"),
            budget=after_claim_budget,
            cancel_event=after_claim_cancel,
        )
        timer.join()
        assert_reason(after_claim, "cancelled", Observation.COULD_NOT_OBSERVE, errors)
        check(after_claim.cancelled and after_claim.process is not None, "cancellation after a claim lost its process identity", errors)
        check(
            after_claim_budget.used == 1 and after_claim.attempts.native_attempts == 1 and after_claim.attempts.supervisor_attempt == 1,
            f"cancellation after a claim refunded its attempt: used={after_claim_budget.used} attempts={after_claim.attempts.native_attempts}",
            errors,
        )

        # Negative control: a cancellation already set before invocation must be
        # observed before the attempt budget is touched, so nothing is claimed,
        # nothing is spawned, and no callback is invoked.
        preset_budget = AttemptBudget(1)
        preset_cancel = threading.Event()
        preset_cancel.set()
        preset_spawned: list[int] = []
        preset_exited: list[int] = []
        preset_events: list[str] = []
        preset = run_pi_json(
            request(temp, "success", phase_id="cancel-preset"),
            budget=preset_budget,
            cancel_event=preset_cancel,
            on_event=lambda event: preset_events.append(event["type"]),
            on_spawn=preset_spawned.append,
            on_exit=preset_exited.append,
        )
        assert_reason(preset, "cancelled-before-launch", Observation.COULD_NOT_OBSERVE, errors)
        check(preset.cancelled, "pre-set cancellation was not typed as cancelled", errors)
        check(preset_budget.used == 0, f"pre-set cancellation consumed attempt budget: used={preset_budget.used}", errors)
        check(
            preset.attempts.native_attempts == 0 and preset.attempts.supervisor_attempt is None,
            f"pre-set cancellation claimed a native attempt: {preset.attempts}",
            errors,
        )
        check(preset.process is None and not preset.provider_launched, "pre-set cancellation produced a provider process", errors)
        check(
            preset.cleanup.custodian_pid is None and not preset.cleanup.attempted,
            f"pre-set cancellation produced a custodian: {preset.cleanup.detail}",
            errors,
        )
        check(
            not preset_spawned and not preset_exited and not preset_events,
            f"pre-set cancellation invoked callbacks: spawn={preset_spawned} exit={preset_exited} event={preset_events}",
            errors,
        )

        # Negative control: a cancellation arriving inside the pre-launch setup
        # window must fail closed before the custodian starts, while still
        # keeping the attempt it already claimed.
        setup_budget = AttemptBudget(1)
        setup_cancel = DeferredCancellation()
        setup_spawned: list[int] = []
        setup_exited: list[int] = []
        environment = safe_environment()
        setup_result = supervise(
            SupervisorRequest(
                argv=[str(FIXTURE), "--print", "--mode", "json", "success"],
                cwd=str(ROOT),
                environment=environment,
                environment_allowlist=frozenset(environment),
                timeout_seconds=2.0,
                term_grace_seconds=0.15,
                verification_grace_seconds=0.6,
            ),
            budget=setup_budget,
            cancel_event=setup_cancel,
            on_spawn=setup_spawned.append,
            on_exit=setup_exited.append,
        )
        assert_reason(setup_result, "cancelled-before-launch", Observation.COULD_NOT_OBSERVE, errors)
        check(setup_cancel.observations >= 2, "pre-launch setup never rechecked cancellation before the custodian", errors)
        check(setup_result.cancelled, "pre-launch setup cancellation was not typed as cancelled", errors)
        check(
            setup_budget.used == 1 and setup_result.attempt_number == 1,
            f"pre-launch setup cancellation refunded its claimed attempt: used={setup_budget.used}",
            errors,
        )
        check(setup_result.process is None, "pre-launch setup cancellation launched a provider process", errors)
        check(
            setup_result.cleanup.custodian_pid is None and not setup_result.cleanup.attempted,
            f"pre-launch setup cancellation started a custodian: {setup_result.cleanup.detail}",
            errors,
        )
        check(not setup_spawned and not setup_exited, "pre-launch setup cancellation invoked spawn/exit callbacks", errors)

        late_cancel = threading.Event()
        timer = threading.Timer(0.25, late_cancel.set)
        timer.start()
        completed = run_pi_json(request(temp, "success", phase_id="late-cancel"), cancel_event=late_cancel)
        timer.join()
        check(completed.terminal_state == TerminalState.SUCCEEDED and not completed.cancelled, "late cancellation overrode completed process", errors)

        unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            isolated = run_pi_json(request(temp, "slow-success", phase_id="unrelated-control"))
            check(isolated.terminal_state == TerminalState.SUCCEEDED, "custodian isolation control failed", errors)
            check(unrelated.poll() is None, "supervisor captured an unrelated coordinator child", errors)
        finally:
            unrelated.terminate()
            unrelated.wait(timeout=2)

        startup = run_pi_json(request(temp, "success", phase_id="startup-failure", custodian_fault="startup"))
        assert_reason(startup, "cleanup-unverified", Observation.COULD_NOT_OBSERVE, errors)
        check(startup.process is None and startup.cleanup.custodian_pid is None, "startup failure claimed a live custodian", errors)

        broken = run_pi_json(request(temp, "timeout", phase_id="broken-ipc", custodian_fault="broken-ipc", timeout_seconds=0.15))
        assert_reason(broken, "cleanup-unverified", Observation.COULD_NOT_OBSERVE, errors)
        check(broken.cleanup.custodian_pid is not None, "broken IPC omitted custodian identity", errors)

        def reject_spawn(_pid: int) -> None:
            raise RuntimeError("fixture callback rejection")

        callback = run_pi_json(request(temp, "slow-success", phase_id="callback-failure"), on_spawn=reject_spawn)
        assert_reason(callback, "cleanup-unverified", Observation.COULD_NOT_OBSERVE, errors)
        check(callback.cleanup.group_absent is True and not callback.cleanup.survivors, "callback failure returned before verified cleanup", errors)

        delivered = []

        def reject_first_event(event: dict) -> None:
            delivered.append(event["type"])
            raise RuntimeError("fixture event delivery rejection")

        before_terminal_request = request(temp, "success", phase_id="event-callback-before-terminal")
        before_terminal = run_pi_json(before_terminal_request, on_event=reject_first_event)
        assert_reason(before_terminal, "observation-delivery-failed", Observation.COULD_NOT_OBSERVE, errors)
        check(delivered == ["session"], "failed event callback was invoked again", errors)
        check(before_terminal.primary_terminal_state == TerminalState.SUCCEEDED and before_terminal.primary_reason is None, "callback CNO erased structured success", errors)
        check(before_terminal.returncode == 0 and before_terminal.cleanup.group_absent is True, "callback CNO lost exit or cleanup evidence", errors)
        check(before_terminal.evidence.raw_events_sha256 == before_terminal.evidence.stdout_sha256 and evidence_path(before_terminal_request).is_file(), "callback CNO lost durable raw evidence", errors)

        delivered.clear()

        def reject_terminal_event(event: dict) -> None:
            delivered.append(event["type"])
            if event["type"] == "agent_end":
                raise RuntimeError("fixture terminal delivery rejection")

        after_terminal = run_pi_json(request(temp, "terminal-first-success", phase_id="event-callback-after-terminal"), on_event=reject_terminal_event)
        assert_reason(after_terminal, "observation-delivery-failed", Observation.COULD_NOT_OBSERVE, errors)
        check(delivered == ["message_end", "agent_end"], "post-terminal events were delivered after callback failure", errors)
        check(after_terminal.primary_terminal_state == TerminalState.SUCCEEDED and after_terminal.terminal_stop == "stop", "terminal callback CNO erased provider outcome", errors)

        for fault in ("mkdir", "create", "reserve-close"):
            setup_request = request(temp, "success", phase_id=f"evidence-setup-{fault}", evidence_fault=fault)
            setup_failure = run_pi_json(setup_request)
            assert_reason(setup_failure, "evidence-setup-unobservable", Observation.COULD_NOT_OBSERVE, errors)
            check(not setup_failure.provider_launched and setup_failure.process is None, f"{fault}: evidence setup failure launched provider", errors)
            check(setup_failure.attempts.native_attempts == 0 and setup_failure.evidence.raw_events_sha256 is None, f"{fault}: evidence setup accounting was dishonest", errors)

        for fault in ("reopen", "write", "flush", "fsync", "final-close"):
            delivered.clear()
            persistence_request = request(temp, "success", phase_id=f"evidence-persistence-{fault}", evidence_fault=fault)
            persistence_failure = run_pi_json(persistence_request, on_event=lambda event: delivered.append(event["type"]))
            assert_reason(persistence_failure, "evidence-persistence-unobservable", Observation.COULD_NOT_OBSERVE, errors)
            check(persistence_failure.provider_launched and persistence_failure.process is not None, f"{fault}: completed provider identity was lost", errors)
            check(persistence_failure.primary_terminal_state == TerminalState.SUCCEEDED and persistence_failure.cleanup.group_absent is True, f"{fault}: primary process or cleanup evidence was lost", errors)
            check(not persistence_failure.evidence_persisted and persistence_failure.evidence.raw_events_sha256 is None, f"{fault}: partial evidence claimed a durable digest", errors)
            check(persistence_failure.attempts.native_attempts == 1 and not persistence_failure.attempts.fully_observable, f"{fault}: persistence attempt accounting was dishonest", errors)
            check(not delivered, f"{fault}: callback ran without durable evidence", errors)
            collision_after_partial = run_pi_json(persistence_request)
            assert_reason(collision_after_partial, "raw-evidence-identity-collision", Observation.COULD_NOT_OBSERVE, errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--heredoc-parent", choices=("safe", "unsafe"))
    args = parser.parse_args()
    if args.heredoc_parent:
        return run_heredoc_parent(args.heredoc_parent == "unsafe")

    errors: list[str] = []
    static_contract(errors)
    platform_refusal(errors)
    if os.name == "posix":
        stdin_regression(errors)
        runtime_fixtures(errors)
    else:
        # This is an explicit CNO/refusal, not a skipped claim: Windows CI runs
        # static/parser controls and proves that no uncontained child launches.
        print("windows-runtime: could-not-observe; Job Object path unavailable and launch refused")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("executor-supervisor: PASS")
    print("watched-red: inherited stdin, malformed/missing/duplicate terminal, structured shell-zero error, hidden retry, timeout, overflow, cancellation (live, late, pre-set, pre-launch-setup)")
    print("provider-calls: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
