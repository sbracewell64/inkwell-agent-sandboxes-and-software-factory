"""Deterministic SBX-1 contract/fake coverage; no external provider calls."""

from __future__ import annotations

from adw_modules.sandbox_provider import (
    CommandSpec,
    FakeSandboxProvider,
    Observation,
    OperationKind,
    OperationKey,
    SandboxSpec,
    StdinPolicy,
    fold_aggregate,
    OutcomeCheck,
)

import importlib.util
from pathlib import Path

_validator_path = Path(__file__).parents[1] / "docs" / "validation" / "check_sandbox_provider.py"
_validator_spec = importlib.util.spec_from_file_location("sbx1_validator", _validator_path)
assert _validator_spec is not None and _validator_spec.loader is not None
_validator = importlib.util.module_from_spec(_validator_spec)
_validator_spec.loader.exec_module(_validator)
run_controls = _validator.run_controls
spec = _validator.spec
load_status_surfaces = _validator.load_status_surfaces
status_surface_errors = _validator.status_surface_errors


def test_all_sbx1_watched_red_controls_are_nonvacuous() -> None:
    assert run_controls() == []


def test_spec_and_command_are_immutable_typed_projections() -> None:
    sandbox = spec()
    assert sandbox.source_identity.commit == "1" * 40
    assert sandbox.source_identity.tree == "2" * 40
    assert sandbox.identity_digest
    try:
        sandbox.run_id = "changed"  # type: ignore[misc]
    except (AttributeError, TypeError):
        pass
    else:
        raise AssertionError("SandboxSpec was mutable")

    command = CommandSpec(
        argv=("/usr/bin/true",),
        guest_cwd="/workspace",
        environment_refs=("LANG",),
        environment_allowlist=frozenset({"LANG"}),
        stdin_policy=StdinPolicy.CLOSED,
        timeout_seconds=1,
        max_stdout_bytes=32,
        max_stderr_bytes=32,
        execution_id="exec-1",
        attempt_id="attempt-1",
        cancellation_id="cancel-1",
    )
    assert command.supervisor_projection["stdin_closed"] is True
    assert command.supervisor_projection["argv"] == ("/usr/bin/true",)
    projected = command.to_supervisor_request({"LANG": "C"})
    assert tuple(projected.argv) == ("/usr/bin/true",)


def test_landed_status_rejects_false_acceptance_and_sbx2_promotion() -> None:
    surfaces = load_status_surfaces()
    assert status_surface_errors(surfaces) == []
    increment = Path("docs/increments/SBX-1_SANDBOX_PROVIDER_CONTRACT.md")
    surfaces[increment] = surfaces[increment].replace(
        "SBX-1 is a **landed implementation**. SBX-1 is not activated, not accepted,\n"
        "not certified, and not real-provider-proven; it does not unlock SBX-2.",
        "SBX-1 is accepted and real-provider-proven. SBX-1 unlocks SBX-2.",
        1,
    )
    observed = status_surface_errors(surfaces)
    assert observed
    assert any("false lifecycle claim" in error for error in observed)


def test_fake_is_in_process_and_aggregate_keeps_cleanup_cno() -> None:
    sandbox = spec()
    provider = FakeSandboxProvider()
    created = provider.create(
        sandbox,
        OperationKey.for_spec(sandbox, OperationKind.CREATE),
    )
    assert created.observation is Observation.OBSERVED_GOOD
    assert provider.external_call_count == 0
    folded = fold_aggregate(
        work=(OutcomeCheck("work", Observation.OBSERVED_GOOD),),
        cleanup=(OutcomeCheck("cleanup", Observation.COULD_NOT_OBSERVE, reason="unreachable"),),
        evidence=(OutcomeCheck("evidence", Observation.OBSERVED_GOOD),),
    )
    assert folded.status is Observation.COULD_NOT_OBSERVE
    assert folded.work.observation is Observation.OBSERVED_GOOD
    assert folded.cleanup.observation is Observation.COULD_NOT_OBSERVE
