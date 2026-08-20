#!/usr/bin/env python3
"""Provider-free SBX-1 contract and watched-red fake controls.

The fake is deliberately in-process.  ``external_call_count`` must remain
zero: this validator never invokes Docker, exe.dev, a provider, a model, a
browser, or a network.  Each watched-red control checks typed observations and
positive state evidence, not merely an error string.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from adws.adw_modules.sandbox_provider import (  # noqa: E402
    ArtifactSpec,
    CapabilityDisposition,
    CapabilityFact,
    CommandSpec,
    CopySpec,
    DestroyNotAuthorized,
    FakeControl,
    FakeSandboxProvider,
    GitExportSpec,
    InMemoryLifecycleRecordStore,
    InterruptTiming,
    LifecycleBoundary,
    LifecycleOperationRecord,
    LifecycleState,
    Observation,
    OperationKey,
    OperationKind,
    OutcomeCheck,
    QuiescenceDomain,
    ResourceBounds,
    SandboxIdentity,
    SandboxSpec,
    SourceIdentity,
    StdinPolicy,
    WorkspaceMode,
    fold_aggregate,
    issue_destroy_authorization,
    validate_artifact_export,
    validate_git_export,
)


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def spec() -> SandboxSpec:
    return SandboxSpec(
        run_id="sbx-fixture-run",
        operation_id="create-fixture",
        source_repo="https://example.invalid/sssf.git",
        source_commit="1" * 40,
        source_tree="2" * 40,
        profile_id="profile/deterministic",
        template_id="template/v1",
        toolchain_id="toolchain/v1",
        workspace_mode=WorkspaceMode.BROKER_CLONE,
        resource_bounds=ResourceBounds(
            cpu_millis=500,
            memory_bytes=64 * 1024 * 1024,
            pids=32,
            disk_bytes=1024 * 1024,
            network_bytes=0,
            wall_seconds=30,
        ),
        filesystem_policy_id="filesystem/readonly-source",
        network_policy_id="network/none",
        effect_policy_id="effects/none",
        exposure_policy_id="exposure/private",
        secret_refs=(),
        cognition_policy_id="cognition/fixture",
        instruction_policy_id="instructions/fixture",
        evidence_root="/evidence/sbx-fixture-run",
    )


def key(run: SandboxSpec, kind: OperationKind, suffix: str) -> OperationKey:
    return OperationKey(
        run_id=run.run_id,
        operation_id=f"{kind.value}-{suffix}",
        attempt_id=f"attempt-{suffix}",
        idempotency_key=f"{run.run_id}:{kind.value}:{suffix}",
        kind=kind,
    )


def command(run: SandboxSpec, suffix: str = "exec") -> CommandSpec:
    return CommandSpec(
        argv=("/usr/bin/true",),
        guest_cwd="/workspace",
        environment_refs=("LANG",),
        environment_allowlist=frozenset({"LANG"}),
        stdin_policy=StdinPolicy.CLOSED,
        timeout_seconds=2,
        max_stdout_bytes=64,
        max_stderr_bytes=64,
        execution_id=suffix,
        attempt_id=f"attempt-{suffix}",
        cancellation_id=f"cancel-{suffix}",
        expected_exit_codes=(0,),
    )


def make_artifact(run: SandboxSpec) -> ArtifactSpec:
    return ArtifactSpec(
        operation=key(run, OperationKind.COLLECT_ARTIFACTS, "artifact"),
        artifact_id="artifact-fixture",
        applicable=True,
        required=True,
        paths=("evidence/result.json",),
        max_files=2,
        max_total_bytes=1024,
        max_file_bytes=512,
        producer_id="fake-provider",
        purpose="sbx-fixture",
        manifest_ref="manifest/evidence-v1",
    )


def make_git(run: SandboxSpec) -> GitExportSpec:
    return GitExportSpec(
        operation=key(run, OperationKind.EXPORT_GIT, "git"),
        applicable=True,
        required=True,
        source=run.source_identity,
        expected_base_commit=run.source_commit,
        expected_base_tree=run.source_tree,
        expected_tip_commit="2" * 40,
        expected_tip_tree="3" * 40,
        max_bundle_bytes=1024,
        export_ref="refs/sandbox/sbx-fixture-run",
    )


def create(provider: FakeSandboxProvider, run: SandboxSpec) -> SandboxIdentity:
    result = provider.create(run, key(run, OperationKind.CREATE, "create"))
    if result.provider_resource_id is None:
        # Only used by controls that deliberately make create ambiguous.  The
        # normal fixture must not hide a missing identity.
        raise AssertionError(f"fixture create did not return resource identity: {result}")
    return SandboxIdentity.requested(run).with_resource(result.provider_resource_id)


def success_control(errors: list[str]) -> None:
    run = spec()
    provider = FakeSandboxProvider()
    identity = create(provider, run)
    copied = provider.copy_in(
        identity,
        CopySpec(
            operation=key(run, OperationKind.COPY_IN, "source"),
            source_ref="source-broker/fixture-clone",
            source_kind="source-broker",
            guest_path="/workspace/source",
            max_bytes=1024,
        ),
    )
    executed = provider.exec(identity, command(run), key(run, OperationKind.EXEC, "exec"))
    artifacts = provider.collect_artifacts(identity, make_artifact(run))
    git = provider.export_git(identity, make_git(run))
    processes = provider.inspect_processes(identity, key(run, OperationKind.INSPECT_PROCESSES, "processes"))
    check(copied.observation is Observation.OBSERVED_GOOD, "success: source copy did not pass", errors)
    check(executed.observation is Observation.OBSERVED_GOOD, "success: typed exec did not pass", errors)
    projection = command(run).to_supervisor_request({"LANG": "C"})
    check(tuple(projection.argv) == ("/usr/bin/true",) and projection.environment_allowlist == frozenset({"LANG"}), "success: CommandSpec did not project onto the existing supervisor", errors)
    check(executed.client_process.domain is QuiescenceDomain.HOST_PROVIDER_CLIENT, "success: host/provider-client domain missing", errors)
    check(executed.workload.domain is QuiescenceDomain.SANDBOX_WORKLOAD and executed.resources.domain is QuiescenceDomain.SANDBOX_RESOURCES, "success: workload/resource domains missing", errors)
    check(artifacts.observation is Observation.OBSERVED_GOOD and artifacts.complete and artifacts.inventory, "success: bounded artifact inventory was empty/incomplete", errors)
    check(git.observation is Observation.OBSERVED_GOOD and git.ancestry_verified is True, "success: Git ancestry was not verified", errors)
    check(git.promotion_authority.value == "none", "success: provider returned promotion authority", errors)
    check(validate_artifact_export(make_artifact(run), artifacts, provider_resource_id=identity.provider_resource_id).complete, "success: exact artifact obligation did not validate", errors)
    check(validate_git_export(make_git(run), git, provider_resource_id=identity.provider_resource_id).complete, "success: exact Git obligation did not validate", errors)
    deferred = CapabilityFact("docker-binding", CapabilityDisposition.DEFERRED, Observation.COULD_NOT_OBSERVE, "Docker mechanism binding is deferred to SBX-2")
    check(deferred.disposition is CapabilityDisposition.DEFERRED and deferred.observation is Observation.COULD_NOT_OBSERVE, "success: Docker deferred capability was not typed", errors)
    check(processes.observation is Observation.OBSERVED_GOOD and processes.resources.quiescent is True, "success: all quiescence domains were not observed", errors)
    destroy_key = key(run, OperationKind.DESTROY, "destroy")
    authorization = issue_destroy_authorization(run, identity, destroy_key, artifact=artifacts, git=git, artifact_spec=make_artifact(run), git_spec=make_git(run))
    destroyed = provider.destroy(identity, destroy_key, authorization)
    reconciled = provider.reconcile(identity, key(run, OperationKind.RECONCILE, "after-destroy"))
    check(destroyed.observation is Observation.OBSERVED_GOOD and destroyed.acknowledged, "success: destroy was not acknowledged", errors)
    check(reconciled.status.value == "absent" and reconciled.observation is Observation.OBSERVED_GOOD, "success: authoritative absence was not observed", errors)
    check(not hasattr(destroyed, "accepted"), "success: provider facts exposed acceptance authority", errors)
    check(provider.external_call_count == 0, "success: fake made an external provider call", errors)


def ambiguity_and_identity_controls(errors: list[str]) -> None:
    run = spec()
    ambiguous = FakeSandboxProvider({FakeControl.CREATE_RESPONSE_AMBIGUITY})
    create_key = key(run, OperationKind.CREATE, "ambiguous")
    first = ambiguous.create(run, create_key)
    check(first.observation is Observation.COULD_NOT_OBSERVE and first.provider_resource_id is None, "create ambiguity did not return CNO without identity", errors)
    retry = ambiguous.create(run, create_key)
    check(retry.observation is Observation.OBSERVED_GOOD and retry.provider_resource_id is not None, "ambiguous create retry did not reconcile", errors)
    check(len(ambiguous.resource_ids) == 1 and retry.provider_resource_id == ambiguous.resource_ids[0], "create retry duplicated a resource", errors)

    stale = FakeSandboxProvider({FakeControl.STALE_IDENTITY})
    identity = create(stale, run)
    inspected = stale.inspect(identity, key(run, OperationKind.INSPECT, "stale"))
    check(inspected.observation is Observation.OBSERVED_BAD and inspected.identity_observation is Observation.OBSERVED_BAD, "stale identity was not positively rejected", errors)
    wrong = SandboxIdentity(run.run_id, "f" * 64, identity.provider_resource_id)
    wrong_result = FakeSandboxProvider().inspect(wrong, key(run, OperationKind.INSPECT, "wrong"))
    check(wrong_result.observation is Observation.COULD_NOT_OBSERVE and wrong_result.observed_state is LifecycleState.UNKNOWN, "wrong identity was converted into absence", errors)


def exec_controls(errors: list[str]) -> None:
    run = spec()
    for control, expected, label in (
        (FakeControl.EXEC_TIMEOUT, Observation.COULD_NOT_OBSERVE, "timeout"),
        (FakeControl.EXEC_CANCELLED, Observation.COULD_NOT_OBSERVE, "cancellation"),
        (FakeControl.EXEC_OVERFLOW, Observation.COULD_NOT_OBSERVE, "overflow"),
        (FakeControl.PROVIDER_CLIENT_CLEANUP_CNO, Observation.COULD_NOT_OBSERVE, "provider-client-cleanup"),
        (FakeControl.WORKLOAD_LEAK, Observation.OBSERVED_BAD, "workload-leak"),
    ):
        provider = FakeSandboxProvider({control})
        identity = create(provider, run)
        result = provider.exec(identity, command(run, label), key(run, OperationKind.EXEC, label))
        check(result.observation is expected, f"exec {label}: wrong three-valued result {result.observation}", errors)
        if label == "timeout":
            check(result.timed_out and result.return_code is None, "exec timeout: no positive timeout fact", errors)
        elif label == "cancellation":
            check(result.cancelled and result.return_code is None, "exec cancellation: no positive cancellation fact", errors)
        elif label == "overflow":
            check(result.output_overflowed and result.stdout_bytes_seen > 64, "exec overflow: no positive bound violation", errors)
        elif label == "provider-client-cleanup":
            check(result.client_process.observation is Observation.COULD_NOT_OBSERVE and result.client_process.quiescent is None, "provider-client cleanup: CNO was not preserved", errors)
        else:
            check(result.workload.quiescent is False and result.workload.identities, "workload leak: no leaked workload identity", errors)


def artifact_and_git_controls(errors: list[str]) -> None:
    run = spec()
    for control, expected, label in (
        (FakeControl.ARTIFACT_MISSING, Observation.COULD_NOT_OBSERVE, "missing"),
        (FakeControl.ARTIFACT_TAMPERED, Observation.OBSERVED_BAD, "tampered"),
        (FakeControl.ARTIFACT_OVERFLOW, Observation.COULD_NOT_OBSERVE, "overflow"),
    ):
        provider = FakeSandboxProvider({control})
        identity = create(provider, run)
        result = provider.collect_artifacts(identity, make_artifact(run))
        check(result.observation is expected, f"artifact {label}: wrong result {result.observation}", errors)
        if label == "missing":
            check(result.missing_paths == ("evidence/result.json",) and not result.complete, "artifact missing: no positive missing inventory", errors)
        elif label == "tampered":
            check(result.tampered_paths == ("evidence/result.json",) and result.inventory[0].sha256 != result.inventory[0].expected_sha256, "artifact tamper: digest mismatch was not manufactured", errors)
        else:
            check(result.overflowed and not result.complete, "artifact overflow: no positive bound fact", errors)

    provider = FakeSandboxProvider({FakeControl.GIT_WRONG_ANCESTRY})
    identity = create(provider, run)
    result = provider.export_git(identity, make_git(run))
    check(result.observation is Observation.OBSERVED_BAD and result.ancestry_verified is False and result.base_commit != run.source_commit, "Git wrong ancestry: no positive ancestry contradiction", errors)

    provider = FakeSandboxProvider()
    identity = create(provider, run)
    artifact_spec = make_artifact(run)
    valid_artifact = provider.collect_artifacts(identity, artifact_spec)
    item = valid_artifact.inventory[0]
    misleading_artifacts = (
        replace(valid_artifact, tampered_paths=(item.path,)),
        replace(valid_artifact, inventory=(replace(item, sha256="0" * 64),)),
        replace(valid_artifact, inventory_sha256="0" * 64),
        replace(valid_artifact, total_bytes=valid_artifact.total_bytes + 1),
    )
    check(
        all(validate_artifact_export(artifact_spec, fact, provider_resource_id=identity.provider_resource_id).observation is Observation.OBSERVED_BAD for fact in misleading_artifacts),
        "artifact validator trusted observed-good tamper, item/inventory digest, or byte-total contradictions",
        errors,
    )
    git_spec = make_git(run)
    valid_git = provider.export_git(identity, git_spec)
    oversized_git = replace(valid_git, bundle_bytes=git_spec.max_bundle_bytes + 1)
    check(
        not validate_git_export(git_spec, oversized_git, provider_resource_id=identity.provider_resource_id).complete,
        "Git validator accepted a bundle above max_bundle_bytes",
        errors,
    )


def cleanup_and_authority_controls(errors: list[str]) -> None:
    run = spec()
    partial = FakeSandboxProvider({FakeControl.STOP_PARTIAL})
    identity = create(partial, run)
    stopped = partial.stop(identity, key(run, OperationKind.STOP, "partial"))
    check(stopped.observation is Observation.OBSERVED_BAD and stopped.acknowledged and stopped.workload_stopped is False, "partial stop: no positive residual workload fact", errors)

    unauthorized = FakeSandboxProvider()
    identity = create(unauthorized, run)
    denied = unauthorized.destroy(identity, key(run, OperationKind.DESTROY, "unauthorized"), None)
    check(denied.observation is Observation.OBSERVED_BAD and not denied.acknowledged, "unauthorized destroy was not refused", errors)

    residual = FakeSandboxProvider({FakeControl.DESTROY_RESIDUAL})
    identity = create(residual, run)
    artifact = residual.collect_artifacts(identity, make_artifact(run))
    git = residual.export_git(identity, make_git(run))
    destroy_key = key(run, OperationKind.DESTROY, "residual")
    auth = issue_destroy_authorization(run, identity, destroy_key, artifact=artifact, git=git, artifact_spec=make_artifact(run), git_spec=make_git(run))
    destroyed = residual.destroy(identity, destroy_key, auth)
    reconciled = residual.reconcile(identity, key(run, OperationKind.RECONCILE, "residual"))
    check(destroyed.observation is Observation.OBSERVED_BAD and destroyed.acknowledged and destroyed.residual_resource_ids, "residual destroy: acknowledgement/residue was not positive", errors)
    check(reconciled.status.value == "residual" and reconciled.observation is Observation.OBSERVED_BAD, "residual destroy: reconciliation did not distinguish residue", errors)

    unreachable = FakeSandboxProvider({FakeControl.INSPECT_UNREACHABLE})
    identity = create(unreachable, run)
    inspected = unreachable.inspect(identity, key(run, OperationKind.INSPECT, "unreachable"))
    reconciled = unreachable.reconcile(identity, key(run, OperationKind.RECONCILE, "unreachable"))
    check(inspected.observation is Observation.COULD_NOT_OBSERVE and inspected.observed_state is LifecycleState.UNKNOWN, "unreachable inspect: CNO became a state assertion", errors)
    check(reconciled.status.value == "could-not-observe" and reconciled.observation is Observation.COULD_NOT_OBSERVE, "unreachable reconcile: failure became absence", errors)

    absent = FakeSandboxProvider({FakeControl.ALREADY_ABSENT})
    identity = create(absent, run)
    artifact = absent.collect_artifacts(identity, make_artifact(run))
    git = absent.export_git(identity, make_git(run))
    auth = issue_destroy_authorization(run, identity, key(run, OperationKind.DESTROY, "absent"), artifact=artifact, git=git, artifact_spec=make_artifact(run), git_spec=make_git(run))
    destroyed = absent.destroy(identity, key(run, OperationKind.DESTROY, "absent"), auth)
    check(destroyed.observation is Observation.OBSERVED_GOOD and destroyed.already_absent, "already absent: destroy was not idempotent", errors)

    duplicate = FakeSandboxProvider({FakeControl.DUPLICATE_RESOURCES})
    duplicate_identity = create(duplicate, run)
    reconciled = duplicate.reconcile(duplicate_identity, key(run, OperationKind.RECONCILE, "duplicate"))
    check(reconciled.status.value == "duplicate" and len(reconciled.duplicate_resource_ids) == 2, "duplicate reconciliation: duplicate resources were not enumerated", errors)

    try:
        issue_destroy_authorization(run, SandboxIdentity.requested(run), key(run, OperationKind.DESTROY, "no-resource"), artifact=artifact, git=git, artifact_spec=make_artifact(run), git_spec=make_git(run))
    except DestroyNotAuthorized:
        pass
    else:
        errors.append("destroy authorization without provider identity was minted")

    try:
        issue_destroy_authorization(
            run,
            identity,
            key(run, OperationKind.DESTROY, "inapplicable-obligation"),
            artifact=artifact,
            git=git,
            artifact_spec=replace(make_artifact(run), applicable=False, required=False),
            git_spec=make_git(run),
        )
    except DestroyNotAuthorized:
        pass
    else:
        errors.append("destroy authorization accepted an inapplicable artifact obligation")

    interrupted = FakeSandboxProvider(interrupt_before=LifecycleBoundary.DESTROY)
    identity = create(interrupted, run)
    artifact_spec = make_artifact(run)
    git_spec = make_git(run)
    artifact = interrupted.collect_artifacts(identity, artifact_spec)
    git = interrupted.export_git(identity, git_spec)
    destroy_key = key(run, OperationKind.DESTROY, "retry-before-linearization")
    auth = issue_destroy_authorization(run, identity, destroy_key, artifact=artifact, git=git, artifact_spec=artifact_spec, git_spec=git_spec)
    first = interrupted.destroy(identity, destroy_key, auth)
    interrupted.interrupt_before = None
    retry = interrupted.destroy(identity, destroy_key, auth)
    check(first.observation is Observation.COULD_NOT_OBSERVE and retry.acknowledged, "pre-linearization destroy interruption consumed retry authority", errors)


def aggregate_controls(errors: list[str]) -> None:
    good = OutcomeCheck("work-good", Observation.OBSERVED_GOOD)
    cno = OutcomeCheck("cleanup-cno", Observation.COULD_NOT_OBSERVE, reason="cleanup unreachable")
    bad = OutcomeCheck("work-fail", Observation.OBSERVED_BAD, reason="contradiction")
    wrong = OutcomeCheck("wrong-identity", Observation.OBSERVED_GOOD, identity_verified=False, reason="identity was not verified")
    incomplete = OutcomeCheck("incomplete", Observation.OBSERVED_GOOD, complete=False, reason="inventory incomplete")
    for label, result, expected in (
        ("pass", fold_aggregate(work=(good,), cleanup=(good,), evidence=(good,)), Observation.OBSERVED_GOOD),
        ("cleanup-cno", fold_aggregate(work=(good,), cleanup=(cno,), evidence=(good,)), Observation.COULD_NOT_OBSERVE),
        ("fail-precedence", fold_aggregate(work=(bad,), cleanup=(cno,), evidence=(good,)), Observation.OBSERVED_BAD),
        ("wrong-identity", fold_aggregate(work=(wrong,), cleanup=(good,), evidence=(good,)), Observation.COULD_NOT_OBSERVE),
        ("incomplete", fold_aggregate(work=(incomplete,), cleanup=(good,), evidence=(good,)), Observation.COULD_NOT_OBSERVE),
        ("empty", fold_aggregate(), Observation.COULD_NOT_OBSERVE),
    ):
        check(result.status is expected, f"aggregate {label}: precedence/result was {result.status}", errors)
    cno_result = fold_aggregate(work=(good,), cleanup=(cno,), evidence=(good,))
    check(cno_result.work.observation is Observation.OBSERVED_GOOD and cno_result.cleanup.observation is Observation.COULD_NOT_OBSERVE, "aggregate cleanup CNO erased separate work/cleanup observations", errors)


def interruption_controls(errors: list[str]) -> None:
    run = spec()
    # Every boundary is positively manufactured as a CNO.  For boundaries with
    # a provider operation, the resource identity remains recoverable after
    # the interruption; secret retirement is an SSSF-owned observation.
    provider_boundaries = (
        (LifecycleBoundary.CREATE, OperationKind.CREATE),
        (LifecycleBoundary.SOURCE_COPY, OperationKind.COPY_IN),
        (LifecycleBoundary.SETUP, OperationKind.EXEC),
        (LifecycleBoundary.EXEC, OperationKind.EXEC),
        (LifecycleBoundary.ARTIFACT_EXPORT, OperationKind.COLLECT_ARTIFACTS),
        (LifecycleBoundary.GIT_EXPORT, OperationKind.EXPORT_GIT),
        (LifecycleBoundary.PROCESS_INSPECTION, OperationKind.INSPECT_PROCESSES),
        (LifecycleBoundary.STOP, OperationKind.STOP),
        (LifecycleBoundary.DESTROY, OperationKind.DESTROY),
        (LifecycleBoundary.POST_DESTROY_RECONCILIATION, OperationKind.RECONCILE),
    )
    for boundary, kind in provider_boundaries:
        provider = FakeSandboxProvider(interrupt_before=boundary)
        if kind is OperationKind.CREATE:
            fact = provider.create(run, key(run, kind, f"before-{boundary.value}"))
            check(fact.observation is Observation.COULD_NOT_OBSERVE, f"interrupt before {boundary.value}: did not return CNO", errors)
            continue
        identity = create(provider, run)
        if kind is OperationKind.COPY_IN:
            fact = provider.copy_in(identity, CopySpec(key(run, kind, f"before-{boundary.value}"), "source-broker/fixture", "source-broker", "/workspace/source", 1024))
        elif kind is OperationKind.EXEC:
            fact = provider.exec(identity, command(run, "setup" if boundary is LifecycleBoundary.SETUP else "exec"), key(run, kind, f"before-{boundary.value}"))
        elif kind is OperationKind.COLLECT_ARTIFACTS:
            fact = provider.collect_artifacts(identity, make_artifact(run))
        elif kind is OperationKind.EXPORT_GIT:
            fact = provider.export_git(identity, make_git(run))
        elif kind is OperationKind.INSPECT_PROCESSES:
            fact = provider.inspect_processes(identity, key(run, kind, f"before-{boundary.value}"))
        elif kind is OperationKind.STOP:
            fact = provider.stop(identity, key(run, kind, f"before-{boundary.value}"))
        elif kind is OperationKind.DESTROY:
            # Authorization is intentionally absent here: interruption is
            # observed before an irreversible call and authorization remains a
            # separate SSSF gate.
            fact = provider.destroy(identity, key(run, kind, f"before-{boundary.value}"), None)
        else:
            fact = provider.reconcile(identity, key(run, kind, f"before-{boundary.value}"))
        check(fact.observation is Observation.COULD_NOT_OBSERVE or (kind is OperationKind.DESTROY and fact.observation is Observation.OBSERVED_BAD), f"interrupt before {boundary.value}: unexpected result {fact.observation}", errors)

    after_create = FakeSandboxProvider(interrupt_after=LifecycleBoundary.CREATE)
    after_create_fact = after_create.create(run, key(run, OperationKind.CREATE, "after-create"))
    check(after_create_fact.observation is Observation.COULD_NOT_OBSERVE and after_create_fact.provider_resource_id is not None, "interrupt after create: resource identity was not retained", errors)

    after_destroy = FakeSandboxProvider(interrupt_after=LifecycleBoundary.DESTROY)
    after_identity = create(after_destroy, run)
    after_artifact = after_destroy.collect_artifacts(after_identity, make_artifact(run))
    after_git = after_destroy.export_git(after_identity, make_git(run))
    after_destroy_key = key(run, OperationKind.DESTROY, "after-destroy")
    after_auth = issue_destroy_authorization(run, after_identity, after_destroy_key, artifact=after_artifact, git=after_git, artifact_spec=make_artifact(run), git_spec=make_git(run))
    after_destroy_fact = after_destroy.destroy(after_identity, after_destroy_key, after_auth)
    after_reconcile = after_destroy.reconcile(after_identity, key(run, OperationKind.RECONCILE, "after-destroy-reconcile"))
    check(after_destroy_fact.observation is Observation.COULD_NOT_OBSERVE and after_destroy_fact.acknowledged, "interrupt after destroy: acknowledgement/CNO was not retained", errors)
    check(after_reconcile.status.value == "absent" and after_reconcile.observation is Observation.OBSERVED_GOOD, "interrupt after destroy: later reconciliation did not recover authoritative absence", errors)

    secret = OutcomeCheck("secret-retirement", Observation.COULD_NOT_OBSERVE, reason="interrupted during secret retirement")
    result = fold_aggregate(evidence=(secret,))
    check(result.status is Observation.COULD_NOT_OBSERVE, "secret retirement interruption was narrowed to success", errors)


def durable_record_controls(errors: list[str]) -> None:
    run = spec()
    identity = SandboxIdentity.requested(run).with_resource("fake-sandbox-sbx-fixture-run")
    operation = key(run, OperationKind.CREATE, "record")
    record = LifecycleOperationRecord(
        record_id="record-1",
        operation=operation,
        requested_identity=SandboxIdentity.requested(run),
        source_identity=run.source_identity,
        attempt_id=operation.attempt_id,
        prior_state=LifecycleState.REQUESTED,
        observed_state=LifecycleState.UNKNOWN,
        observation=Observation.COULD_NOT_OBSERVE,
        requested_at="1970-01-01T00:00:00Z",
        observed_at="1970-01-01T00:00:01Z",
        observation_reason="create response ambiguous",
        provider_resource_id=identity.provider_resource_id,
    )
    store = InMemoryLifecycleRecordStore()
    store.append(record)
    check(store.latest(run.run_id, operation.operation_id) == record, "durable record store did not preserve CNO record", errors)
    check(store.latest(run.run_id, operation.operation_id).observed_state is LifecycleState.UNKNOWN, "durable record converted CNO to scalar absence", errors)
    other_operation = key(run, OperationKind.INSPECT, "other-record-stream")
    other_record = replace(
        record,
        record_id="record-2",
        operation=other_operation,
        attempt_id=other_operation.attempt_id,
    )
    store.append(other_record)
    check(other_record.version == 0 and store.latest(run.run_id, other_operation.operation_id) == other_record, "durable record version leaked across operation streams", errors)


def run_controls() -> list[str]:
    errors: list[str] = []
    success_control(errors)
    ambiguity_and_identity_controls(errors)
    exec_controls(errors)
    artifact_and_git_controls(errors)
    cleanup_and_authority_controls(errors)
    aggregate_controls(errors)
    interruption_controls(errors)
    durable_record_controls(errors)
    return errors


def main() -> int:
    errors = run_controls()
    if errors:
        print("SBX-1 SandboxProvider contract/fake controls: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("SBX-1 SandboxProvider contract/fake controls: PASS")
    print("provider-calls: 0 (in-process fake; no Docker/exe.dev/network/provider side effect)")
    print("positive success: typed source/exec/artifact/Git/quiescence/destroy/reconcile facts")
    print("watched-red: ambiguity, identity, timeout/cancel/overflow, cleanup CNO, workload leak")
    print("watched-red: artifact missing/tamper/overflow, Git ancestry, stop, authorization, residue")
    print("watched-red: unreachable inspection, duplicates, idempotent absence, interruptions, aggregate precedence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
