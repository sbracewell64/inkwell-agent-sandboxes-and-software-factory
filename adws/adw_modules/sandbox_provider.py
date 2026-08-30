"""Provider-neutral sandbox contract owned by SSSF.

This module is the SBX-1 semantic seam.  It deliberately contains no Docker,
SSH, network, credential, or model client.  A provider reports bounded facts;
SSSF code owns ordering, budgets, retry/recovery choices, acceptance, promotion,
and the one-use authorization required for destruction.

``AgentBackend`` is intentionally not defined here.  Agent execution remains a
separate contract.  Typed guest commands are projected onto the existing SSSF
subprocess supervisor rather than creating another process owner.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import threading
import time
from typing import Iterable, Iterator, Mapping, MutableMapping, Protocol, Sequence

from .subprocess_supervisor import Observation, SupervisorRequest
from tools.ci_gate import CNO_REASON_PREFIX, COULD_NOT_OBSERVE_EXIT
from tools.evidence_manifest import (
    Observation as EvidenceManifestObservation,
    ValidationContext as EvidenceManifestContext,
    validate_manifest as validate_evidence_manifest,
)


# ---------------------------------------------------------------------------
# Closed identities and small value types

_IDENTITY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+\-]{0,255}$")
_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _token(value: str, label: str) -> None:
    if not isinstance(value, str) or _IDENTITY.fullmatch(value) is None:
        raise ValueError(f"{label} must be a bounded identity token")


def _sha(value: str, label: str) -> None:
    if not isinstance(value, str) or _SHA1.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase 40-character Git SHA")


def _digest(value: str, label: str) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")


def _nonempty(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError(f"{label} must be a nonempty NUL-free string")


def _tokens(values: Iterable[str], label: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    result = tuple(values)
    if not allow_empty and not result:
        raise ValueError(f"{label} must be nonempty")
    if len(set(result)) != len(result):
        raise ValueError(f"{label} must be duplicate-free")
    for value in result:
        _token(value, f"{label} item")
    return result


def _sorted_tokens(values: Iterable[str], label: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    result = _tokens(values, label, allow_empty=allow_empty)
    if result != tuple(sorted(result)):
        raise ValueError(f"{label} must be sorted")
    return result


def _absolute_guest_path(value: str, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value.startswith("/")
        or "\x00" in value
        or "\\" in value
        or any(part in {"", ".", ".."} for part in PurePosixPath(value).parts[1:])
    ):
        raise ValueError(f"{label} must be an absolute normalized guest path")


def _relative_path(value: str, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or "\x00" in value
        or "\\" in value
    ):
        raise ValueError(f"{label} must be a relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix() or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise ValueError(f"{label} must not escape its artifact root")


def _timestamp(value: str, label: str) -> None:
    _nonempty(value, label)


class WorkspaceMode(str, Enum):
    BROKER_CLONE = "broker-clone"
    EXPLICIT_COPY = "explicit-copy"
    READ_ONLY_OVERLAY = "read-only-overlay"


@dataclass(frozen=True, slots=True)
class ResourceBounds:
    """Finite provider resource ceilings; zero is never an implicit unlimited value."""

    cpu_millis: int = 1_000
    memory_bytes: int = 512 * 1024 * 1024
    pids: int = 128
    disk_bytes: int = 4 * 1024 * 1024 * 1024
    network_bytes: int = 0
    wall_seconds: float = 900.0

    def __post_init__(self) -> None:
        for name in ("cpu_millis", "memory_bytes", "pids", "disk_bytes"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"resource bound {name} must be a positive integer")
        if not isinstance(self.network_bytes, int) or isinstance(self.network_bytes, bool) or self.network_bytes < 0:
            raise ValueError("resource bound network_bytes must be a nonnegative integer")
        if not isinstance(self.wall_seconds, (int, float)) or isinstance(self.wall_seconds, bool) or self.wall_seconds <= 0:
            raise ValueError("resource bound wall_seconds must be positive")


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    repository: str
    commit: str
    tree: str

    def __post_init__(self) -> None:
        if not isinstance(self.repository, str) or not self.repository.startswith("https://"):
            raise ValueError("source repository must be an HTTPS URL")
        _nonempty(self.repository, "source repository")
        _sha(self.commit, "source commit")
        _sha(self.tree, "source tree")


@dataclass(frozen=True, slots=True)
class SandboxSpec:
    """Immutable requested identity and policy for one sandbox world."""

    run_id: str
    operation_id: str
    source_repo: str
    source_commit: str
    source_tree: str
    profile_id: str
    template_id: str
    toolchain_id: str
    workspace_mode: WorkspaceMode
    resource_bounds: ResourceBounds
    filesystem_policy_id: str
    network_policy_id: str
    effect_policy_id: str
    exposure_policy_id: str
    secret_refs: tuple[str, ...]
    cognition_policy_id: str
    evidence_root: str
    instruction_policy_id: str = "instruction-policy/v1"
    schema_version: str = "sandbox-spec/v1"

    def __post_init__(self) -> None:
        for name in (
            "run_id",
            "operation_id",
            "profile_id",
            "template_id",
            "toolchain_id",
            "filesystem_policy_id",
            "network_policy_id",
            "effect_policy_id",
            "exposure_policy_id",
            "cognition_policy_id",
            "instruction_policy_id",
        ):
            _token(getattr(self, name), name)
        if self.schema_version != "sandbox-spec/v1":
            raise ValueError("unsupported SandboxSpec schema version")
        if not isinstance(self.workspace_mode, WorkspaceMode):
            raise ValueError("workspace_mode must be a WorkspaceMode")
        SourceIdentity(self.source_repo, self.source_commit, self.source_tree)
        object.__setattr__(self, "secret_refs", tuple(self.secret_refs))
        _tokens(self.secret_refs, "secret_refs")
        if not isinstance(self.evidence_root, str) or not self.evidence_root.startswith("/") or "\x00" in self.evidence_root:
            raise ValueError("evidence_root must be an absolute path identity")
        if ".." in PurePosixPath(self.evidence_root).parts:
            raise ValueError("evidence_root must not contain parent traversal")

    @property
    def source_identity(self) -> SourceIdentity:
        return SourceIdentity(self.source_repo, self.source_commit, self.source_tree)

    @property
    def identity_digest(self) -> str:
        """Content identity; secret values cannot enter because only refs exist."""
        document = {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "operation_id": self.operation_id,
            "source": asdict(self.source_identity),
            "profile_id": self.profile_id,
            "template_id": self.template_id,
            "toolchain_id": self.toolchain_id,
            "workspace_mode": self.workspace_mode.value,
            "resource_bounds": asdict(self.resource_bounds),
            "filesystem_policy_id": self.filesystem_policy_id,
            "network_policy_id": self.network_policy_id,
            "effect_policy_id": self.effect_policy_id,
            "exposure_policy_id": self.exposure_policy_id,
            "secret_refs": list(self.secret_refs),
            "cognition_policy_id": self.cognition_policy_id,
            "instruction_policy_id": self.instruction_policy_id,
            "evidence_root": self.evidence_root,
        }
        raw = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class SandboxIdentity:
    run_id: str
    spec_digest: str
    provider_resource_id: str | None = None

    def __post_init__(self) -> None:
        _token(self.run_id, "sandbox identity run_id")
        _digest(self.spec_digest, "sandbox identity spec_digest")
        if self.provider_resource_id is not None:
            _token(self.provider_resource_id, "provider resource identity")

    @classmethod
    def requested(cls, spec: SandboxSpec) -> "SandboxIdentity":
        return cls(spec.run_id, spec.identity_digest)

    def with_resource(self, provider_resource_id: str) -> "SandboxIdentity":
        return SandboxIdentity(self.run_id, self.spec_digest, provider_resource_id)


class OperationKind(str, Enum):
    CREATE = "create"
    INSPECT = "inspect"
    COPY_IN = "copy-in"
    EXEC = "exec"
    COLLECT_ARTIFACTS = "collect-artifacts"
    EXPORT_GIT = "export-git"
    INSPECT_PROCESSES = "inspect-processes"
    WAIT_QUIESCENT = "wait-quiescent"
    STOP = "stop"
    DESTROY = "destroy"
    RECONCILE = "reconcile"


@dataclass(frozen=True, slots=True)
class OperationKey:
    """The SSSF-owned idempotency key for one operation attempt."""

    run_id: str
    operation_id: str
    attempt_id: str
    idempotency_key: str
    kind: OperationKind = OperationKind.INSPECT

    def __post_init__(self) -> None:
        for name in ("run_id", "operation_id", "attempt_id", "idempotency_key"):
            _token(getattr(self, name), name)
        if not isinstance(self.kind, OperationKind):
            raise ValueError("operation kind must be an OperationKind")

    @classmethod
    def for_spec(cls, spec: SandboxSpec, kind: OperationKind, *, attempt_id: str = "attempt-1") -> "OperationKey":
        _token(attempt_id, "attempt_id")
        return cls(
            run_id=spec.run_id,
            operation_id=spec.operation_id,
            attempt_id=attempt_id,
            idempotency_key=f"{spec.run_id}:{spec.operation_id}:{kind.value}",
            kind=kind,
        )


class StdinPolicy(str, Enum):
    CLOSED = "closed"
    EMPTY = "empty"
    REFERENCED = "referenced"


class TimeoutClock(str, Enum):
    MONOTONIC = "monotonic"


@dataclass(frozen=True, slots=True)
class CommandSpec:
    """Typed command authority projected onto ``subprocess_supervisor``."""

    argv: tuple[str, ...]
    guest_cwd: str
    environment_refs: tuple[str, ...]
    environment_allowlist: frozenset[str]
    stdin_policy: StdinPolicy
    timeout_seconds: float
    max_stdout_bytes: int
    max_stderr_bytes: int
    execution_id: str
    attempt_id: str
    cancellation_id: str
    expected_exit_codes: tuple[int, ...] = (0,)
    terminal_parser_id: str | None = None
    stdin_ref: str | None = None
    timeout_clock: TimeoutClock = TimeoutClock.MONOTONIC
    stdout_retention: str = "bounded-digest"
    stderr_retention: str = "bounded-digest"

    def __post_init__(self) -> None:
        if not self.argv or any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in self.argv):
            raise ValueError("CommandSpec argv must be a nonempty NUL-free array")
        _absolute_guest_path(self.guest_cwd, "guest_cwd")
        object.__setattr__(self, "argv", tuple(self.argv))
        object.__setattr__(self, "environment_refs", tuple(self.environment_refs))
        object.__setattr__(self, "environment_allowlist", frozenset(self.environment_allowlist))
        object.__setattr__(self, "expected_exit_codes", tuple(self.expected_exit_codes))
        refs = _tokens(self.environment_refs, "environment_refs")
        allowlist = frozenset(self.environment_allowlist)
        if any(not isinstance(name, str) or _ENV_NAME.fullmatch(name) is None for name in allowlist):
            raise ValueError("environment_allowlist contains an invalid environment name")
        if not set(refs).issubset(allowlist):
            raise ValueError("environment_refs must be a subset of environment_allowlist")
        if not isinstance(self.stdin_policy, StdinPolicy):
            raise ValueError("stdin_policy must be a StdinPolicy")
        if self.stdin_policy is StdinPolicy.REFERENCED:
            _token(self.stdin_ref or "", "stdin_ref")
        elif self.stdin_ref is not None:
            raise ValueError("stdin_ref is only valid with referenced stdin policy")
        if not isinstance(self.timeout_seconds, (int, float)) or isinstance(self.timeout_seconds, bool) or self.timeout_seconds <= 0:
            raise ValueError("CommandSpec timeout must be a positive monotonic duration")
        for name in ("max_stdout_bytes", "max_stderr_bytes"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{name} must be a positive bound")
        if not self.expected_exit_codes and not self.terminal_parser_id:
            raise ValueError("CommandSpec needs expected exits or a terminal parser identity")
        if self.expected_exit_codes and any(not isinstance(code, int) or isinstance(code, bool) for code in self.expected_exit_codes):
            raise ValueError("expected exit codes must be integers")
        if len(set(self.expected_exit_codes)) != len(self.expected_exit_codes):
            raise ValueError("expected exit codes must be duplicate-free")
        if self.terminal_parser_id is not None:
            _token(self.terminal_parser_id, "terminal_parser_id")
        for name in ("execution_id", "attempt_id", "cancellation_id"):
            _token(getattr(self, name), name)
        if self.timeout_clock is not TimeoutClock.MONOTONIC:
            raise ValueError("only monotonic command timeouts are supported")
        for name in ("stdout_retention", "stderr_retention"):
            _token(getattr(self, name), name)

    @property
    def supervisor_projection(self) -> Mapping[str, object]:
        """The exact fields handed to the existing SSSF process owner."""
        return {
            "argv": self.argv,
            "cwd": self.guest_cwd,
            "environment_allowlist": self.environment_allowlist,
            "timeout_seconds": self.timeout_seconds,
            "max_stdout_bytes": self.max_stdout_bytes,
            "max_stderr_bytes": self.max_stderr_bytes,
            "stdin_closed": self.stdin_policy in {StdinPolicy.CLOSED, StdinPolicy.EMPTY},
            "execution_id": self.execution_id,
            "attempt_id": self.attempt_id,
            "cancellation_id": self.cancellation_id,
        }

    def to_supervisor_request(
        self,
        environment: Mapping[str, str],
        *,
        term_grace_seconds: float = 1.0,
        verification_grace_seconds: float = 1.0,
    ) -> SupervisorRequest:
        """Project this command onto the one existing SSSF process owner.

        Values are supplied at launch by the caller and are never part of the
        immutable command/spec identity. The supervisor still receives the
        complete explicit allowlist and closes stdin; a referenced stdin mode
        needs a separately qualified transport and is refused here.
        """
        if self.stdin_policy is StdinPolicy.REFERENCED:
            raise ValueError("referenced stdin has no accepted subprocess-supervisor projection")
        supplied = dict(environment)
        if not set(supplied).issubset(self.environment_allowlist):
            unknown = sorted(set(supplied) - self.environment_allowlist)
            raise ValueError(f"environment contains names outside CommandSpec allowlist: {unknown}")
        return SupervisorRequest(
            argv=self.argv,
            cwd=self.guest_cwd,
            environment=supplied,
            environment_allowlist=self.environment_allowlist,
            timeout_seconds=self.timeout_seconds,
            term_grace_seconds=term_grace_seconds,
            verification_grace_seconds=verification_grace_seconds,
            max_stdout_bytes=self.max_stdout_bytes,
            max_stderr_bytes=self.max_stderr_bytes,
        )


@dataclass(frozen=True, slots=True)
class CopySpec:
    """Only an explicit Source Broker or input reference may cross the seam."""

    operation: OperationKey
    source_ref: str
    source_kind: str
    guest_path: str
    max_bytes: int
    expected_sha256: str | None = None

    def __post_init__(self) -> None:
        if self.operation.kind is not OperationKind.COPY_IN:
            raise ValueError("copy operation must use COPY_IN kind")
        _token(self.source_ref, "source_ref")
        if self.source_kind not in {"source-broker", "explicit-input"}:
            raise ValueError("source_kind must be source-broker or explicit-input")
        _absolute_guest_path(self.guest_path, "guest_path")
        if not isinstance(self.max_bytes, int) or isinstance(self.max_bytes, bool) or self.max_bytes < 1:
            raise ValueError("copy max_bytes must be positive")
        if self.expected_sha256 is not None:
            _digest(self.expected_sha256, "expected_sha256")


InputCopySpec = CopySpec
SourceCopySpec = CopySpec


@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    operation: OperationKey
    artifact_id: str
    applicable: bool
    required: bool
    paths: tuple[str, ...]
    max_files: int
    max_total_bytes: int
    max_file_bytes: int
    producer_id: str
    purpose: str
    manifest_path: Path
    artifact_root: Path
    manifest_context: EvidenceManifestContext

    def __post_init__(self) -> None:
        if self.operation.kind is not OperationKind.COLLECT_ARTIFACTS:
            raise ValueError("artifact operation must use COLLECT_ARTIFACTS kind")
        _token(self.artifact_id, "artifact_id")
        object.__setattr__(self, "paths", tuple(self.paths))
        _sorted_tokens(self.paths, "artifact paths")
        for path in self.paths:
            _relative_path(path, "artifact path")
        if self.applicable and self.required and not self.paths:
            raise ValueError("an applicable required artifact must declare exact paths")
        for name in ("max_files", "max_total_bytes", "max_file_bytes"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{name} must be a positive bound")
        if len(self.paths) > self.max_files:
            raise ValueError("artifact max_files is below the exact path inventory")
        _token(self.producer_id, "producer_id")
        _token(self.purpose, "purpose")
        if not isinstance(self.manifest_path, Path) or not isinstance(self.artifact_root, Path):
            raise ValueError("artifact manifest and root must be paths")
        if not isinstance(self.manifest_context, EvidenceManifestContext):
            raise ValueError("artifact manifest context must use the canonical evidence owner")


@dataclass(frozen=True, slots=True)
class ArtifactInventoryItem:
    path: str
    artifact_type: str
    byte_length: int
    sha256: str
    producer_id: str
    run_id: str
    operation_id: str
    attempt_id: str

    def __post_init__(self) -> None:
        _relative_path(self.path, "artifact inventory path")
        _token(self.artifact_type, "artifact_type")
        if not isinstance(self.byte_length, int) or isinstance(self.byte_length, bool) or self.byte_length < 1:
            raise ValueError("artifact byte_length must be positive")
        _digest(self.sha256, "artifact sha256")
        for name in ("producer_id", "run_id", "operation_id", "attempt_id"):
            _token(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class GitExportSpec:
    operation: OperationKey
    applicable: bool
    required: bool
    source: SourceIdentity
    expected_base_commit: str
    expected_base_tree: str
    expected_tip_commit: str | None
    expected_tip_tree: str | None
    max_bundle_bytes: int
    export_ref: str

    def __post_init__(self) -> None:
        if self.operation.kind is not OperationKind.EXPORT_GIT:
            raise ValueError("Git operation must use EXPORT_GIT kind")
        if not isinstance(self.source, SourceIdentity):
            raise ValueError("Git export source must be SourceIdentity")
        _sha(self.expected_base_commit, "expected_base_commit")
        _sha(self.expected_base_tree, "expected_base_tree")
        if self.expected_tip_commit is not None:
            _sha(self.expected_tip_commit, "expected_tip_commit")
        if self.expected_tip_tree is not None:
            _sha(self.expected_tip_tree, "expected_tip_tree")
        if (self.expected_tip_commit is None) != (self.expected_tip_tree is None):
            raise ValueError("expected tip commit and tree must be supplied together")
        if not isinstance(self.max_bundle_bytes, int) or isinstance(self.max_bundle_bytes, bool) or self.max_bundle_bytes < 1:
            raise ValueError("max_bundle_bytes must be positive")
        _token(self.export_ref, "export_ref")


class PromotionAuthority(str, Enum):
    NONE = "none"


class CapabilityDisposition(str, Enum):
    AVAILABLE = "available"
    DEFERRED = "deferred-to-sbx-2"
    REFUSED = "refused"


@dataclass(frozen=True, slots=True)
class CapabilityFact:
    """Typed mechanism decision; SBX-1 never guesses a Docker binding."""

    capability_id: str
    disposition: CapabilityDisposition
    observation: Observation
    reason: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _token(self.capability_id, "capability_id")
        if not isinstance(self.disposition, CapabilityDisposition):
            raise ValueError("capability disposition must be closed")
        if not isinstance(self.observation, Observation):
            raise ValueError("capability observation must be closed")
        _nonempty(self.reason, "capability reason")
        _tokens(self.evidence_refs, "capability evidence_refs")
        if self.disposition is CapabilityDisposition.AVAILABLE and self.observation is not Observation.OBSERVED_GOOD:
            raise ValueError("available capability must be observed-good")
        if self.disposition is not CapabilityDisposition.AVAILABLE and self.observation is Observation.OBSERVED_GOOD:
            raise ValueError("deferred/refused capability cannot be observed-good")


DeferredCapability = CapabilityFact


# ---------------------------------------------------------------------------
# Provider facts.  Every fact carries an explicit three-valued observation.


class LifecycleState(str, Enum):
    REQUESTED = "requested"
    CREATING = "creating"
    PRESENT = "present"
    SOURCE_STAGED = "source-staged"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    EXPORTING = "exporting"
    QUIESCENT = "quiescent"
    DESTROYING = "destroying"
    ABSENT = "absent"
    DUPLICATE = "duplicate"
    RESIDUAL = "residual"
    UNKNOWN = "unknown"


class QuiescenceDomain(str, Enum):
    HOST_PROVIDER_CLIENT = "host-provider-client"
    SANDBOX_WORKLOAD = "sandbox-workload"
    SANDBOX_RESOURCES = "sandbox-resources"


@dataclass(frozen=True, slots=True)
class QuiescenceFact:
    domain: QuiescenceDomain
    observation: Observation
    quiescent: bool | None
    reason: str
    identities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.domain, QuiescenceDomain):
            raise ValueError("quiescence domain must be closed")
        if self.quiescent is not None and not isinstance(self.quiescent, bool):
            raise ValueError("quiescent must be true, false, or unknown")
        _nonempty(self.reason, "quiescence reason")
        _tokens(self.identities, "quiescence identities")
        if self.observation is Observation.OBSERVED_GOOD and self.quiescent is not True:
            raise ValueError("observed-good quiescence must positively observe quiescent=true")
        if self.observation is Observation.OBSERVED_BAD and self.quiescent is not False:
            raise ValueError("observed-bad quiescence must positively observe quiescent=false")


@dataclass(frozen=True, slots=True)
class FactBase:
    operation: OperationKey
    observation: Observation
    reason: str
    observed_at: str
    prior_state: LifecycleState = LifecycleState.UNKNOWN
    observed_state: LifecycleState = LifecycleState.UNKNOWN
    provider_resource_id: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.observation, Observation):
            raise ValueError("provider facts require a closed Observation")
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))
        _nonempty(self.reason, "observation reason")
        _timestamp(self.observed_at, "observed_at")
        if not isinstance(self.prior_state, LifecycleState) or not isinstance(self.observed_state, LifecycleState):
            raise ValueError("lifecycle states must be closed LifecycleState values")
        if self.observation is Observation.COULD_NOT_OBSERVE and self.observed_state is LifecycleState.ABSENT:
            raise ValueError("could-not-observe cannot silently assert ABSENT")
        if self.provider_resource_id is not None:
            _token(self.provider_resource_id, "provider_resource_id")
        _tokens(self.evidence_refs, "evidence_refs")


@dataclass(frozen=True, slots=True)
class CreateFacts(FactBase):
    spec_digest: str = ""
    resource_identity_observation: Observation = Observation.COULD_NOT_OBSERVE
    duplicate_resource_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        FactBase.__post_init__(self)
        _digest(self.spec_digest, "create spec_digest")
        if not isinstance(self.resource_identity_observation, Observation):
            raise ValueError("resource identity observation must be closed")
        object.__setattr__(self, "duplicate_resource_ids", tuple(self.duplicate_resource_ids))
        _tokens(self.duplicate_resource_ids, "duplicate_resource_ids")


@dataclass(frozen=True, slots=True)
class InspectFacts(FactBase):
    identity_observation: Observation = Observation.COULD_NOT_OBSERVE

    def __post_init__(self) -> None:
        FactBase.__post_init__(self)
        if not isinstance(self.identity_observation, Observation):
            raise ValueError("identity observation must be closed")


@dataclass(frozen=True, slots=True)
class CopyFacts(FactBase):
    source_observation: Observation = Observation.COULD_NOT_OBSERVE
    source_digest: str | None = None
    guest_path: str = "/"

    def __post_init__(self) -> None:
        FactBase.__post_init__(self)
        if not isinstance(self.source_observation, Observation):
            raise ValueError("source observation must be closed")
        if self.source_digest is not None:
            _digest(self.source_digest, "source_digest")
        _absolute_guest_path(self.guest_path, "guest_path")


@dataclass(frozen=True, slots=True)
class ExecFacts(FactBase):
    return_code: int | None = None
    stdout: bytes = b""
    stderr: bytes = b""
    stdout_bytes_seen: int = 0
    stderr_bytes_seen: int = 0
    stdout_sha256: str = hashlib.sha256(b"").hexdigest()
    stderr_sha256: str = hashlib.sha256(b"").hexdigest()
    output_overflowed: bool = False
    client_process: QuiescenceFact = field(
        default_factory=lambda: QuiescenceFact(
            QuiescenceDomain.HOST_PROVIDER_CLIENT,
            Observation.COULD_NOT_OBSERVE,
            None,
            "provider client cleanup was not observed",
        )
    )
    workload: QuiescenceFact = field(
        default_factory=lambda: QuiescenceFact(
            QuiescenceDomain.SANDBOX_WORKLOAD,
            Observation.COULD_NOT_OBSERVE,
            None,
            "sandbox workload quiescence was not observed",
        )
    )
    resources: QuiescenceFact = field(
        default_factory=lambda: QuiescenceFact(
            QuiescenceDomain.SANDBOX_RESOURCES,
            Observation.COULD_NOT_OBSERVE,
            None,
            "sandbox resource quiescence was not observed",
        )
    )
    timed_out: bool = False
    cancelled: bool = False

    def __post_init__(self) -> None:
        FactBase.__post_init__(self)
        for name in ("stdout_bytes_seen", "stderr_bytes_seen"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be nonnegative")
        _digest(self.stdout_sha256, "stdout_sha256")
        _digest(self.stderr_sha256, "stderr_sha256")
        if not isinstance(self.stdout, bytes) or not isinstance(self.stderr, bytes):
            raise ValueError("stdout and stderr facts must be bytes")
        if self.stdout_bytes_seen < len(self.stdout) or self.stderr_bytes_seen < len(self.stderr):
            raise ValueError("stream byte counts cannot be below retained bytes")
        if not isinstance(self.client_process, QuiescenceFact) or self.client_process.domain is not QuiescenceDomain.HOST_PROVIDER_CLIENT:
            raise ValueError("exec must carry host/provider-client custody facts")
        if not isinstance(self.workload, QuiescenceFact) or self.workload.domain is not QuiescenceDomain.SANDBOX_WORKLOAD:
            raise ValueError("exec must carry sandbox workload facts")
        if not isinstance(self.resources, QuiescenceFact) or self.resources.domain is not QuiescenceDomain.SANDBOX_RESOURCES:
            raise ValueError("exec must carry sandbox resource facts")


@dataclass(frozen=True, slots=True)
class ArtifactExportFacts(FactBase):
    artifact_id: str = ""
    applicable: bool = True
    complete: bool = False
    inventory: tuple[ArtifactInventoryItem, ...] = ()
    total_bytes: int = 0
    missing_paths: tuple[str, ...] = ()
    tampered_paths: tuple[str, ...] = ()
    overflowed: bool = False

    def __post_init__(self) -> None:
        FactBase.__post_init__(self)
        _token(self.artifact_id, "artifact_id")
        if not isinstance(self.applicable, bool) or not isinstance(self.complete, bool):
            raise ValueError("artifact applicability/completeness must be boolean")
        object.__setattr__(self, "inventory", tuple(self.inventory))
        object.__setattr__(self, "missing_paths", tuple(self.missing_paths))
        object.__setattr__(self, "tampered_paths", tuple(self.tampered_paths))
        if self.inventory != tuple(sorted(self.inventory, key=lambda item: item.path)):
            raise ValueError("artifact inventory must be path-sorted")
        if len({item.path for item in self.inventory}) != len(self.inventory):
            raise ValueError("artifact inventory paths must be unique")
        if not isinstance(self.total_bytes, int) or isinstance(self.total_bytes, bool) or self.total_bytes < 0:
            raise ValueError("artifact total_bytes must be nonnegative")
        _tokens(self.missing_paths, "missing_paths")
        for path in self.missing_paths:
            _relative_path(path, "missing artifact path")
        _tokens(self.tampered_paths, "tampered_paths")
        for path in self.tampered_paths:
            _relative_path(path, "tampered artifact path")


@dataclass(frozen=True, slots=True)
class GitExportFacts(FactBase):
    applicable: bool = True
    complete: bool = False
    source: SourceIdentity | None = None
    base_commit: str | None = None
    base_tree: str | None = None
    tip_commit: str | None = None
    tip_tree: str | None = None
    ancestry_verified: bool | None = None
    export_ref: str = ""
    bundle_sha256: str = hashlib.sha256(b"").hexdigest()
    bundle_bytes: int = 0
    promotion_authority: PromotionAuthority = PromotionAuthority.NONE

    def __post_init__(self) -> None:
        FactBase.__post_init__(self)
        if not isinstance(self.applicable, bool) or not isinstance(self.complete, bool):
            raise ValueError("Git applicability/completeness must be boolean")
        if self.source is not None and not isinstance(self.source, SourceIdentity):
            raise ValueError("Git facts source must be SourceIdentity")
        for name in ("base_commit", "base_tree", "tip_commit", "tip_tree"):
            value = getattr(self, name)
            if value is not None:
                _sha(value, name)
        if self.ancestry_verified is not None and not isinstance(self.ancestry_verified, bool):
            raise ValueError("ancestry_verified must be true, false, or unknown")
        _token(self.export_ref, "export_ref")
        _digest(self.bundle_sha256, "bundle_sha256")
        if not isinstance(self.bundle_bytes, int) or isinstance(self.bundle_bytes, bool) or self.bundle_bytes < 0:
            raise ValueError("bundle_bytes must be nonnegative")
        if self.promotion_authority is not PromotionAuthority.NONE:
            raise ValueError("provider Git export cannot carry promotion authority")


@dataclass(frozen=True, slots=True)
class ProcessFacts(FactBase):
    host_client: QuiescenceFact = field(
        default_factory=lambda: QuiescenceFact(
            QuiescenceDomain.HOST_PROVIDER_CLIENT,
            Observation.COULD_NOT_OBSERVE,
            None,
            "host/provider-client custody was not observed",
        )
    )
    workload: QuiescenceFact = field(
        default_factory=lambda: QuiescenceFact(
            QuiescenceDomain.SANDBOX_WORKLOAD,
            Observation.COULD_NOT_OBSERVE,
            None,
            "sandbox workload was not observed",
        )
    )
    resources: QuiescenceFact = field(
        default_factory=lambda: QuiescenceFact(
            QuiescenceDomain.SANDBOX_RESOURCES,
            Observation.COULD_NOT_OBSERVE,
            None,
            "sandbox resources were not observed",
        )
    )

    def __post_init__(self) -> None:
        FactBase.__post_init__(self)
        expected = (
            (self.host_client, QuiescenceDomain.HOST_PROVIDER_CLIENT),
            (self.workload, QuiescenceDomain.SANDBOX_WORKLOAD),
            (self.resources, QuiescenceDomain.SANDBOX_RESOURCES),
        )
        for fact, domain in expected:
            if not isinstance(fact, QuiescenceFact) or fact.domain is not domain:
                raise ValueError("process facts must preserve all three quiescence domains")


@dataclass(frozen=True, slots=True)
class StopFacts(FactBase):
    acknowledged: bool = False
    workload_stopped: bool | None = None

    def __post_init__(self) -> None:
        FactBase.__post_init__(self)
        if not isinstance(self.acknowledged, bool):
            raise ValueError("stop acknowledgement must be boolean")
        if self.workload_stopped is not None and not isinstance(self.workload_stopped, bool):
            raise ValueError("workload_stopped must be boolean or unknown")


@dataclass(frozen=True, slots=True)
class DestroyFacts(FactBase):
    acknowledged: bool = False
    already_absent: bool = False
    residual_resource_ids: tuple[str, ...] = ()
    authorization_id: str | None = None

    def __post_init__(self) -> None:
        FactBase.__post_init__(self)
        if not isinstance(self.acknowledged, bool) or not isinstance(self.already_absent, bool):
            raise ValueError("destroy acknowledgement flags must be boolean")
        object.__setattr__(self, "residual_resource_ids", tuple(self.residual_resource_ids))
        _tokens(self.residual_resource_ids, "residual_resource_ids")
        if self.authorization_id is not None:
            _token(self.authorization_id, "authorization_id")
        if self.observation is Observation.OBSERVED_GOOD and self.residual_resource_ids:
            raise ValueError("observed-good destroy cannot carry residual resources")
        if self.observation is Observation.COULD_NOT_OBSERVE and self.observed_state is LifecycleState.ABSENT:
            raise ValueError("destroy CNO cannot assert absence")


class ReconciliationStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    DUPLICATE = "duplicate"
    RESIDUAL = "residual"
    COULD_NOT_OBSERVE = "could-not-observe"


@dataclass(frozen=True, slots=True)
class ReconciliationFacts(FactBase):
    status: ReconciliationStatus = ReconciliationStatus.COULD_NOT_OBSERVE
    resource_ids: tuple[str, ...] = ()
    duplicate_resource_ids: tuple[str, ...] = ()
    residual_resource_ids: tuple[str, ...] = ()
    identity_observation: Observation = Observation.COULD_NOT_OBSERVE

    def __post_init__(self) -> None:
        FactBase.__post_init__(self)
        if not isinstance(self.status, ReconciliationStatus):
            raise ValueError("reconciliation status must be closed")
        if not isinstance(self.identity_observation, Observation):
            raise ValueError("reconciliation identity observation must be closed")
        _tokens(self.resource_ids, "resource_ids")
        _tokens(self.duplicate_resource_ids, "duplicate_resource_ids")
        _tokens(self.residual_resource_ids, "residual_resource_ids")
        object.__setattr__(self, "resource_ids", tuple(self.resource_ids))
        object.__setattr__(self, "duplicate_resource_ids", tuple(self.duplicate_resource_ids))
        object.__setattr__(self, "residual_resource_ids", tuple(self.residual_resource_ids))
        if self.status is ReconciliationStatus.ABSENT:
            if self.observation is not Observation.OBSERVED_GOOD or self.resource_ids:
                raise ValueError("ABSENT is only a positively observed empty result")
        if self.status is ReconciliationStatus.COULD_NOT_OBSERVE:
            if self.observation is not Observation.COULD_NOT_OBSERVE or self.observed_state is LifecycleState.ABSENT:
                raise ValueError("CNO reconciliation cannot assert absence")
        if self.status in {ReconciliationStatus.DUPLICATE, ReconciliationStatus.RESIDUAL} and self.observation is not Observation.OBSERVED_BAD:
            raise ValueError("duplicate/residual reconciliation is an observed contradiction")


def validate_artifact_export(
    spec: ArtifactSpec,
    facts: ArtifactExportFacts,
    *,
    provider_resource_id: str | None = None,
) -> "OutcomeCheck":
    """SSSF-side exact inventory/applicability check for one export fact."""
    if facts.artifact_id != spec.artifact_id:
        return OutcomeCheck("artifact-export", Observation.OBSERVED_BAD, reason="artifact obligation identity differs")
    if not spec.applicable:
        return OutcomeCheck("artifact-export", Observation.OBSERVED_GOOD, required=False, applicable=False, reason="artifact is not applicable")
    identity_ok = (
        facts.applicable == spec.applicable
        and facts.operation == spec.operation
        and (provider_resource_id is None or facts.provider_resource_id == provider_resource_id)
    )
    total_bytes_match = facts.total_bytes == sum(item.byte_length for item in facts.inventory)
    manifest_validation = validate_evidence_manifest(
        spec.manifest_path,
        spec.artifact_root,
        spec.manifest_context,
    )
    manifest_items = {item.path: item for item in manifest_validation.validated_inventory}
    manifest_inventory_match = len(manifest_items) == len(facts.inventory) and all(
        item.path in manifest_items
        and item.artifact_type == manifest_items[item.path].artifact_type
        and item.byte_length == manifest_items[item.path].byte_length
        and item.sha256 == manifest_items[item.path].sha256
        and item.producer_id == manifest_items[item.path].producer
        and item.run_id == manifest_items[item.path].run_id
        for item in facts.inventory
    )
    tampered = bool(facts.tampered_paths)
    complete = (
        facts.complete
        and not facts.missing_paths
        and not facts.overflowed
        and not tampered
        and total_bytes_match
        and manifest_inventory_match
    )
    paths = tuple(item.path for item in facts.inventory)
    exact_paths = paths == spec.paths
    bounded = (
        len(facts.inventory) <= spec.max_files
        and facts.total_bytes <= spec.max_total_bytes
        and all(item.byte_length <= spec.max_file_bytes for item in facts.inventory)
    )
    item_identity = all(
        item.producer_id == spec.producer_id
        and item.run_id == spec.operation.run_id
        and item.operation_id == spec.operation.operation_id
        and item.attempt_id == spec.operation.attempt_id
        for item in facts.inventory
    )
    if facts.observation is Observation.OBSERVED_BAD:
        return OutcomeCheck("artifact-export", Observation.OBSERVED_BAD, reason=facts.reason)
    if manifest_validation.observation is EvidenceManifestObservation.OBSERVED_BAD:
        return OutcomeCheck("artifact-export", Observation.OBSERVED_BAD, reason="; ".join(manifest_validation.issues))
    if facts.observation is Observation.COULD_NOT_OBSERVE:
        return OutcomeCheck("artifact-export", Observation.COULD_NOT_OBSERVE, reason=facts.reason)
    if manifest_validation.observation is EvidenceManifestObservation.CNO:
        return OutcomeCheck("artifact-export", Observation.COULD_NOT_OBSERVE, reason="; ".join(manifest_validation.issues))
    if tampered or not total_bytes_match or not manifest_inventory_match:
        return OutcomeCheck(
            "artifact-export",
            Observation.OBSERVED_BAD,
            reason="artifact facts contradict the canonical validated manifest or byte total",
        )
    return OutcomeCheck(
        "artifact-export",
        Observation.OBSERVED_GOOD,
        required=spec.required,
        identity_verified=identity_ok and item_identity,
        complete=complete and exact_paths and bounded,
        reason=("artifact inventory is exact and bounded" if complete and exact_paths and bounded else "artifact inventory is incomplete, unexpected, or over bound"),
    )


def validate_git_export(
    spec: GitExportSpec,
    facts: GitExportFacts,
    *,
    provider_resource_id: str | None = None,
) -> "OutcomeCheck":
    """SSSF-side source/base/tip/tree/ancestry and no-promotion check."""
    if not spec.applicable:
        return OutcomeCheck("git-export", Observation.OBSERVED_GOOD, required=spec.required, applicable=False, reason="Git export is not applicable")
    if facts.observation is Observation.OBSERVED_BAD:
        return OutcomeCheck("git-export", Observation.OBSERVED_BAD, reason=facts.reason)
    if facts.observation is Observation.COULD_NOT_OBSERVE:
        return OutcomeCheck("git-export", Observation.COULD_NOT_OBSERVE, reason=facts.reason)
    identity_ok = (
        facts.applicable == spec.applicable
        and facts.operation == spec.operation
        and (provider_resource_id is None or facts.provider_resource_id == provider_resource_id)
        and facts.source == spec.source
        and facts.export_ref == spec.export_ref
        and facts.base_commit == spec.expected_base_commit
        and facts.base_tree == spec.expected_base_tree
        and facts.promotion_authority is PromotionAuthority.NONE
    )
    tip_ok = (
        spec.expected_tip_commit is None
        or (facts.tip_commit == spec.expected_tip_commit and facts.tip_tree == spec.expected_tip_tree)
    )
    tip_obligation_declared = not spec.required or spec.expected_tip_commit is not None
    complete = (
        facts.complete
        and facts.ancestry_verified is True
        and 0 < facts.bundle_bytes <= spec.max_bundle_bytes
        and tip_ok
        and tip_obligation_declared
    )
    return OutcomeCheck(
        "git-export",
        Observation.OBSERVED_GOOD,
        required=spec.required,
        identity_verified=identity_ok,
        complete=complete,
        reason=("Git export identity and ancestry are verified" if identity_ok and complete else "Git export identity, ancestry, tip, or completeness is unverified"),
    )


# Friendly names for callers that do not want to know the concrete operation.
OperationFacts = FactBase
SandboxStateFacts = InspectFacts


# ---------------------------------------------------------------------------
# SSSF-owned durable record interface and aggregate fold


@dataclass(frozen=True, slots=True)
class DestroyAuthorization:
    """An opaque, one-use token minted by SSSF, never by a provider."""

    authorization_id: str
    run_id: str
    provider_resource_id: str
    sandbox_spec_digest: str
    operation_id: str
    idempotency_key: str
    source_identity: SourceIdentity
    obligations_digest: str
    issued_at: str
    authenticator: str
    scope: str = "destroy-only"

    def __post_init__(self) -> None:
        _token(self.authorization_id, "authorization_id")
        _token(self.run_id, "authorization run_id")
        _token(self.provider_resource_id, "authorization provider resource")
        _digest(self.sandbox_spec_digest, "authorization sandbox spec digest")
        _token(self.operation_id, "authorization operation_id")
        _token(self.idempotency_key, "authorization idempotency_key")
        if not isinstance(self.source_identity, SourceIdentity):
            raise ValueError("authorization source identity is required")
        _digest(self.obligations_digest, "obligations_digest")
        _timestamp(self.issued_at, "authorization issued_at")
        _digest(self.authenticator, "authorization authenticator")
        if self.scope != "destroy-only":
            raise ValueError("destroy authorization scope is closed")


def _destroy_authorization_payload(authorization: DestroyAuthorization) -> bytes:
    document = {
        "authorization_id": authorization.authorization_id,
        "run_id": authorization.run_id,
        "provider_resource_id": authorization.provider_resource_id,
        "sandbox_spec_digest": authorization.sandbox_spec_digest,
        "operation_id": authorization.operation_id,
        "idempotency_key": authorization.idempotency_key,
        "source_identity": asdict(authorization.source_identity),
        "obligations_digest": authorization.obligations_digest,
        "issued_at": authorization.issued_at,
        "scope": authorization.scope,
    }
    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode()


def _destroy_authorization_fingerprint(authorization: DestroyAuthorization) -> str:
    return hashlib.sha256(
        _destroy_authorization_payload(authorization) + b"|" + authorization.authenticator.encode()
    ).hexdigest()


class DestroyAuthorizationStateStore(Protocol):
    def record_issuance(self, authorization_id: str, fingerprint: str) -> None:
        ...

    def verifies(self, authorization_id: str, fingerprint: str) -> bool:
        ...

    def reserved(self, authorization_id: str) -> bool:
        ...

    def completed(self, authorization_id: str) -> bool:
        ...

    def compare_and_swap_reserved(self, authorization_id: str, fingerprint: str) -> bool:
        ...

    def compare_and_swap_completed(self, authorization_id: str, fingerprint: str) -> bool:
        ...


class InMemoryDestroyAuthorizationStateStore:
    """Deterministic test store for the durable atomic authorization state seam."""

    def __init__(self, state: MutableMapping[str, MutableMapping[str, object]] | None = None) -> None:
        self._state = state if state is not None else {}
        for authorization_id, item in self._state.items():
            _token(authorization_id, "persisted authorization_id")
            _digest(item.get("fingerprint"), "persisted authorization fingerprint")
            if item.get("status") not in {"issued", "reserved", "completed"}:
                raise ValueError("persisted authorization status must be issued, reserved, or completed")
        self._lock = threading.Lock()

    def record_issuance(self, authorization_id: str, fingerprint: str) -> None:
        _token(authorization_id, "authorization_id")
        _digest(fingerprint, "authorization fingerprint")
        with self._lock:
            existing = self._state.get(authorization_id)
            if existing is not None and existing["fingerprint"] != fingerprint:
                raise ValueError("authorization identity was reissued with different provenance")
            self._state.setdefault(authorization_id, {"fingerprint": fingerprint, "status": "issued"})

    def verifies(self, authorization_id: str, fingerprint: str) -> bool:
        with self._lock:
            item = self._state.get(authorization_id)
            return item is not None and hmac.compare_digest(str(item["fingerprint"]), fingerprint)

    def reserved(self, authorization_id: str) -> bool:
        with self._lock:
            item = self._state.get(authorization_id)
            return item is not None and item["status"] == "reserved"

    def completed(self, authorization_id: str) -> bool:
        with self._lock:
            item = self._state.get(authorization_id)
            return item is not None and item["status"] == "completed"

    def compare_and_swap_reserved(self, authorization_id: str, fingerprint: str) -> bool:
        with self._lock:
            item = self._state.get(authorization_id)
            if (
                item is None
                or item["status"] == "completed"
                or not hmac.compare_digest(str(item["fingerprint"]), fingerprint)
            ):
                return False
            item["status"] = "reserved"
            return True

    def compare_and_swap_completed(self, authorization_id: str, fingerprint: str) -> bool:
        with self._lock:
            item = self._state.get(authorization_id)
            if (
                item is None
                or item["status"] != "reserved"
                or not hmac.compare_digest(str(item["fingerprint"]), fingerprint)
            ):
                return False
            item["status"] = "completed"
            return True

    def snapshot(self) -> Mapping[str, Mapping[str, object]]:
        with self._lock:
            return {
                authorization_id: {
                    "fingerprint": item["fingerprint"],
                    "status": item["status"],
                }
                for authorization_id, item in self._state.items()
            }


class DestroyAuthorizationIssuer:
    """SSSF-only signing capability; never passed across the provider seam."""

    def __init__(self, signing_key: bytes, state_store: DestroyAuthorizationStateStore) -> None:
        if not isinstance(signing_key, bytes) or len(signing_key) < 32:
            raise ValueError("destroy authorization signing key must contain at least 32 bytes")
        self.__signing_key = signing_key
        self.__state_store = state_store

    def _mint(self, authorization: DestroyAuthorization) -> DestroyAuthorization:
        authenticator = hmac.new(
            self.__signing_key,
            _destroy_authorization_payload(authorization),
            hashlib.sha256,
        ).hexdigest()
        minted = replace(authorization, authenticator=authenticator)
        self.__state_store.record_issuance(
            minted.authorization_id,
            _destroy_authorization_fingerprint(minted),
        )
        return minted


class DestroyAuthorizationVerifier:
    """Provider-facing verification, reservation, and completion capability."""

    def __init__(self, state_store: DestroyAuthorizationStateStore) -> None:
        self.__state_store = state_store

    def verifies(self, authorization: DestroyAuthorization) -> bool:
        return self.__state_store.verifies(
            authorization.authorization_id,
            _destroy_authorization_fingerprint(authorization),
        )

    def reserved(self, authorization: DestroyAuthorization) -> bool:
        return self.__state_store.reserved(authorization.authorization_id)

    def completed(self, authorization: DestroyAuthorization) -> bool:
        return self.__state_store.completed(authorization.authorization_id)

    def reserve(self, authorization: DestroyAuthorization) -> bool:
        return self.__state_store.compare_and_swap_reserved(
            authorization.authorization_id,
            _destroy_authorization_fingerprint(authorization),
        )

    def complete(self, authorization: DestroyAuthorization) -> bool:
        return self.__state_store.compare_and_swap_completed(
            authorization.authorization_id,
            _destroy_authorization_fingerprint(authorization),
        )


@dataclass(frozen=True, slots=True)
class LifecycleOperationRecord:
    """Append/CAS record owned by SSSF, not a provider lifecycle database."""

    record_id: str
    operation: OperationKey
    requested_identity: SandboxIdentity
    source_identity: SourceIdentity
    attempt_id: str
    prior_state: LifecycleState
    observed_state: LifecycleState
    observation: Observation
    requested_at: str
    observed_at: str
    observation_reason: str
    evidence_refs: tuple[str, ...] = ()
    provider_resource_id: str | None = None
    destroy_authorization: DestroyAuthorization | None = None
    version: int = 0

    def __post_init__(self) -> None:
        _token(self.record_id, "record_id")
        if self.operation.attempt_id != self.attempt_id:
            raise ValueError("record attempt identity must equal operation attempt identity")
        if self.requested_identity.run_id != self.operation.run_id:
            raise ValueError("record requested identity and operation run_id differ")
        if not isinstance(self.source_identity, SourceIdentity):
            raise ValueError("record source identity is required")
        if not isinstance(self.prior_state, LifecycleState) or not isinstance(self.observed_state, LifecycleState):
            raise ValueError("record states must be closed")
        if not isinstance(self.observation, Observation):
            raise ValueError("record observation must be closed")
        _timestamp(self.requested_at, "requested_at")
        _timestamp(self.observed_at, "observed_at")
        _nonempty(self.observation_reason, "observation_reason")
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))
        _tokens(self.evidence_refs, "record evidence_refs")
        if self.provider_resource_id is not None:
            _token(self.provider_resource_id, "record provider_resource_id")
        if self.observation is Observation.COULD_NOT_OBSERVE and self.observed_state is LifecycleState.ABSENT:
            raise ValueError("record CNO cannot silently assert absence")
        if self.destroy_authorization is not None:
            if self.destroy_authorization.run_id != self.operation.run_id:
                raise ValueError("destroy authorization run identity differs")
            if self.provider_resource_id != self.destroy_authorization.provider_resource_id:
                raise ValueError("destroy authorization resource identity differs")
            if (
                self.destroy_authorization.operation_id != self.operation.operation_id
                or self.destroy_authorization.idempotency_key != self.operation.idempotency_key
            ):
                raise ValueError("destroy authorization operation identity differs")


class LifecycleRecordStore(Protocol):
    """SSSF's persistence seam; implementations use the existing observability owner."""

    def append(self, record: LifecycleOperationRecord) -> int:
        ...

    def compare_and_swap(
        self,
        run_id: str,
        operation_id: str,
        expected_version: int,
        record: LifecycleOperationRecord,
    ) -> int:
        ...

    def latest(self, run_id: str, operation_id: str) -> LifecycleOperationRecord | None:
        ...


class InMemoryLifecycleRecordStore:
    """Deterministic test store; production must bind the SSSF-owned store."""

    def __init__(self) -> None:
        self._records: list[LifecycleOperationRecord] = []

    @property
    def records(self) -> tuple[LifecycleOperationRecord, ...]:
        return tuple(self._records)

    def append(self, record: LifecycleOperationRecord) -> int:
        current = self.latest(record.operation.run_id, record.operation.operation_id)
        version = 0 if current is None else current.version + 1
        if record.version != version:
            raise ValueError("append version does not match the durable record sequence")
        self._records.append(record)
        return version

    def compare_and_swap(
        self,
        run_id: str,
        operation_id: str,
        expected_version: int,
        record: LifecycleOperationRecord,
    ) -> int:
        if record.operation.run_id != run_id or record.operation.operation_id != operation_id:
            raise ValueError("CAS record identity differs from the selected lifecycle stream")
        current = self.latest(run_id, operation_id)
        if current is None or current.version != expected_version:
            raise RuntimeError("lifecycle record compare-and-swap lost its owner")
        if record.version != expected_version + 1:
            raise ValueError("CAS record must advance exactly one version")
        self._records.append(record)
        return record.version

    def latest(self, run_id: str, operation_id: str) -> LifecycleOperationRecord | None:
        matches = [
            record
            for record in self._records
            if record.operation.run_id == run_id and record.operation.operation_id == operation_id
        ]
        return matches[-1] if matches else None


@dataclass(frozen=True, slots=True)
class OutcomeCheck:
    name: str
    observation: Observation | None
    required: bool = True
    applicable: bool = True
    identity_verified: bool = True
    complete: bool = True
    cleanup_verified: bool = True
    reason: str = ""

    def __post_init__(self) -> None:
        _token(self.name, "outcome check name")
        if not isinstance(self.required, bool) or not isinstance(self.applicable, bool):
            raise ValueError("outcome check applicability flags must be boolean")
        for name in ("identity_verified", "complete", "cleanup_verified"):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"outcome check {name} must be boolean")
        if self.observation is not None and not isinstance(self.observation, Observation):
            raise ValueError("outcome check observation must be closed or None")
        if not self.reason:
            object.__setattr__(self, "reason", "no reason supplied")


@dataclass(frozen=True, slots=True)
class SecretRetirementFacts:
    sandbox_identity: SandboxIdentity
    operation: OperationKey
    secret_refs: tuple[str, ...]
    observation: Observation
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.sandbox_identity, SandboxIdentity):
            raise ValueError("secret retirement sandbox identity is required")
        if self.operation.kind is not OperationKind.DESTROY:
            raise ValueError("secret retirement must bind the destroy operation")
        object.__setattr__(self, "secret_refs", tuple(self.secret_refs))
        _sorted_tokens(self.secret_refs, "retired secret_refs")
        if not isinstance(self.observation, Observation):
            raise ValueError("secret retirement observation must be closed")
        _nonempty(self.reason, "secret retirement reason")


@dataclass(frozen=True, slots=True)
class ObservationSummary:
    observation: Observation
    names: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class AggregateResult:
    status: Observation
    reason: str
    work: ObservationSummary
    cleanup: ObservationSummary
    evidence: ObservationSummary

    @property
    def aggregate(self) -> Observation:
        return self.status


def _component_summary(checks: Sequence[OutcomeCheck], label: str) -> ObservationSummary:
    applicable = [check for check in checks if check.applicable]
    names = tuple(check.name for check in checks)
    if not applicable:
        return ObservationSummary(
            Observation.COULD_NOT_OBSERVE,
            names,
            f"{label} has no applicable required observation",
        )
    bad = [check for check in applicable if check.observation is Observation.OBSERVED_BAD]
    if bad:
        return ObservationSummary(
            Observation.OBSERVED_BAD,
            names,
            "; ".join(f"{check.name}: {check.reason}" for check in bad),
        )
    cno = [
        check
        for check in applicable
        if check.observation is not Observation.OBSERVED_GOOD
        or not check.identity_verified
        or not check.complete
        or not check.cleanup_verified
    ]
    if cno:
        return ObservationSummary(
            Observation.COULD_NOT_OBSERVE,
            names,
            "; ".join(f"{check.name}: {check.reason}" for check in cno),
        )
    return ObservationSummary(Observation.OBSERVED_GOOD, names, "all applicable observations are good")


def fold_aggregate(
    observations: Iterable[OutcomeCheck] | None = None,
    *,
    work: Iterable[OutcomeCheck] = (),
    cleanup: Iterable[OutcomeCheck] = (),
    evidence: Iterable[OutcomeCheck] = (),
) -> AggregateResult:
    """Fold a nonempty lifecycle result without losing component observations.

    Precedence is deterministic and intentionally not Boolean:

    1. an observed contradiction/FAIL wins;
    2. otherwise a required CNO, missing result, wrong identity, incomplete
       collection, or unverified cleanup yields CNO;
    3. PASS requires every applicable required observation to be good.
    """
    component_work = tuple(work)
    component_cleanup = tuple(cleanup)
    component_evidence = tuple(evidence)
    flat = list(observations or ()) + list(component_work) + list(component_cleanup) + list(component_evidence)
    if not flat:
        unknown = ObservationSummary(Observation.COULD_NOT_OBSERVE, (), "aggregate has no observations")
        return AggregateResult(Observation.COULD_NOT_OBSERVE, "nonempty aggregate required", unknown, unknown, unknown)

    applicable = [check for check in flat if check.applicable]
    bad = [check for check in applicable if check.observation is Observation.OBSERVED_BAD]
    if bad:
        reason = "; ".join(f"{check.name}: {check.reason}" for check in bad)
        return AggregateResult(
            Observation.OBSERVED_BAD,
            f"observed contradiction takes precedence: {reason}",
            _component_summary(component_work, "work"),
            _component_summary(component_cleanup, "cleanup"),
            _component_summary(component_evidence, "evidence"),
        )

    required = [check for check in applicable if check.required]
    cno = [
        check
        for check in required
        if check.observation is not Observation.OBSERVED_GOOD
        or not check.identity_verified
        or not check.complete
        or not check.cleanup_verified
    ]
    if not required:
        reason = "no applicable required observations"
        status = Observation.COULD_NOT_OBSERVE
    elif cno:
        reason = "; ".join(f"{check.name}: {check.reason}" for check in cno)
        status = Observation.COULD_NOT_OBSERVE
    else:
        reason = "all applicable required observations are observed-good"
        status = Observation.OBSERVED_GOOD
    return AggregateResult(
        status,
        reason,
        _component_summary(component_work, "work"),
        _component_summary(component_cleanup, "cleanup"),
        _component_summary(component_evidence, "evidence"),
    )


class DestroyNotAuthorized(RuntimeError):
    pass


def _obligation_digest(checks: Sequence[OutcomeCheck]) -> str:
    raw = json.dumps(
        [
            {
                "name": check.name,
                "observation": check.observation.value if check.observation else None,
                "required": check.required,
                "applicable": check.applicable,
                "identity_verified": check.identity_verified,
                "complete": check.complete,
                "cleanup_verified": check.cleanup_verified,
                "reason": check.reason,
            }
            for check in checks
        ],
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(raw).hexdigest()


def issue_destroy_authorization(
    spec: SandboxSpec,
    identity: SandboxIdentity,
    operation: OperationKey,
    *,
    artifact: ArtifactExportFacts,
    git: GitExportFacts,
    artifact_spec: ArtifactSpec,
    git_spec: GitExportSpec,
    authorization_issuer: DestroyAuthorizationIssuer,
    secret_retirement: SecretRetirementFacts | None = None,
    issued_at: str = "1970-01-01T00:00:00Z",
) -> DestroyAuthorization:
    """Mint destruction authority only after SSSF-owned export obligations pass."""
    if operation.kind is not OperationKind.DESTROY:
        raise DestroyNotAuthorized("destroy authorization requires a DESTROY operation")
    if (
        operation.run_id != spec.run_id
        or identity.run_id != spec.run_id
        or identity.spec_digest != spec.identity_digest
    ):
        raise DestroyNotAuthorized("destroy authorization identity is stale")
    if identity.provider_resource_id is None:
        raise DestroyNotAuthorized("destroy authorization needs a provider resource identity")
    if not artifact_spec.applicable or not artifact_spec.required:
        raise DestroyNotAuthorized("destroy authorization requires an applicable required artifact obligation")
    if not git_spec.applicable or not git_spec.required:
        raise DestroyNotAuthorized("destroy authorization requires an applicable required Git obligation")
    if not isinstance(authorization_issuer, DestroyAuthorizationIssuer):
        raise DestroyNotAuthorized("destroy authorization requires the SSSF-only issuer")
    artifact_context = artifact_spec.manifest_context
    if (
        artifact_spec.operation.run_id != spec.run_id
        or artifact_context.run_id != spec.run_id
        or artifact_context.canonical_url != spec.source_repo
        or artifact_context.base_sha != spec.source_commit
    ):
        raise DestroyNotAuthorized("artifact obligation does not belong to the sandbox specification")
    if (
        git_spec.operation.run_id != spec.run_id
        or git_spec.source != spec.source_identity
        or git_spec.expected_base_commit != spec.source_commit
        or git_spec.expected_base_tree != spec.source_tree
        or git_spec.expected_tip_commit is None
        or artifact_context.candidate_sha != git_spec.expected_tip_commit
    ):
        raise DestroyNotAuthorized("Git obligation does not belong to the sandbox specification")
    artifact_check = validate_artifact_export(
        artifact_spec, artifact, provider_resource_id=identity.provider_resource_id
    )
    git_check = validate_git_export(
        git_spec, git, provider_resource_id=identity.provider_resource_id
    )
    checks = [artifact_check, git_check]
    if spec.secret_refs:
        if secret_retirement is None:
            raise DestroyNotAuthorized("secret retirement observation is required before destroy")
        retirement_identity_ok = (
            secret_retirement.sandbox_identity == identity
            and secret_retirement.operation == operation
            and secret_retirement.secret_refs == tuple(sorted(spec.secret_refs))
        )
        checks.append(
            OutcomeCheck(
                "secret-retirement",
                secret_retirement.observation,
                identity_verified=retirement_identity_ok,
                complete=retirement_identity_ok,
                reason=secret_retirement.reason,
            )
        )
    folded = fold_aggregate(evidence=checks)
    if folded.status is not Observation.OBSERVED_GOOD:
        raise DestroyNotAuthorized(f"destroy obligations are not PASS: {folded.reason}")
    obligation_digest = _obligation_digest(checks)
    auth_raw = f"destroy/v1|{spec.run_id}|{identity.provider_resource_id}|{operation.idempotency_key}|{obligation_digest}"
    authorization_id = hashlib.sha256(auth_raw.encode()).hexdigest()
    authorization = DestroyAuthorization(
        authorization_id=authorization_id,
        run_id=spec.run_id,
        provider_resource_id=identity.provider_resource_id,
        sandbox_spec_digest=identity.spec_digest,
        operation_id=operation.operation_id,
        idempotency_key=operation.idempotency_key,
        source_identity=spec.source_identity,
        obligations_digest=obligation_digest,
        issued_at=issued_at,
        authenticator="0" * 64,
    )
    return authorization_issuer._mint(authorization)


# ---------------------------------------------------------------------------
# Public provider interface


class SandboxProvider(Protocol):
    """Environment mechanics only; no acceptance, promotion, or recovery policy."""

    def create(self, spec: SandboxSpec, operation: OperationKey) -> CreateFacts:
        ...

    def inspect(self, identity: SandboxIdentity, operation: OperationKey) -> InspectFacts:
        ...

    def exec(self, identity: SandboxIdentity, command: CommandSpec, operation: OperationKey) -> ExecFacts:
        ...

    def copy_in(self, identity: SandboxIdentity, copy: CopySpec) -> CopyFacts:
        ...

    def collect_artifacts(self, identity: SandboxIdentity, artifact: ArtifactSpec) -> ArtifactExportFacts:
        ...

    def export_git(self, identity: SandboxIdentity, git: GitExportSpec) -> GitExportFacts:
        ...

    def inspect_processes(self, identity: SandboxIdentity, operation: OperationKey) -> ProcessFacts:
        ...

    def wait_quiescent(self, identity: SandboxIdentity, operation: OperationKey) -> ProcessFacts:
        ...

    def stop(self, identity: SandboxIdentity, operation: OperationKey) -> StopFacts:
        ...

    def destroy(
        self,
        identity: SandboxIdentity,
        operation: OperationKey,
        authorization: DestroyAuthorization | None,
    ) -> DestroyFacts:
        ...

    def reconcile(self, identity: SandboxIdentity, operation: OperationKey) -> ReconciliationFacts:
        ...


# ---------------------------------------------------------------------------
# Deterministic in-process fake.  It has no provider/network calls.


class FakeControl(str, Enum):
    CREATE_RESPONSE_AMBIGUITY = "create-response-ambiguity"
    STALE_IDENTITY = "stale-identity"
    WRONG_IDENTITY = "wrong-identity"
    EXEC_TIMEOUT = "exec-timeout"
    EXEC_CANCELLED = "exec-cancelled"
    EXEC_OVERFLOW = "exec-overflow"
    PROVIDER_CLIENT_CLEANUP_CNO = "provider-client-cleanup-cno"
    WORKLOAD_LEAK = "workload-leak"
    ARTIFACT_MISSING = "artifact-missing"
    ARTIFACT_TAMPERED = "artifact-tampered"
    ARTIFACT_OVERFLOW = "artifact-overflow"
    GIT_WRONG_ANCESTRY = "git-wrong-ancestry"
    STOP_PARTIAL = "stop-partial"
    DESTROY_RESIDUAL = "destroy-residual"
    DESTROY_RESIDUAL_RECOVERY_CNO = "destroy-residual-recovery-cno"
    DESTROY_AFTER_RESERVATION_CNO = "destroy-after-reservation-cno"
    DESTROY_BEFORE_COMPLETION_CNO = "destroy-before-completion-cno"
    INSPECT_UNREACHABLE = "inspect-unreachable"
    ALREADY_ABSENT = "already-absent"
    DUPLICATE_RESOURCES = "duplicate-resources"
    RESOURCE_ID_COLLISION = "resource-id-collision"


class LifecycleBoundary(str, Enum):
    CREATE = "create"
    SOURCE_COPY = "source-copy"
    SETUP = "setup"
    EXEC = "exec"
    ARTIFACT_EXPORT = "artifact-export"
    GIT_EXPORT = "git-export"
    PROCESS_INSPECTION = "process-inspection"
    SECRET_RETIREMENT = "secret-retirement"
    STOP = "stop"
    DESTROY = "destroy"
    POST_DESTROY_RECONCILIATION = "post-destroy-reconciliation"


class InterruptTiming(str, Enum):
    BEFORE = "before"
    AFTER = "after"


@dataclass
class _FakeResource:
    identity: SandboxIdentity
    spec: SandboxSpec
    state: LifecycleState = LifecycleState.PRESENT
    source_staged: bool = False
    client_quiescent: bool = True
    workload_quiescent: bool = True
    resources_quiescent: bool = True
    destroyed: bool = False
    residual: bool = False
    artifacts_exported: bool = False
    git_exported: bool = False
    secrets_retired: bool = False


class FakeSandboxProvider:
    """A watched-red fake with deterministic facts and zero external calls."""

    def __init__(
        self,
        controls: Iterable[FakeControl] = (),
        *,
        interrupt_before: LifecycleBoundary | None = None,
        interrupt_after: LifecycleBoundary | None = None,
        authorization_verifier: DestroyAuthorizationVerifier | None = None,
    ) -> None:
        self.controls = frozenset(controls)
        self.interrupt_before = interrupt_before
        self.interrupt_after = interrupt_after
        self._resources: dict[SandboxIdentity, _FakeResource] = {}
        self._by_run: dict[str, SandboxIdentity] = {}
        self._create_calls: dict[str, int] = {}
        self._destroy_interruptions: set[FakeControl] = set()
        self._authorization_verifier = authorization_verifier
        self.calls: list[tuple[OperationKind, str]] = []
        self.external_call_count = 0

    @property
    def provider_calls(self) -> int:
        """Always zero: the fake cannot reach Docker, exe.dev, or a network."""
        return self.external_call_count

    @property
    def resource_ids(self) -> tuple[str, ...]:
        return tuple(sorted(resource.identity.provider_resource_id for resource in self._resources.values() if resource.identity.provider_resource_id))

    def _record(self, operation: OperationKey) -> None:
        self.calls.append((operation.kind, operation.idempotency_key))

    def _now(self, operation: OperationKey) -> str:
        # Stable fixture timestamps make serialized facts reproducible.
        return f"1970-01-01T00:00:{len(self.calls):02d}Z"

    def _interrupted(self, boundary: LifecycleBoundary, timing: InterruptTiming) -> bool:
        return (
            (timing is InterruptTiming.BEFORE and self.interrupt_before is boundary)
            or (timing is InterruptTiming.AFTER and self.interrupt_after is boundary)
        )

    def _base(
        self,
        operation: OperationKey,
        observation: Observation,
        reason: str,
        *,
        prior: LifecycleState = LifecycleState.UNKNOWN,
        state: LifecycleState = LifecycleState.UNKNOWN,
        resource_id: str | None = None,
        evidence: tuple[str, ...] = (),
    ) -> dict[str, object]:
        return {
            "operation": operation,
            "observation": observation,
            "reason": reason,
            "observed_at": self._now(operation),
            "prior_state": prior,
            "observed_state": state,
            "provider_resource_id": resource_id,
            "evidence_refs": evidence,
        }

    def _resource_for(self, identity: SandboxIdentity) -> tuple[_FakeResource | None, Observation]:
        if identity.provider_resource_id is None:
            return None, Observation.COULD_NOT_OBSERVE
        resource = self._resources.get(identity)
        if resource is not None:
            return resource, Observation.OBSERVED_GOOD
        collision = any(
            stored.provider_resource_id == identity.provider_resource_id
            for stored in self._resources
        )
        return None, Observation.OBSERVED_BAD if collision else Observation.COULD_NOT_OBSERVE

    def _wrong_identity(self, identity: SandboxIdentity, operation: OperationKey, *, state: LifecycleState = LifecycleState.UNKNOWN) -> InspectFacts:
        return InspectFacts(
            **self._base(
                operation,
                Observation.OBSERVED_BAD,
                "stale or wrong provider/resource identity",
                state=state,
                resource_id=identity.provider_resource_id,
            ),
            identity_observation=Observation.OBSERVED_BAD,
        )

    def _identity_or_fact(self, identity: SandboxIdentity, operation: OperationKey) -> _FakeResource | InspectFacts:
        if operation.run_id != identity.run_id:
            return self._wrong_identity(identity, operation)
        if FakeControl.STALE_IDENTITY in self.controls or FakeControl.WRONG_IDENTITY in self.controls:
            return self._wrong_identity(identity, operation)
        resource, lookup_observation = self._resource_for(identity)
        if resource is None:
            if lookup_observation is Observation.OBSERVED_BAD:
                return self._wrong_identity(identity, operation)
            return InspectFacts(
                **self._base(operation, Observation.COULD_NOT_OBSERVE, "provider resource identity could not be resolved", resource_id=identity.provider_resource_id),
                identity_observation=Observation.COULD_NOT_OBSERVE,
            )
        return resource

    def create(self, spec: SandboxSpec, operation: OperationKey) -> CreateFacts:
        self._record(operation)
        if operation.kind is not OperationKind.CREATE or operation.run_id != spec.run_id:
            return CreateFacts(
                **self._base(operation, Observation.OBSERVED_BAD, "create operation identity does not bind to SandboxSpec"),
                spec_digest=spec.identity_digest,
                resource_identity_observation=Observation.OBSERVED_BAD,
            )
        key_count = self._create_calls.get(operation.idempotency_key, 0)
        self._create_calls[operation.idempotency_key] = key_count + 1
        if self._interrupted(LifecycleBoundary.CREATE, InterruptTiming.BEFORE):
            return CreateFacts(
                **self._base(operation, Observation.COULD_NOT_OBSERVE, "interrupted before create linearization", state=LifecycleState.CREATING),
                spec_digest=spec.identity_digest,
            )
        existing_identity = self._by_run.get(spec.run_id)
        if existing_identity is not None:
            existing = self._resources[existing_identity]
            existing_id = existing_identity.provider_resource_id
            if existing.spec.identity_digest != spec.identity_digest:
                return CreateFacts(
                    **self._base(operation, Observation.OBSERVED_BAD, "same run requested a wrong SandboxSpec identity", state=existing.state, resource_id=existing_id),
                    spec_digest=spec.identity_digest,
                    resource_identity_observation=Observation.OBSERVED_BAD,
                    duplicate_resource_ids=(existing_id,),
                )
            if FakeControl.CREATE_RESPONSE_AMBIGUITY in self.controls and key_count == 0:
                return CreateFacts(
                    **self._base(operation, Observation.COULD_NOT_OBSERVE, "create response was ambiguous after resource linearization", state=existing.state, resource_id=None),
                    spec_digest=spec.identity_digest,
                    resource_identity_observation=Observation.COULD_NOT_OBSERVE,
                )
            return CreateFacts(
                **self._base(operation, Observation.OBSERVED_GOOD, "idempotent create retry adopted the existing resource", state=existing.state, resource_id=existing_id),
                spec_digest=spec.identity_digest,
                resource_identity_observation=Observation.OBSERVED_GOOD,
            )
        resource_id = "fake-sandbox-collision" if FakeControl.RESOURCE_ID_COLLISION in self.controls else f"fake-sandbox-{spec.run_id}"
        identity = SandboxIdentity(spec.run_id, spec.identity_digest, resource_id)
        resource = _FakeResource(identity, spec)
        self._resources[identity] = resource
        self._by_run[spec.run_id] = identity
        if FakeControl.DUPLICATE_RESOURCES in self.controls:
            duplicate_id = f"{resource_id}-duplicate"
            duplicate_identity = SandboxIdentity(spec.run_id, spec.identity_digest, duplicate_id)
            self._resources[duplicate_identity] = _FakeResource(duplicate_identity, spec)
        if FakeControl.CREATE_RESPONSE_AMBIGUITY in self.controls:
            fact = CreateFacts(
                **self._base(operation, Observation.COULD_NOT_OBSERVE, "create response was ambiguous after resource linearization", state=LifecycleState.PRESENT, resource_id=None),
                spec_digest=spec.identity_digest,
                resource_identity_observation=Observation.COULD_NOT_OBSERVE,
            )
        else:
            fact = CreateFacts(
                **self._base(operation, Observation.OBSERVED_GOOD, "resource created and identity observed", state=LifecycleState.PRESENT, resource_id=resource_id),
                spec_digest=spec.identity_digest,
                resource_identity_observation=Observation.OBSERVED_GOOD,
                duplicate_resource_ids=(resource_id, f"{resource_id}-duplicate") if FakeControl.DUPLICATE_RESOURCES in self.controls else (),
            )
        if self._interrupted(LifecycleBoundary.CREATE, InterruptTiming.AFTER):
            return CreateFacts(
                **self._base(operation, Observation.COULD_NOT_OBSERVE, "interrupted after create linearization", state=LifecycleState.PRESENT, resource_id=resource_id),
                spec_digest=spec.identity_digest,
                resource_identity_observation=Observation.COULD_NOT_OBSERVE,
            )
        return fact

    def inspect(self, identity: SandboxIdentity, operation: OperationKey) -> InspectFacts:
        self._record(operation)
        if operation.kind is not OperationKind.INSPECT or operation.run_id != identity.run_id:
            return self._wrong_identity(identity, operation)
        if self._interrupted(LifecycleBoundary.PROCESS_INSPECTION, InterruptTiming.BEFORE):
            return InspectFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "interrupted before inspection", resource_id=identity.provider_resource_id))
        if FakeControl.INSPECT_UNREACHABLE in self.controls:
            return InspectFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "provider inspection endpoint is unreachable", resource_id=identity.provider_resource_id))
        target = self._identity_or_fact(identity, operation)
        if isinstance(target, InspectFacts):
            return target
        if FakeControl.ALREADY_ABSENT in self.controls or target.destroyed and not target.residual:
            return InspectFacts(**self._base(operation, Observation.OBSERVED_GOOD, "resource absence observed", prior=target.state, state=LifecycleState.ABSENT, resource_id=identity.provider_resource_id), identity_observation=Observation.OBSERVED_GOOD)
        fact = InspectFacts(**self._base(operation, Observation.OBSERVED_GOOD, "resource identity and state observed", prior=target.state, state=target.state, resource_id=identity.provider_resource_id), identity_observation=Observation.OBSERVED_GOOD)
        if self._interrupted(LifecycleBoundary.PROCESS_INSPECTION, InterruptTiming.AFTER):
            return InspectFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "interrupted after inspection", prior=target.state, state=LifecycleState.UNKNOWN, resource_id=identity.provider_resource_id), identity_observation=Observation.COULD_NOT_OBSERVE)
        return fact

    def copy_in(self, identity: SandboxIdentity, copy: CopySpec) -> CopyFacts:
        self._record(copy.operation)
        if copy.operation.run_id != identity.run_id:
            return CopyFacts(**self._base(copy.operation, Observation.OBSERVED_BAD, "source copy operation identity is wrong", resource_id=identity.provider_resource_id), source_observation=Observation.OBSERVED_BAD, guest_path=copy.guest_path)
        if self._interrupted(LifecycleBoundary.SOURCE_COPY, InterruptTiming.BEFORE):
            return CopyFacts(**self._base(copy.operation, Observation.COULD_NOT_OBSERVE, "interrupted before explicit source/input copy", resource_id=identity.provider_resource_id), source_observation=Observation.COULD_NOT_OBSERVE, guest_path=copy.guest_path)
        target, lookup_observation = self._resource_for(identity)
        if target is None:
            return CopyFacts(**self._base(copy.operation, lookup_observation, "source copy target identity mismatched" if lookup_observation is Observation.OBSERVED_BAD else "source copy target could not be observed", resource_id=identity.provider_resource_id), source_observation=lookup_observation, guest_path=copy.guest_path)
        if FakeControl.STALE_IDENTITY in self.controls or FakeControl.WRONG_IDENTITY in self.controls:
            return CopyFacts(**self._base(copy.operation, Observation.OBSERVED_BAD, "source copy identity mismatch", resource_id=identity.provider_resource_id), source_observation=Observation.OBSERVED_BAD, guest_path=copy.guest_path)
        target.source_staged = True
        source_digest = copy.expected_sha256 or hashlib.sha256(copy.source_ref.encode()).hexdigest()
        fact = CopyFacts(**self._base(copy.operation, Observation.OBSERVED_GOOD, "explicit source/input copy observed", prior=target.state, state=LifecycleState.SOURCE_STAGED, resource_id=identity.provider_resource_id), source_observation=Observation.OBSERVED_GOOD, source_digest=source_digest, guest_path=copy.guest_path)
        target.state = LifecycleState.SOURCE_STAGED
        if self._interrupted(LifecycleBoundary.SOURCE_COPY, InterruptTiming.AFTER):
            return CopyFacts(**self._base(copy.operation, Observation.COULD_NOT_OBSERVE, "interrupted after source/input copy", prior=LifecycleState.SOURCE_STAGED, state=LifecycleState.SOURCE_STAGED, resource_id=identity.provider_resource_id), source_observation=Observation.COULD_NOT_OBSERVE, source_digest=source_digest, guest_path=copy.guest_path)
        return fact

    def exec(self, identity: SandboxIdentity, command: CommandSpec, operation: OperationKey) -> ExecFacts:
        self._record(operation)
        target, lookup_observation = self._resource_for(identity)
        if target is None:
            return self._exec_failure(operation, identity, "typed exec target identity mismatched" if lookup_observation is Observation.OBSERVED_BAD else "typed exec target identity could not be observed", lookup_observation)
        if operation.kind is not OperationKind.EXEC or operation.run_id != identity.run_id:
            return self._exec_failure(operation, identity, "typed exec operation identity is wrong", Observation.OBSERVED_BAD)
        if self._interrupted(LifecycleBoundary.SETUP if command.execution_id == "setup" else LifecycleBoundary.EXEC, InterruptTiming.BEFORE):
            return self._exec_failure(operation, identity, "interrupted before typed execution", Observation.COULD_NOT_OBSERVE)
        if FakeControl.STALE_IDENTITY in self.controls or FakeControl.WRONG_IDENTITY in self.controls:
            return self._exec_failure(operation, identity, "typed exec identity mismatch", Observation.OBSERVED_BAD)
        clean_client = QuiescenceFact(QuiescenceDomain.HOST_PROVIDER_CLIENT, Observation.OBSERVED_GOOD, True, "provider-client process custody verified")
        clean_workload = QuiescenceFact(QuiescenceDomain.SANDBOX_WORKLOAD, Observation.OBSERVED_GOOD, True, "workload completed and is quiescent")
        clean_resources = QuiescenceFact(QuiescenceDomain.SANDBOX_RESOURCES, Observation.OBSERVED_GOOD, True, "sandbox workload resources are quiescent")
        if FakeControl.PROVIDER_CLIENT_CLEANUP_CNO in self.controls:
            clean_client = QuiescenceFact(QuiescenceDomain.HOST_PROVIDER_CLIENT, Observation.COULD_NOT_OBSERVE, None, "provider-client cleanup could not be verified", ("fake-client-1",))
        if FakeControl.WORKLOAD_LEAK in self.controls:
            target.workload_quiescent = False
            clean_workload = QuiescenceFact(QuiescenceDomain.SANDBOX_WORKLOAD, Observation.OBSERVED_BAD, False, "sandbox workload process leaked", ("fake-workload-1",))
            clean_resources = QuiescenceFact(QuiescenceDomain.SANDBOX_RESOURCES, Observation.OBSERVED_BAD, False, "sandbox workload resource leaked", ("fake-volume-1",))
        else:
            target.workload_quiescent = True
        output = b"typed-fake-success\n"
        reason = "typed command completed with bounded streams"
        state = LifecycleState.READY
        observation = Observation.OBSERVED_GOOD
        timed_out = False
        cancelled = False
        overflowed = False
        if FakeControl.EXEC_TIMEOUT in self.controls:
            observation, reason, timed_out = Observation.COULD_NOT_OBSERVE, "monotonic command timeout expired", True
        elif FakeControl.EXEC_CANCELLED in self.controls:
            observation, reason, cancelled = Observation.COULD_NOT_OBSERVE, "command cancellation was observed", True
        elif FakeControl.EXEC_OVERFLOW in self.controls:
            observation, reason, overflowed = Observation.COULD_NOT_OBSERVE, "stdout/stderr bound overflowed", True
            output = b"x" * (command.max_stdout_bytes + 1)
        elif FakeControl.PROVIDER_CLIENT_CLEANUP_CNO in self.controls:
            observation, reason = Observation.COULD_NOT_OBSERVE, "provider-client cleanup could not be verified"
        elif FakeControl.WORKLOAD_LEAK in self.controls:
            observation, reason = Observation.OBSERVED_BAD, "workload quiescence contradiction observed"
        fact = ExecFacts(
            **self._base(operation, observation, reason, prior=target.state, state=state, resource_id=identity.provider_resource_id),
            return_code=0 if observation is Observation.OBSERVED_GOOD else None,
            stdout=output[: command.max_stdout_bytes],
            stderr=b"",
            stdout_bytes_seen=len(output),
            stderr_bytes_seen=0,
            stdout_sha256=hashlib.sha256(output[: command.max_stdout_bytes]).hexdigest(),
            stderr_sha256=hashlib.sha256(b"").hexdigest(),
            output_overflowed=overflowed,
            client_process=clean_client,
            workload=clean_workload,
            resources=clean_resources,
            timed_out=timed_out,
            cancelled=cancelled,
        )
        boundary = LifecycleBoundary.SETUP if command.execution_id == "setup" else LifecycleBoundary.EXEC
        if self._interrupted(boundary, InterruptTiming.AFTER):
            return ExecFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "interrupted after typed execution", prior=target.state, state=LifecycleState.UNKNOWN, resource_id=identity.provider_resource_id), return_code=fact.return_code, stdout=fact.stdout, stderr=fact.stderr, stdout_bytes_seen=fact.stdout_bytes_seen, stderr_bytes_seen=fact.stderr_bytes_seen, stdout_sha256=fact.stdout_sha256, stderr_sha256=fact.stderr_sha256, output_overflowed=fact.output_overflowed, client_process=fact.client_process, workload=fact.workload, resources=fact.resources, timed_out=fact.timed_out, cancelled=fact.cancelled)
        return fact

    def _exec_failure(self, operation: OperationKey, identity: SandboxIdentity, reason: str, observation: Observation) -> ExecFacts:
        unknown_client = QuiescenceFact(QuiescenceDomain.HOST_PROVIDER_CLIENT, observation, None if observation is Observation.COULD_NOT_OBSERVE else False, reason)
        unknown_workload = QuiescenceFact(QuiescenceDomain.SANDBOX_WORKLOAD, observation, None if observation is Observation.COULD_NOT_OBSERVE else False, reason)
        unknown_resources = QuiescenceFact(QuiescenceDomain.SANDBOX_RESOURCES, observation, None if observation is Observation.COULD_NOT_OBSERVE else False, reason)
        return ExecFacts(**self._base(operation, observation, reason, resource_id=identity.provider_resource_id), client_process=unknown_client, workload=unknown_workload, resources=unknown_resources)

    def collect_artifacts(self, identity: SandboxIdentity, artifact: ArtifactSpec) -> ArtifactExportFacts:
        self._record(artifact.operation)
        if artifact.operation.run_id != identity.run_id:
            return ArtifactExportFacts(**self._base(artifact.operation, Observation.OBSERVED_BAD, "artifact collection operation identity is wrong", resource_id=identity.provider_resource_id), artifact_id=artifact.artifact_id)
        if self._interrupted(LifecycleBoundary.ARTIFACT_EXPORT, InterruptTiming.BEFORE):
            return ArtifactExportFacts(**self._base(artifact.operation, Observation.COULD_NOT_OBSERVE, "interrupted before artifact collection", resource_id=identity.provider_resource_id), artifact_id=artifact.artifact_id)
        target, lookup_observation = self._resource_for(identity)
        if target is None:
            return ArtifactExportFacts(**self._base(artifact.operation, lookup_observation, "artifact collection target identity mismatched" if lookup_observation is Observation.OBSERVED_BAD else "artifact collection target identity could not be observed", resource_id=identity.provider_resource_id), artifact_id=artifact.artifact_id)
        if not artifact.applicable:
            return ArtifactExportFacts(**self._base(artifact.operation, Observation.OBSERVED_GOOD, "artifact obligation is explicitly not applicable", prior=target.state, state=target.state, resource_id=identity.provider_resource_id), artifact_id=artifact.artifact_id, applicable=False, complete=True)
        item = ArtifactInventoryItem("evidence/result.json", "json", 18, hashlib.sha256(b'{"result":"good"}\n').hexdigest(), artifact.producer_id, identity.run_id, artifact.operation.operation_id, artifact.operation.attempt_id)
        inventory = (item,)
        missing: tuple[str, ...] = ()
        tampered: tuple[str, ...] = ()
        complete = True
        observation = Observation.OBSERVED_GOOD
        reason = "bounded artifact inventory and digests observed"
        overflowed = False
        if FakeControl.ARTIFACT_MISSING in self.controls:
            inventory = ()
            missing = artifact.paths or ("evidence/result.json",)
            complete, observation, reason = False, Observation.COULD_NOT_OBSERVE, "required artifact was missing"
        elif FakeControl.ARTIFACT_TAMPERED in self.controls:
            item = ArtifactInventoryItem(item.path, item.artifact_type, item.byte_length, "0" * 64, item.producer_id, item.run_id, item.operation_id, item.attempt_id)
            inventory = (item,)
            tampered = (item.path,)
            observation, reason = Observation.OBSERVED_BAD, "artifact digest mismatch/tamper observed"
        elif FakeControl.ARTIFACT_OVERFLOW in self.controls:
            complete, observation, reason, overflowed = False, Observation.COULD_NOT_OBSERVE, "artifact byte/file bound overflowed", True
        fact = ArtifactExportFacts(**self._base(artifact.operation, observation, reason, prior=target.state, state=LifecycleState.EXPORTING, resource_id=identity.provider_resource_id), artifact_id=artifact.artifact_id, applicable=True, complete=complete, inventory=inventory, total_bytes=sum(entry.byte_length for entry in inventory), missing_paths=missing, tampered_paths=tampered, overflowed=overflowed)
        target.artifacts_exported = observation is Observation.OBSERVED_GOOD
        if self._interrupted(LifecycleBoundary.ARTIFACT_EXPORT, InterruptTiming.AFTER):
            return ArtifactExportFacts(**self._base(artifact.operation, Observation.COULD_NOT_OBSERVE, "interrupted after artifact collection", prior=target.state, state=LifecycleState.UNKNOWN, resource_id=identity.provider_resource_id), artifact_id=artifact.artifact_id, inventory=fact.inventory, total_bytes=fact.total_bytes, complete=fact.complete, missing_paths=fact.missing_paths, tampered_paths=fact.tampered_paths, overflowed=fact.overflowed)
        return fact

    def export_git(self, identity: SandboxIdentity, git: GitExportSpec) -> GitExportFacts:
        self._record(git.operation)
        if git.operation.run_id != identity.run_id:
            return GitExportFacts(**self._base(git.operation, Observation.OBSERVED_BAD, "Git export operation identity is wrong", resource_id=identity.provider_resource_id), export_ref=git.export_ref)
        if self._interrupted(LifecycleBoundary.GIT_EXPORT, InterruptTiming.BEFORE):
            return GitExportFacts(**self._base(git.operation, Observation.COULD_NOT_OBSERVE, "interrupted before Git export", resource_id=identity.provider_resource_id), export_ref=git.export_ref)
        target, lookup_observation = self._resource_for(identity)
        if target is None:
            return GitExportFacts(**self._base(git.operation, lookup_observation, "Git export target identity mismatched" if lookup_observation is Observation.OBSERVED_BAD else "Git export target identity could not be observed", resource_id=identity.provider_resource_id), export_ref=git.export_ref)
        tip_commit = git.expected_tip_commit or "2" * 40
        tip_tree = git.expected_tip_tree or "3" * 40
        observation = Observation.OBSERVED_GOOD
        reason = "Git base/tip/tree and ancestry verified before export"
        ancestry = True
        base_commit = git.expected_base_commit
        base_tree = git.expected_base_tree
        if FakeControl.GIT_WRONG_ANCESTRY in self.controls:
            observation, reason, ancestry = Observation.OBSERVED_BAD, "Git export ancestry did not descend from requested base", False
            base_commit = "4" * 40
        bundle = b"fake-git-bundle-v1"
        fact = GitExportFacts(**self._base(git.operation, observation, reason, prior=target.state, state=LifecycleState.EXPORTING, resource_id=identity.provider_resource_id), applicable=git.applicable, complete=observation is Observation.OBSERVED_GOOD, source=git.source, base_commit=base_commit, base_tree=base_tree, tip_commit=tip_commit, tip_tree=tip_tree, ancestry_verified=ancestry, export_ref=git.export_ref, bundle_sha256=hashlib.sha256(bundle).hexdigest(), bundle_bytes=len(bundle), promotion_authority=PromotionAuthority.NONE)
        target.git_exported = observation is Observation.OBSERVED_GOOD
        if self._interrupted(LifecycleBoundary.GIT_EXPORT, InterruptTiming.AFTER):
            return GitExportFacts(**self._base(git.operation, Observation.COULD_NOT_OBSERVE, "interrupted after Git export", prior=target.state, state=LifecycleState.UNKNOWN, resource_id=identity.provider_resource_id), applicable=git.applicable, complete=fact.complete, source=fact.source, base_commit=fact.base_commit, base_tree=fact.base_tree, tip_commit=fact.tip_commit, tip_tree=fact.tip_tree, ancestry_verified=fact.ancestry_verified, export_ref=git.export_ref, bundle_sha256=fact.bundle_sha256, bundle_bytes=fact.bundle_bytes, promotion_authority=PromotionAuthority.NONE)
        return fact

    def _process_facts(self, identity: SandboxIdentity, operation: OperationKey) -> ProcessFacts:
        if operation.run_id != identity.run_id or operation.kind not in {OperationKind.INSPECT_PROCESSES, OperationKind.WAIT_QUIESCENT}:
            reason = "process inspection operation identity is wrong"
            host = QuiescenceFact(QuiescenceDomain.HOST_PROVIDER_CLIENT, Observation.OBSERVED_BAD, False, reason)
            return ProcessFacts(**self._base(operation, Observation.OBSERVED_BAD, reason, resource_id=identity.provider_resource_id), host_client=host, workload=QuiescenceFact(QuiescenceDomain.SANDBOX_WORKLOAD, Observation.OBSERVED_BAD, False, reason), resources=QuiescenceFact(QuiescenceDomain.SANDBOX_RESOURCES, Observation.OBSERVED_BAD, False, reason))
        if self._interrupted(LifecycleBoundary.PROCESS_INSPECTION, InterruptTiming.BEFORE):
            cno = QuiescenceFact(QuiescenceDomain.HOST_PROVIDER_CLIENT, Observation.COULD_NOT_OBSERVE, None, "interrupted before process inspection")
            return ProcessFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "interrupted before process inspection", resource_id=identity.provider_resource_id), host_client=cno, workload=QuiescenceFact(QuiescenceDomain.SANDBOX_WORKLOAD, Observation.COULD_NOT_OBSERVE, None, cno.reason), resources=QuiescenceFact(QuiescenceDomain.SANDBOX_RESOURCES, Observation.COULD_NOT_OBSERVE, None, cno.reason))
        target, lookup_observation = self._resource_for(identity)
        if target is None:
            reason = "process target identity mismatched" if lookup_observation is Observation.OBSERVED_BAD else "process target identity could not be observed"
            quiescent = None if lookup_observation is Observation.COULD_NOT_OBSERVE else False
            host = QuiescenceFact(QuiescenceDomain.HOST_PROVIDER_CLIENT, lookup_observation, quiescent, reason)
            return ProcessFacts(**self._base(operation, lookup_observation, reason, resource_id=identity.provider_resource_id), host_client=host, workload=QuiescenceFact(QuiescenceDomain.SANDBOX_WORKLOAD, lookup_observation, quiescent, reason), resources=QuiescenceFact(QuiescenceDomain.SANDBOX_RESOURCES, lookup_observation, quiescent, reason))
        client = QuiescenceFact(QuiescenceDomain.HOST_PROVIDER_CLIENT, Observation.OBSERVED_GOOD, True, "host/provider-client process custody is quiescent")
        workload = QuiescenceFact(QuiescenceDomain.SANDBOX_WORKLOAD, Observation.OBSERVED_GOOD, True, "sandbox workload is quiescent")
        resources = QuiescenceFact(QuiescenceDomain.SANDBOX_RESOURCES, Observation.OBSERVED_GOOD, True, "sandbox resources are quiescent")
        observation = Observation.OBSERVED_GOOD
        reason = "host client and sandbox workload/resource quiescence observed"
        if FakeControl.INSPECT_UNREACHABLE in self.controls:
            cno = QuiescenceFact(QuiescenceDomain.HOST_PROVIDER_CLIENT, Observation.COULD_NOT_OBSERVE, None, "provider inspection endpoint is unreachable")
            return ProcessFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "provider process inspection was unreachable", resource_id=identity.provider_resource_id), host_client=cno, workload=QuiescenceFact(QuiescenceDomain.SANDBOX_WORKLOAD, Observation.COULD_NOT_OBSERVE, None, cno.reason), resources=QuiescenceFact(QuiescenceDomain.SANDBOX_RESOURCES, Observation.COULD_NOT_OBSERVE, None, cno.reason))
        if FakeControl.PROVIDER_CLIENT_CLEANUP_CNO in self.controls:
            client = QuiescenceFact(QuiescenceDomain.HOST_PROVIDER_CLIENT, Observation.COULD_NOT_OBSERVE, None, "provider-client process cleanup could not be verified", ("fake-client-1",))
            observation, reason = Observation.COULD_NOT_OBSERVE, "provider-client cleanup CNO"
        if FakeControl.WORKLOAD_LEAK in self.controls:
            workload = QuiescenceFact(QuiescenceDomain.SANDBOX_WORKLOAD, Observation.OBSERVED_BAD, False, "workload process leak observed", ("fake-workload-1",))
            resources = QuiescenceFact(QuiescenceDomain.SANDBOX_RESOURCES, Observation.OBSERVED_BAD, False, "workload resource residue observed", ("fake-volume-1",))
            observation, reason = Observation.OBSERVED_BAD, "workload leak contradicts clean quiescence"
        fact = ProcessFacts(**self._base(operation, observation, reason, prior=target.state, state=LifecycleState.QUIESCENT if observation is Observation.OBSERVED_GOOD else LifecycleState.RESIDUAL, resource_id=identity.provider_resource_id), host_client=client, workload=workload, resources=resources)
        if self._interrupted(LifecycleBoundary.PROCESS_INSPECTION, InterruptTiming.AFTER):
            cno = QuiescenceFact(QuiescenceDomain.HOST_PROVIDER_CLIENT, Observation.COULD_NOT_OBSERVE, None, "interrupted after process inspection")
            return ProcessFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "interrupted after process inspection", prior=target.state, state=LifecycleState.UNKNOWN, resource_id=identity.provider_resource_id), host_client=cno, workload=QuiescenceFact(QuiescenceDomain.SANDBOX_WORKLOAD, Observation.COULD_NOT_OBSERVE, None, cno.reason), resources=QuiescenceFact(QuiescenceDomain.SANDBOX_RESOURCES, Observation.COULD_NOT_OBSERVE, None, cno.reason))
        return fact

    def inspect_processes(self, identity: SandboxIdentity, operation: OperationKey) -> ProcessFacts:
        self._record(operation)
        return self._process_facts(identity, operation)

    def wait_quiescent(self, identity: SandboxIdentity, operation: OperationKey) -> ProcessFacts:
        self._record(operation)
        return self._process_facts(identity, operation)

    def stop(self, identity: SandboxIdentity, operation: OperationKey) -> StopFacts:
        self._record(operation)
        if operation.kind is not OperationKind.STOP or operation.run_id != identity.run_id:
            return StopFacts(**self._base(operation, Observation.OBSERVED_BAD, "stop operation identity is wrong", resource_id=identity.provider_resource_id))
        if self._interrupted(LifecycleBoundary.STOP, InterruptTiming.BEFORE):
            return StopFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "interrupted before stop", resource_id=identity.provider_resource_id))
        target, lookup_observation = self._resource_for(identity)
        if target is None:
            return StopFacts(**self._base(operation, lookup_observation, "stop target identity mismatched" if lookup_observation is Observation.OBSERVED_BAD else "stop target could not be observed", resource_id=identity.provider_resource_id))
        if FakeControl.STOP_PARTIAL in self.controls:
            target.state = LifecycleState.STOPPED
            target.workload_quiescent = False
            return StopFacts(**self._base(operation, Observation.OBSERVED_BAD, "stop acknowledged only partially; workload remains", prior=LifecycleState.PRESENT, state=LifecycleState.RESIDUAL, resource_id=identity.provider_resource_id), acknowledged=True, workload_stopped=False)
        target.state = LifecycleState.STOPPED
        target.workload_quiescent = True
        fact = StopFacts(**self._base(operation, Observation.OBSERVED_GOOD, "stop acknowledged and workload stopped", prior=LifecycleState.PRESENT, state=LifecycleState.STOPPED, resource_id=identity.provider_resource_id), acknowledged=True, workload_stopped=True)
        if self._interrupted(LifecycleBoundary.STOP, InterruptTiming.AFTER):
            return StopFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "interrupted after stop", prior=LifecycleState.STOPPED, state=LifecycleState.UNKNOWN, resource_id=identity.provider_resource_id), acknowledged=True, workload_stopped=True)
        return fact

    def destroy(self, identity: SandboxIdentity, operation: OperationKey, authorization: DestroyAuthorization | None) -> DestroyFacts:
        self._record(operation)
        if authorization is None:
            return DestroyFacts(**self._base(operation, Observation.OBSERVED_BAD, "destroy authorization is absent; provider did not destroy", resource_id=identity.provider_resource_id), authorization_id=None)
        if self._authorization_verifier is None or not self._authorization_verifier.verifies(authorization):
            return DestroyFacts(**self._base(operation, Observation.OBSERVED_BAD, "destroy authorization has no valid SSSF authenticator", resource_id=identity.provider_resource_id), authorization_id=authorization.authorization_id)
        if self._authorization_verifier.completed(authorization):
            return DestroyFacts(**self._base(operation, Observation.OBSERVED_BAD, "one-use destroy authorization was already completed", resource_id=identity.provider_resource_id), authorization_id=authorization.authorization_id)
        if operation.kind is not OperationKind.DESTROY:
            return DestroyFacts(**self._base(operation, Observation.OBSERVED_BAD, "destroy call used a non-destroy operation identity", resource_id=identity.provider_resource_id), authorization_id=authorization.authorization_id)
        if (
            authorization.run_id != identity.run_id
            or authorization.provider_resource_id != identity.provider_resource_id
            or authorization.sandbox_spec_digest != identity.spec_digest
            or authorization.operation_id != operation.operation_id
            or authorization.idempotency_key != operation.idempotency_key
        ):
            return DestroyFacts(**self._base(operation, Observation.OBSERVED_BAD, "destroy authorization has a stale or wrong identity", resource_id=identity.provider_resource_id), authorization_id=authorization.authorization_id)
        if self._interrupted(LifecycleBoundary.DESTROY, InterruptTiming.BEFORE):
            return DestroyFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "interrupted before destroy linearization", prior=LifecycleState.PRESENT, state=LifecycleState.DESTROYING, resource_id=identity.provider_resource_id), authorization_id=authorization.authorization_id)
        target, lookup_observation = self._resource_for(identity)
        if target is None:
            return DestroyFacts(**self._base(operation, lookup_observation, "destroy target identity mismatched" if lookup_observation is Observation.OBSERVED_BAD else "destroy target identity could not be authoritatively resolved", state=LifecycleState.UNKNOWN, resource_id=identity.provider_resource_id), authorization_id=authorization.authorization_id)
        if target.residual:
            if not self._authorization_verifier.reserve(authorization):
                return DestroyFacts(**self._base(operation, Observation.OBSERVED_BAD, "residual cleanup authority could not be durably reserved", state=LifecycleState.RESIDUAL, resource_id=identity.provider_resource_id), authorization_id=authorization.authorization_id)
            if FakeControl.DESTROY_RESIDUAL_RECOVERY_CNO in self.controls and FakeControl.DESTROY_RESIDUAL_RECOVERY_CNO not in self._destroy_interruptions:
                self._destroy_interruptions.add(FakeControl.DESTROY_RESIDUAL_RECOVERY_CNO)
                return DestroyFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "residual cleanup could not be observed", prior=LifecycleState.RESIDUAL, state=LifecycleState.UNKNOWN, resource_id=identity.provider_resource_id), authorization_id=authorization.authorization_id)
            target.residual = False
            target.state = LifecycleState.ABSENT
            target.resources_quiescent = True
            if not self._authorization_verifier.complete(authorization):
                return DestroyFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "residual cleanup succeeded but completion could not be durably recorded", prior=LifecycleState.RESIDUAL, state=LifecycleState.UNKNOWN, resource_id=identity.provider_resource_id), acknowledged=True, authorization_id=authorization.authorization_id)
            return DestroyFacts(**self._base(operation, Observation.OBSERVED_GOOD, "residual resource cleanup established authoritative absence", prior=LifecycleState.RESIDUAL, state=LifecycleState.ABSENT, resource_id=identity.provider_resource_id), acknowledged=True, authorization_id=authorization.authorization_id)
        if (target.destroyed and not target.residual) or FakeControl.ALREADY_ABSENT in self.controls:
            if not self._authorization_verifier.reserve(authorization) or not self._authorization_verifier.complete(authorization):
                return DestroyFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "destroy completion could not be durably recorded", resource_id=identity.provider_resource_id), authorization_id=authorization.authorization_id)
            target.destroyed = True
            target.state = LifecycleState.ABSENT
            target.resources_quiescent = True
            return DestroyFacts(**self._base(operation, Observation.OBSERVED_GOOD, "resource already absent; destroy is idempotent", prior=LifecycleState.ABSENT, state=LifecycleState.ABSENT, resource_id=identity.provider_resource_id), acknowledged=False, already_absent=True, authorization_id=authorization.authorization_id)
        if not self._authorization_verifier.reserve(authorization):
            return DestroyFacts(**self._base(operation, Observation.OBSERVED_BAD, "destroy authorization could not be durably reserved", resource_id=identity.provider_resource_id), authorization_id=authorization.authorization_id)
        if FakeControl.DESTROY_AFTER_RESERVATION_CNO in self.controls and FakeControl.DESTROY_AFTER_RESERVATION_CNO not in self._destroy_interruptions:
            self._destroy_interruptions.add(FakeControl.DESTROY_AFTER_RESERVATION_CNO)
            return DestroyFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "provider failed after destroy reservation but before side effect", prior=LifecycleState.PRESENT, state=LifecycleState.UNKNOWN, resource_id=identity.provider_resource_id), authorization_id=authorization.authorization_id)
        target.destroyed = True
        if FakeControl.DESTROY_BEFORE_COMPLETION_CNO in self.controls and FakeControl.DESTROY_BEFORE_COMPLETION_CNO not in self._destroy_interruptions:
            self._destroy_interruptions.add(FakeControl.DESTROY_BEFORE_COMPLETION_CNO)
            target.state = LifecycleState.ABSENT
            target.resources_quiescent = True
            return DestroyFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "provider failed after destroy side effect but before durable completion", prior=LifecycleState.DESTROYING, state=LifecycleState.UNKNOWN, resource_id=identity.provider_resource_id), acknowledged=True, authorization_id=authorization.authorization_id)
        if FakeControl.DESTROY_RESIDUAL in self.controls:
            target.residual = True
            target.state = LifecycleState.RESIDUAL
            target.resources_quiescent = False
            return DestroyFacts(**self._base(operation, Observation.OBSERVED_BAD, "destroy acknowledged but residual resource remains", prior=target.state, state=LifecycleState.RESIDUAL, resource_id=identity.provider_resource_id), acknowledged=True, residual_resource_ids=(identity.provider_resource_id or "",), authorization_id=authorization.authorization_id)
        if not self._authorization_verifier.complete(authorization):
            return DestroyFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "destroy occurred but completion could not be durably recorded", prior=LifecycleState.DESTROYING, state=LifecycleState.UNKNOWN, resource_id=identity.provider_resource_id), acknowledged=True, authorization_id=authorization.authorization_id)
        target.state = LifecycleState.ABSENT
        target.resources_quiescent = True
        fact = DestroyFacts(**self._base(operation, Observation.OBSERVED_GOOD, "destroy acknowledged", prior=LifecycleState.PRESENT, state=LifecycleState.ABSENT, resource_id=identity.provider_resource_id), acknowledged=True, authorization_id=authorization.authorization_id)
        if self._interrupted(LifecycleBoundary.DESTROY, InterruptTiming.AFTER):
            return DestroyFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "interrupted after destroy linearization", prior=LifecycleState.DESTROYING, state=LifecycleState.UNKNOWN, resource_id=identity.provider_resource_id), acknowledged=True, authorization_id=authorization.authorization_id)
        return fact

    def reconcile(self, identity: SandboxIdentity, operation: OperationKey) -> ReconciliationFacts:
        self._record(operation)
        if operation.kind is not OperationKind.RECONCILE or operation.run_id != identity.run_id:
            return ReconciliationFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "reconciliation operation identity is wrong", resource_id=identity.provider_resource_id), status=ReconciliationStatus.COULD_NOT_OBSERVE, identity_observation=Observation.OBSERVED_BAD)
        if self._interrupted(LifecycleBoundary.POST_DESTROY_RECONCILIATION, InterruptTiming.BEFORE) or FakeControl.INSPECT_UNREACHABLE in self.controls:
            return ReconciliationFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "authoritative reconciliation could not reach the provider", resource_id=identity.provider_resource_id), status=ReconciliationStatus.COULD_NOT_OBSERVE)
        if self._interrupted(LifecycleBoundary.POST_DESTROY_RECONCILIATION, InterruptTiming.AFTER):
            return ReconciliationFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, "interrupted after reconciliation observation", resource_id=identity.provider_resource_id), status=ReconciliationStatus.COULD_NOT_OBSERVE)
        if FakeControl.DUPLICATE_RESOURCES in self.controls:
            ids = tuple(
                sorted(
                    resource.identity.provider_resource_id
                    for resource in self._resources.values()
                    if resource.identity.run_id == identity.run_id
                    and resource.identity.spec_digest == identity.spec_digest
                    and resource.identity.provider_resource_id is not None
                )
            )
            return ReconciliationFacts(**self._base(operation, Observation.OBSERVED_BAD, "duplicate resources share one requested identity", state=LifecycleState.DUPLICATE, resource_id=identity.provider_resource_id), status=ReconciliationStatus.DUPLICATE, resource_ids=ids, duplicate_resource_ids=ids)
        target, lookup_observation = self._resource_for(identity)
        if target is None:
            reason = "cross-identity resource collision observed during reconciliation" if lookup_observation is Observation.OBSERVED_BAD else "reconciliation identity could not be resolved against authoritative enumeration"
            return ReconciliationFacts(**self._base(operation, Observation.COULD_NOT_OBSERVE, reason, resource_id=identity.provider_resource_id), status=ReconciliationStatus.COULD_NOT_OBSERVE, identity_observation=lookup_observation)
        if FakeControl.ALREADY_ABSENT in self.controls and target.destroyed and not target.residual:
            return ReconciliationFacts(**self._base(operation, Observation.OBSERVED_GOOD, "authoritative exact-identity absence observed", state=LifecycleState.ABSENT, resource_id=identity.provider_resource_id), status=ReconciliationStatus.ABSENT)
        if target.destroyed and not target.residual:
            return ReconciliationFacts(**self._base(operation, Observation.OBSERVED_GOOD, "authoritative resource absence observed", state=LifecycleState.ABSENT, resource_id=identity.provider_resource_id), status=ReconciliationStatus.ABSENT)
        if target.residual or FakeControl.DESTROY_RESIDUAL in self.controls:
            ids = (identity.provider_resource_id or "",)
            return ReconciliationFacts(**self._base(operation, Observation.OBSERVED_BAD, "residual resource remains after destroy", state=LifecycleState.RESIDUAL, resource_id=identity.provider_resource_id), status=ReconciliationStatus.RESIDUAL, resource_ids=ids, residual_resource_ids=ids)
        return ReconciliationFacts(**self._base(operation, Observation.OBSERVED_GOOD, "resource is present and uniquely reconciled", prior=target.state, state=target.state, resource_id=identity.provider_resource_id), status=ReconciliationStatus.PRESENT, resource_ids=(identity.provider_resource_id or "",))


# ---------------------------------------------------------------------------
# SDLC-L1 — head-bound one-use authority for the three live SSSF effect seams
#
# Three host recipes perform an irreversible, spending, or exposing effect:
# ``just/sandbox/lifecycle/teardown.just`` destroys a VM,
# ``just/sandbox/lifecycle/create.just`` mints a spending runtime key, and
# ``just/sandbox/lifecycle/observe.just`` publishes a sandbox anonymously.
# Before this section they consumed ORDERING — "the harvest step ran", "the
# provisioning key is in the environment", "control reached this line" — and
# never a typed authority.
#
# control #36 LAW_1: *repository landing authorization must not be reused as
# configuration-mutation authority*.  That is enforced structurally rather than
# by convention.  An effect authority is signed over bytes that begin with
# ``EFFECT_AUTHORITY_DOMAIN`` and carries that domain in its own document.  A
# repository landing authorization belongs to a different purpose domain, so it
# can neither be parsed as an effect authority nor produce a verifying
# authenticator for one, and no code path widens one into the other.
#
# The trust boundary is stated plainly: the host owns the signing material, so
# this is not a defence against a compromised host.  What it does own are the
# four properties the law names — authority is derived only from positively
# observed obligations, bound to an exact repository/head/target, spendable
# once, and completed only after the terminal state is authoritatively
# observed.  Absence of a token, an environment marker, a flag, or a prose
# marker is never approval.


EFFECT_AUTHORITY_DOMAIN = "sssf-sandbox-effect-authority/v1"

# The maximum spend ceiling a runtime-key mint may be authorized for.  A
# requested ceiling above this is an observed contradiction, not a CNO.
RUNTIME_KEY_SPEND_CEILING_USD = 500.0


class EffectClass(str, Enum):
    """The closed set of live seam effects that require typed authority.

    Repository landing and publication are deliberately absent: they are a
    different purpose domain and LAW_1 forbids reusing one as the other.
    """

    DESTROY = "destroy-only"
    RUNTIME_KEY_MINT = "runtime-key-mint-only"
    PUBLIC_EXPOSURE = "public-exposure-only"


class EffectNotAuthorized(RuntimeError):
    """A positively observed refusal: the effect must not run."""


class EffectStateUnobservable(RuntimeError):
    """The authority state could not be observed; this is CNO, never a pass."""


def _parameter(value: str, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 256
        or "\x00" in value
        or "\n" in value
        or "\r" in value
    ):
        raise ValueError(f"{label} must be a bounded single-line value")


@dataclass(frozen=True, slots=True)
class EffectSubject:
    """The exact repository, head, and target one effect is authorized against.

    ``repository`` and ``head_commit`` are the SSSF head the effect is
    authorized at; ``resource_id`` and ``parameters`` are the concrete target
    and its bounded configuration.  All four are compared exactly at the
    pre-effect gate, so a stale head, a foreign repository, another VM, or a
    widened spend ceiling can never satisfy an authority minted for this one.
    """

    run_id: str
    effect_class: EffectClass
    repository: str
    head_commit: str
    resource_id: str
    parameters: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _token(self.run_id, "effect subject run_id")
        if not isinstance(self.effect_class, EffectClass):
            raise ValueError("effect class must be a closed EffectClass member")
        if not isinstance(self.repository, str) or not self.repository.startswith("https://"):
            raise ValueError("effect subject repository must be an HTTPS URL")
        _nonempty(self.repository, "effect subject repository")
        _sha(self.head_commit, "effect subject head_commit")
        _token(self.resource_id, "effect subject resource_id")
        parameters = tuple((str(name), str(value)) for name, value in self.parameters)
        names = tuple(name for name, _ in parameters)
        if len(set(names)) != len(names):
            raise ValueError("effect subject parameters must be duplicate-free")
        if names != tuple(sorted(names)):
            raise ValueError("effect subject parameters must be sorted")
        for name, value in parameters:
            _token(name, "effect parameter name")
            _parameter(value, f"effect parameter {name}")
        object.__setattr__(self, "parameters", parameters)

    def to_document(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "effect_class": self.effect_class.value,
            "repository": self.repository,
            "head_commit": self.head_commit,
            "resource_id": self.resource_id,
            "parameters": [list(pair) for pair in self.parameters],
        }

    @classmethod
    def from_document(cls, document: Mapping[str, object]) -> "EffectSubject":
        try:
            effect_class = EffectClass(str(document["effect_class"]))
            parameters = tuple(
                (str(pair[0]), str(pair[1])) for pair in document.get("parameters") or ()
            )
            return cls(
                run_id=str(document["run_id"]),
                effect_class=effect_class,
                repository=str(document["repository"]),
                head_commit=str(document["head_commit"]),
                resource_id=str(document["resource_id"]),
                parameters=parameters,
            )
        except (KeyError, TypeError, IndexError, ValueError) as exc:
            raise EffectNotAuthorized(f"effect subject is not a closed subject: {exc}") from exc

    @property
    def digest(self) -> str:
        raw = json.dumps(self.to_document(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def mismatch(self, observed: "EffectSubject") -> str:
        """Name the first field that differs, or an empty string when bound."""
        for field_name in ("run_id", "effect_class", "repository", "head_commit", "resource_id"):
            mine = getattr(self, field_name)
            theirs = getattr(observed, field_name)
            if mine != theirs:
                return f"{field_name}: authorized {mine!r}, observed {theirs!r}"
        if self.parameters != observed.parameters:
            return f"parameters: authorized {self.parameters!r}, observed {observed.parameters!r}"
        return ""


@dataclass(frozen=True, slots=True)
class EffectAuthorization:
    """A one-use capability for exactly one effect at exactly one head."""

    authorization_id: str
    subject: EffectSubject
    obligations_digest: str
    issued_at: str
    authenticator: str
    purpose_domain: str = EFFECT_AUTHORITY_DOMAIN

    def __post_init__(self) -> None:
        _digest(self.authorization_id, "effect authorization_id")
        if not isinstance(self.subject, EffectSubject):
            raise ValueError("effect authorization subject is required")
        _digest(self.obligations_digest, "effect obligations_digest")
        _timestamp(self.issued_at, "effect authorization issued_at")
        _digest(self.authenticator, "effect authorization authenticator")
        # LAW_1, enforced in the type: only this purpose domain exists here, so a
        # repository landing authorization cannot be presented as effect
        # authority even when its other fields would otherwise line up.
        if self.purpose_domain != EFFECT_AUTHORITY_DOMAIN:
            raise ValueError(
                "effect authority purpose domain is closed; a repository landing "
                "authorization is never configuration-mutation authority"
            )

    def to_document(self) -> dict[str, object]:
        return {
            "purpose_domain": self.purpose_domain,
            "authorization_id": self.authorization_id,
            "subject": self.subject.to_document(),
            "obligations_digest": self.obligations_digest,
            "issued_at": self.issued_at,
            "authenticator": self.authenticator,
        }

    @classmethod
    def from_document(cls, document: Mapping[str, object]) -> "EffectAuthorization":
        if not isinstance(document, Mapping):
            raise EffectNotAuthorized("effect authorization document is not an object")
        domain = document.get("purpose_domain")
        if domain != EFFECT_AUTHORITY_DOMAIN:
            raise EffectNotAuthorized(
                f"purpose domain {domain!r} is not {EFFECT_AUTHORITY_DOMAIN!r}: a repository "
                "landing authorization is never configuration-mutation authority"
            )
        subject_document = document.get("subject")
        if not isinstance(subject_document, Mapping):
            raise EffectNotAuthorized("effect authorization has no closed subject")
        try:
            return cls(
                authorization_id=str(document["authorization_id"]),
                subject=EffectSubject.from_document(subject_document),
                obligations_digest=str(document["obligations_digest"]),
                issued_at=str(document["issued_at"]),
                authenticator=str(document["authenticator"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise EffectNotAuthorized(f"effect authorization is malformed: {exc}") from exc


def _effect_authorization_payload(authorization: EffectAuthorization) -> bytes:
    document = {
        "purpose_domain": authorization.purpose_domain,
        "authorization_id": authorization.authorization_id,
        "subject": authorization.subject.to_document(),
        "obligations_digest": authorization.obligations_digest,
        "issued_at": authorization.issued_at,
    }
    # The domain prefix is inside the signed bytes, so an authenticator minted
    # for any other purpose domain cannot verify here.
    return (
        EFFECT_AUTHORITY_DOMAIN.encode()
        + b"|"
        + json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    )


def _effect_authorization_fingerprint(authorization: EffectAuthorization) -> str:
    return hashlib.sha256(
        _effect_authorization_payload(authorization) + b"|" + authorization.authenticator.encode()
    ).hexdigest()


class JsonFileAuthorizationStateStore:
    """Durable one-use authorization state for the host effect seams.

    This is a host state file beside the existing per-run records, never a
    second lifecycle or trace database: it holds only authorization identity,
    provenance fingerprint, and ``issued``/``reserved``/``completed`` status.
    Every read that cannot reach the predicate raises
    :class:`EffectStateUnobservable`, which the callers report as
    could-not-observe rather than narrowing into a pass.
    """

    _STATUSES = ("issued", "reserved", "completed")

    def __init__(self, path: "Path | str", *, lock_timeout_seconds: float = 10.0) -> None:
        self._path = Path(path)
        self._lock_path = self._path.with_name(self._path.name + ".lock")
        self._lock_timeout = float(lock_timeout_seconds)
        self._thread_lock = threading.Lock()

    @property
    def path(self) -> Path:
        return self._path

    def _acquire(self) -> None:
        deadline = time.monotonic() + self._lock_timeout
        while True:
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                handle = os.open(self._lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                if time.monotonic() >= deadline:
                    try:
                        age = time.time() - os.stat(self._lock_path).st_mtime
                    except OSError as exc:
                        raise EffectStateUnobservable(f"authority lock unreadable: {exc}") from exc
                    if age > max(60.0, self._lock_timeout * 6):
                        # A lock older than any legitimate critical section is
                        # a crashed writer, not a live one.
                        try:
                            os.unlink(self._lock_path)
                        except OSError as exc:
                            raise EffectStateUnobservable(
                                f"stale authority lock could not be cleared: {exc}"
                            ) from exc
                        deadline = time.monotonic() + self._lock_timeout
                        continue
                    raise EffectStateUnobservable(
                        f"authority state lock held for more than {self._lock_timeout}s"
                    )
                time.sleep(0.02)
                continue
            except OSError as exc:
                raise EffectStateUnobservable(f"authority lock unavailable: {exc}") from exc
            os.close(handle)
            return

    def _release(self) -> None:
        try:
            os.unlink(self._lock_path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise EffectStateUnobservable(f"authority lock could not be released: {exc}") from exc

    @contextmanager
    def _exclusive(self) -> "Iterator[MutableMapping[str, MutableMapping[str, str]]]":
        with self._thread_lock:
            self._acquire()
            try:
                state = self._read()
                yield state
            finally:
                self._release()

    def _read(self) -> MutableMapping[str, MutableMapping[str, str]]:
        try:
            raw = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {}
        except (OSError, UnicodeError) as exc:
            raise EffectStateUnobservable(f"authority state unreadable: {exc}") from exc
        try:
            document = json.loads(raw)
        except ValueError as exc:
            raise EffectStateUnobservable(f"authority state is not readable JSON: {exc}") from exc
        if not isinstance(document, dict):
            raise EffectStateUnobservable("authority state is not an object")
        state: MutableMapping[str, MutableMapping[str, str]] = {}
        for authorization_id, item in document.items():
            if (
                not isinstance(item, dict)
                or item.get("status") not in self._STATUSES
                or not isinstance(item.get("fingerprint"), str)
            ):
                raise EffectStateUnobservable(
                    f"authority state entry {authorization_id!r} is not a closed record"
                )
            state[str(authorization_id)] = {
                "fingerprint": str(item["fingerprint"]),
                "status": str(item["status"]),
            }
        return state

    def _write(self, state: Mapping[str, Mapping[str, str]]) -> None:
        rendered = json.dumps(state, sort_keys=True, indent=2) + "\n"
        temporary = self._path.with_name(self._path.name + ".tmp")
        try:
            handle = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                stream.write(rendered)
            os.replace(temporary, self._path)
        except OSError as exc:
            raise EffectStateUnobservable(f"authority state could not be written: {exc}") from exc

    def record_issuance(self, authorization_id: str, fingerprint: str) -> None:
        _digest(authorization_id, "authorization_id")
        _digest(fingerprint, "authorization fingerprint")
        with self._exclusive() as state:
            existing = state.get(authorization_id)
            if existing is not None and existing["fingerprint"] != fingerprint:
                raise EffectNotAuthorized(
                    "authorization identity was reissued with different provenance"
                )
            if existing is None:
                state[authorization_id] = {"fingerprint": fingerprint, "status": "issued"}
                self._write(state)

    def verifies(self, authorization_id: str, fingerprint: str) -> bool:
        with self._exclusive() as state:
            item = state.get(authorization_id)
            return item is not None and hmac.compare_digest(item["fingerprint"], fingerprint)

    def reserved(self, authorization_id: str) -> bool:
        with self._exclusive() as state:
            item = state.get(authorization_id)
            return item is not None and item["status"] == "reserved"

    def completed(self, authorization_id: str) -> bool:
        with self._exclusive() as state:
            item = state.get(authorization_id)
            return item is not None and item["status"] == "completed"

    def compare_and_swap_reserved(self, authorization_id: str, fingerprint: str) -> bool:
        with self._exclusive() as state:
            item = state.get(authorization_id)
            if (
                item is None
                or item["status"] == "completed"
                or not hmac.compare_digest(item["fingerprint"], fingerprint)
            ):
                return False
            item["status"] = "reserved"
            self._write(state)
            return True

    def compare_and_swap_completed(self, authorization_id: str, fingerprint: str) -> bool:
        with self._exclusive() as state:
            item = state.get(authorization_id)
            if (
                item is None
                or item["status"] != "reserved"
                or not hmac.compare_digest(item["fingerprint"], fingerprint)
            ):
                return False
            item["status"] = "completed"
            self._write(state)
            return True


class EffectAuthorizationIssuer:
    """SSSF-only signing capability for effect authority.

    It is never a landing authority and never crosses to a provider or a guest.
    """

    def __init__(self, signing_key: bytes, state_store: DestroyAuthorizationStateStore) -> None:
        if not isinstance(signing_key, bytes) or len(signing_key) < 32:
            raise ValueError("effect authority signing key must contain at least 32 bytes")
        self.__signing_key = signing_key
        self.__state_store = state_store

    def _mint(self, authorization: EffectAuthorization) -> EffectAuthorization:
        authenticator = hmac.new(
            self.__signing_key,
            _effect_authorization_payload(authorization),
            hashlib.sha256,
        ).hexdigest()
        minted = replace(authorization, authenticator=authenticator)
        self.__state_store.record_issuance(
            minted.authorization_id,
            _effect_authorization_fingerprint(minted),
        )
        return minted


class EffectAuthorizationVerifier:
    """Gate-facing verification, reservation, and completion capability."""

    def __init__(self, state_store: DestroyAuthorizationStateStore) -> None:
        self.__state_store = state_store

    def verifies(self, authorization: EffectAuthorization) -> bool:
        return self.__state_store.verifies(
            authorization.authorization_id,
            _effect_authorization_fingerprint(authorization),
        )

    def reserved(self, authorization: EffectAuthorization) -> bool:
        return self.__state_store.reserved(authorization.authorization_id)

    def completed(self, authorization: EffectAuthorization) -> bool:
        return self.__state_store.completed(authorization.authorization_id)

    def reserve(self, authorization: EffectAuthorization) -> bool:
        return self.__state_store.compare_and_swap_reserved(
            authorization.authorization_id,
            _effect_authorization_fingerprint(authorization),
        )

    def complete(self, authorization: EffectAuthorization) -> bool:
        return self.__state_store.compare_and_swap_completed(
            authorization.authorization_id,
            _effect_authorization_fingerprint(authorization),
        )


@dataclass(frozen=True, slots=True)
class EffectGateResult:
    """A closed three-valued gate answer; never a boolean."""

    observation: Observation
    reason: str
    authorization_id: str = ""

    @property
    def permitted(self) -> bool:
        return self.observation is Observation.OBSERVED_GOOD


def issue_effect_authorization(
    subject: EffectSubject,
    *,
    obligations: Sequence[OutcomeCheck],
    authorization_issuer: EffectAuthorizationIssuer,
    issued_at: str,
) -> EffectAuthorization:
    """Mint one-use effect authority only from positively observed obligations.

    A zero-observation fold is CNO, so an empty obligation list — the shape an
    environment marker or a prose flag reduces to — can never mint authority.
    """
    if not isinstance(authorization_issuer, EffectAuthorizationIssuer):
        raise EffectNotAuthorized("effect authority requires the SSSF-only issuer")
    if not isinstance(subject, EffectSubject):
        raise EffectNotAuthorized("effect authority requires a closed subject")
    checks = tuple(obligations)
    folded = fold_aggregate(evidence=checks)
    if folded.status is not Observation.OBSERVED_GOOD:
        raise EffectNotAuthorized(
            f"effect obligations are not observed-good ({folded.status.value}): {folded.reason}"
        )
    if subject.effect_class is EffectClass.RUNTIME_KEY_MINT:
        ceiling = dict(subject.parameters).get("spend_limit_usd", "")
        try:
            requested = float(ceiling)
        except (TypeError, ValueError) as exc:
            raise EffectNotAuthorized(
                "runtime-key mint authority requires a numeric spend_limit_usd parameter"
            ) from exc
        if not 0 < requested <= RUNTIME_KEY_SPEND_CEILING_USD:
            raise EffectNotAuthorized(
                f"requested spend ceiling {requested} is outside "
                f"(0, {RUNTIME_KEY_SPEND_CEILING_USD}]"
            )
    obligations_digest = _obligation_digest(checks)
    raw = "|".join(
        (
            EFFECT_AUTHORITY_DOMAIN,
            subject.digest,
            obligations_digest,
            issued_at,
        )
    )
    authorization = EffectAuthorization(
        authorization_id=hashlib.sha256(raw.encode()).hexdigest(),
        subject=subject,
        obligations_digest=obligations_digest,
        issued_at=issued_at,
        authenticator="0" * 64,
    )
    return authorization_issuer._mint(authorization)


def authorize_effect(
    presented: EffectAuthorization,
    observed_subject: EffectSubject,
    verifier: EffectAuthorizationVerifier,
) -> EffectGateResult:
    """The pre-effect gate.  Observed-good is the only value that permits.

    It reserves the capability, so the same authority cannot be spent twice.  A
    reservation that has not completed stays retryable, because a failure that
    precedes the side effect must not burn the capability.
    """
    if not isinstance(presented, EffectAuthorization):
        return EffectGateResult(Observation.OBSERVED_BAD, "no effect authority was presented")
    mismatch = presented.subject.mismatch(observed_subject)
    if mismatch:
        return EffectGateResult(
            Observation.OBSERVED_BAD,
            f"authority is bound to a different subject — {mismatch}",
            presented.authorization_id,
        )
    try:
        if not verifier.verifies(presented):
            return EffectGateResult(
                Observation.OBSERVED_BAD,
                "authority is fabricated, tampered, or unknown to the durable state store",
                presented.authorization_id,
            )
        if verifier.completed(presented):
            return EffectGateResult(
                Observation.OBSERVED_BAD,
                "one-use authority was already consumed",
                presented.authorization_id,
            )
        if not verifier.reserve(presented):
            return EffectGateResult(
                Observation.OBSERVED_BAD,
                "authority could not be reserved for this effect",
                presented.authorization_id,
            )
    except EffectStateUnobservable as exc:
        return EffectGateResult(
            Observation.COULD_NOT_OBSERVE, str(exc), presented.authorization_id
        )
    return EffectGateResult(
        Observation.OBSERVED_GOOD,
        "authority is authentic, exactly bound, and reserved for this effect",
        presented.authorization_id,
    )


def complete_effect(
    authorization: EffectAuthorization,
    post_effect: OutcomeCheck,
    verifier: EffectAuthorizationVerifier,
) -> EffectGateResult:
    """The post-effect gate.  Success is observed, never inferred.

    Only a positively observed terminal state consumes the capability.  A CNO
    or a contradiction leaves it reserved so the seam reconciles and retries
    instead of recording a destruction, a mint, or a publication it never saw.
    """
    folded = fold_aggregate(work=(post_effect,))
    if folded.status is not Observation.OBSERVED_GOOD:
        return EffectGateResult(
            folded.status,
            f"post-effect state was not authoritatively observed: {folded.reason}",
            authorization.authorization_id,
        )
    try:
        if not verifier.complete(authorization):
            return EffectGateResult(
                Observation.OBSERVED_BAD,
                "authority could not be completed; it was not reserved by this effect",
                authorization.authorization_id,
            )
    except EffectStateUnobservable as exc:
        return EffectGateResult(
            Observation.COULD_NOT_OBSERVE, str(exc), authorization.authorization_id
        )
    return EffectGateResult(
        Observation.OBSERVED_GOOD,
        "terminal state observed; one-use authority consumed",
        authorization.authorization_id,
    )


# ---------------------------------------------------------------------------
# The three live seams, their observed head, and the host CLI the recipes call


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUTHORITY_STATE = Path(".sandbox/effect-authority.state.json")
DEFAULT_AUTHORITY_SIGNING_KEY = Path(".sandbox/effect-authority.key")
GIT_TIMEOUT_SECONDS = float(os.environ.get("SSSF_CHILD_TIMEOUT_SECONDS", "30"))


@dataclass(frozen=True, slots=True)
class LiveEffectSeam:
    """One recipe whose effect line must sit inside the authority sandwich."""

    path: str
    effect_class: EffectClass
    effect_marker: str
    description: str

    @property
    def mint_marker(self) -> str:
        return f"sandbox_provider mint --effect {self.effect_class.value}"

    @property
    def gate_marker(self) -> str:
        return f"sandbox_provider gate --effect {self.effect_class.value}"

    @property
    def complete_marker(self) -> str:
        return "sandbox_provider complete"


LIVE_EFFECT_SEAMS: tuple[LiveEffectSeam, ...] = (
    LiveEffectSeam(
        path="just/sandbox/lifecycle/teardown.just",
        effect_class=EffectClass.DESTROY,
        effect_marker='ssh "${SSH_OPTS[@]}" exe.dev rm "$VM"',
        description="irreversible VM destruction",
    ),
    LiveEffectSeam(
        path="just/sandbox/lifecycle/create.just",
        effect_class=EffectClass.RUNTIME_KEY_MINT,
        effect_marker="https://openrouter.ai/api/v1/keys",
        description="spending runtime-key mint",
    ),
    LiveEffectSeam(
        path="just/sandbox/lifecycle/observe.just",
        effect_class=EffectClass.PUBLIC_EXPOSURE,
        effect_marker='ssh exe.dev share set-public "$VM"',
        description="anonymous public exposure",
    ),
)


def _normalized_repository(remote: str) -> str:
    """Project a Git remote onto the canonical HTTPS repository identity."""
    value = remote.strip()
    if value.startswith("https://"):
        return value
    if value.startswith("ssh://git@"):
        rest = value[len("ssh://git@"):]
        return "https://" + rest
    if value.startswith("git@") and ":" in value:
        host, _, path = value[len("git@"):].partition(":")
        return f"https://{host}/{path}"
    raise EffectStateUnobservable(f"repository remote {remote!r} has no HTTPS projection")


def observed_repository_head(root: "Path | None" = None) -> tuple[str, str]:
    """Observe the exact repository and head this effect is authorized at.

    A missing, unspawnable, or wedged ``git`` is could-not-observe, never a
    silently accepted authority (ruling 36/5421223592, the same observation
    boundary ``docs/validation/check_obs_query.py`` landed).
    """
    workdir = Path(root) if root is not None else REPOSITORY_ROOT

    def git(*args: str) -> str:
        try:
            completed = subprocess.run(
                ("git", *args),
                cwd=workdir,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=GIT_TIMEOUT_SECONDS,
            )
        except OSError as exc:
            raise EffectStateUnobservable(f"git is unavailable: {exc}") from exc
        except subprocess.TimeoutExpired as exc:
            raise EffectStateUnobservable(f"git timed out: git {' '.join(args)}") from exc
        if completed.returncode != 0:
            raise EffectStateUnobservable(
                f"git {' '.join(args)} exited {completed.returncode}: "
                f"{completed.stderr.strip() or 'no output'}"
            )
        return completed.stdout.strip()

    repository = _normalized_repository(git("config", "--get", "remote.origin.url"))
    head = git("rev-parse", "HEAD")
    if _SHA1.fullmatch(head) is None:
        raise EffectStateUnobservable(f"git HEAD {head!r} is not a full commit sha")
    return repository, head


def load_or_create_signing_key(path: "Path | str") -> bytes:
    """Read the host-owned effect signing material, creating it once if absent.

    Verification never needs this material — the durable store keeps the
    provenance fingerprint — so rotating or losing it cannot resurrect or
    invalidate an already reserved capability.
    """
    target = Path(path)
    try:
        material = target.read_bytes()
    except FileNotFoundError:
        material = b""
    except OSError as exc:
        raise EffectStateUnobservable(f"effect signing material unreadable: {exc}") from exc
    if len(material) >= 32:
        return material
    if material:
        raise EffectStateUnobservable("effect signing material is present but too short")
    minted = os.urandom(32)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        handle = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(handle, "wb") as stream:
            stream.write(minted)
    except FileExistsError:
        return load_or_create_signing_key(target)
    except OSError as exc:
        raise EffectStateUnobservable(f"effect signing material unwritable: {exc}") from exc
    return minted


def _parse_parameters(values: Sequence[str]) -> tuple[tuple[str, str], ...]:
    parsed: list[tuple[str, str]] = []
    for item in values:
        name, separator, value = item.partition("=")
        if not separator:
            raise EffectNotAuthorized(f"--param must be name=value, got {item!r}")
        parsed.append((name, value))
    return tuple(sorted(parsed))


def _parse_obligations(values: Sequence[str]) -> tuple[OutcomeCheck, ...]:
    """Parse ``NAME|observation|reason`` triples into typed observations.

    There is no shorthand that means "approved": every obligation carries one of
    the three closed observation values, and only observed-good contributes to
    a mint.
    """
    checks: list[OutcomeCheck] = []
    for item in values:
        parts = item.split("|", 2)
        if len(parts) < 2:
            raise EffectNotAuthorized(
                f"--obligation must be NAME|observation|reason, got {item!r}"
            )
        name, raw_observation = parts[0], parts[1]
        reason = parts[2] if len(parts) == 3 else "no reason supplied"
        try:
            observation = Observation(raw_observation)
        except ValueError as exc:
            raise EffectNotAuthorized(
                f"obligation {name!r} observation must be one of "
                f"{[value.value for value in Observation]}, got {raw_observation!r}"
            ) from exc
        checks.append(OutcomeCheck(name, observation, reason=reason))
    return tuple(checks)


def _subject_from_arguments(arguments: object) -> EffectSubject:
    repository = getattr(arguments, "repository", None)
    head = getattr(arguments, "head", None)
    if not repository or not head:
        observed_repository, observed_head = observed_repository_head(
            getattr(arguments, "root", None)
        )
        repository = repository or observed_repository
        head = head or observed_head
    return EffectSubject(
        run_id=arguments.run_id,
        effect_class=EffectClass(arguments.effect),
        repository=repository,
        head_commit=head,
        resource_id=arguments.resource,
        parameters=_parse_parameters(arguments.param),
    )


def _read_authorization(path: "Path | str") -> EffectAuthorization:
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise EffectNotAuthorized(
            f"no effect authority at {path}: absence is never approval"
        ) from exc
    except (OSError, UnicodeError) as exc:
        raise EffectStateUnobservable(f"effect authority unreadable: {exc}") from exc
    try:
        document = json.loads(raw)
    except ValueError as exc:
        raise EffectNotAuthorized(f"effect authority is not readable JSON: {exc}") from exc
    return EffectAuthorization.from_document(document)


# ---------------------------------------------------------------------------
# Watched-red controls for the four LAW_1 acceptance properties
#
# Each control positively manufactures the defect the law names and asserts a
# typed refusal, and each is paired with a non-vacuity case proving the same
# gate still admits the correct input.  A control that cannot reach its subject
# reports could-not-observe; it never reports a pass by absence.


_CONTROL_REPOSITORY = "https://example.invalid/sssf-effect-controls.git"
_CONTROL_HEAD = "a" * 40
_CONTROL_OTHER_HEAD = "b" * 40
_CONTROL_ISSUED_AT = "1970-01-01T00:00:00Z"
_CONTROL_ENVIRONMENT_MARKERS = {
    "SBX_EFFECT_APPROVED": "1",
    "SSSF_EFFECT_AUTHORIZED": "yes",
    "TEARDOWN_APPROVED": "true",
}


def _control_check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _control_subject(
    effect_class: EffectClass = EffectClass.DESTROY,
    **overrides: object,
) -> EffectSubject:
    fields: dict[str, object] = {
        "run_id": "ctl-run-1",
        "effect_class": effect_class,
        "repository": _CONTROL_REPOSITORY,
        "head_commit": _CONTROL_HEAD,
        "resource_id": "ctl-vm-1",
        "parameters": (),
    }
    fields.update(overrides)
    return EffectSubject(**fields)  # type: ignore[arg-type]


def _control_obligations() -> tuple[OutcomeCheck, ...]:
    return (
        OutcomeCheck("commits-harvested", Observation.OBSERVED_GOOD, reason="bundle written"),
        OutcomeCheck("runtime-key-retired", Observation.OBSERVED_GOOD, reason="DELETE returned 200"),
    )


def _control_authority(directory: Path, name: str = "state.json") -> tuple[
    JsonFileAuthorizationStateStore, EffectAuthorizationIssuer, EffectAuthorizationVerifier
]:
    store = JsonFileAuthorizationStateStore(directory / name)
    issuer = EffectAuthorizationIssuer(b"control-signing-material-32-bytes", store)
    return store, issuer, EffectAuthorizationVerifier(store)


def marker_is_not_approval_controls(errors: list[str], executed: list[str]) -> None:
    """Watched red: an env var or prose marker treated as approval for a head-bound effect."""
    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        _store, issuer, verifier = _control_authority(directory)
        subject = _control_subject()

        executed.append("marker/empty-obligation-set-cannot-mint")
        try:
            issue_effect_authorization(
                subject, obligations=(), authorization_issuer=issuer, issued_at=_CONTROL_ISSUED_AT
            )
        except EffectNotAuthorized:
            pass
        else:
            errors.append("an empty obligation set minted effect authority")

        executed.append("marker/could-not-observe-obligation-cannot-mint")
        try:
            issue_effect_authorization(
                subject,
                obligations=(
                    OutcomeCheck("commits-harvested", Observation.OBSERVED_GOOD, reason="ok"),
                    OutcomeCheck(
                        "runtime-key-retired",
                        Observation.COULD_NOT_OBSERVE,
                        reason="provisioning list unreadable",
                    ),
                ),
                authorization_issuer=issuer,
                issued_at=_CONTROL_ISSUED_AT,
            )
        except EffectNotAuthorized:
            pass
        else:
            errors.append("a could-not-observe obligation minted effect authority")

        executed.append("marker/absent-authority-is-not-approval")
        try:
            _read_authorization(directory / "does-not-exist.json")
        except EffectNotAuthorized:
            pass
        except EffectStateUnobservable:
            errors.append("an absent effect authority was reported as unobservable, not refused")
        else:
            errors.append("an absent effect authority was accepted")

        executed.append("marker/prose-marker-file-is-not-approval")
        prose = directory / "approved.txt"
        prose.write_text("APPROVED BY THE OPERATOR — destroy is fine\n", encoding="utf-8")
        try:
            _read_authorization(prose)
        except EffectNotAuthorized:
            pass
        else:
            errors.append("a prose approval marker was accepted as effect authority")

        executed.append("marker/hand-written-unsigned-token-is-refused")
        forged = EffectAuthorization(
            authorization_id="c" * 64,
            subject=subject,
            obligations_digest="d" * 64,
            issued_at=_CONTROL_ISSUED_AT,
            authenticator="0" * 64,
        )
        forged_result = authorize_effect(forged, subject, verifier)
        _control_check(
            forged_result.observation is Observation.OBSERVED_BAD,
            "a hand-written unsigned effect authority was not refused",
            errors,
        )

        executed.append("marker/environment-markers-do-not-approve")
        preserved = {name: os.environ.get(name) for name in _CONTROL_ENVIRONMENT_MARKERS}
        try:
            os.environ.update(_CONTROL_ENVIRONMENT_MARKERS)
            still_refused = authorize_effect(forged, subject, verifier)
            _control_check(
                still_refused.observation is Observation.OBSERVED_BAD,
                "environment approval markers admitted an unsigned effect authority",
                errors,
            )
            # Non-vacuity, with the same markers still set: a properly minted
            # authority is admitted, so the refusal above is the token's doing
            # and not an unconditional deny.
            executed.append("marker/non-vacuity-minted-authority-is-admitted")
            minted = issue_effect_authorization(
                subject,
                obligations=_control_obligations(),
                authorization_issuer=issuer,
                issued_at=_CONTROL_ISSUED_AT,
            )
            admitted = authorize_effect(minted, subject, verifier)
            _control_check(
                admitted.observation is Observation.OBSERVED_GOOD,
                f"a correctly minted effect authority was refused: {admitted.reason}",
                errors,
            )
        finally:
            for name, value in preserved.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value


def landing_authority_is_not_effect_authority_controls(
    errors: list[str], executed: list[str]
) -> None:
    """LAW_1: repository landing authority is never configuration-mutation authority."""
    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        _store, issuer, verifier = _control_authority(directory)
        subject = _control_subject()
        minted = issue_effect_authorization(
            subject,
            obligations=_control_obligations(),
            authorization_issuer=issuer,
            issued_at=_CONTROL_ISSUED_AT,
        )

        executed.append("law1/foreign-purpose-domain-is-refused")
        landing_document = minted.to_document()
        landing_document["purpose_domain"] = "repository-landing/example"
        try:
            EffectAuthorization.from_document(landing_document)
        except EffectNotAuthorized as exc:
            _control_check(
                "repository landing authorization is never configuration-mutation authority"
                in str(exc),
                "the foreign purpose domain refusal did not name LAW_1",
                errors,
            )
        else:
            errors.append("a repository landing purpose domain was parsed as effect authority")

        executed.append("law1/domain-separated-signature-does-not-verify")
        payload = _effect_authorization_payload(minted)
        _control_check(
            payload.startswith(EFFECT_AUTHORITY_DOMAIN.encode() + b"|"),
            "the effect authority payload is not domain separated",
            errors,
        )
        landing_authenticator = hmac.new(
            b"control-signing-material-32-bytes",
            b"repository-landing/example|" + payload.split(b"|", 1)[1],
            hashlib.sha256,
        ).hexdigest()
        _control_check(
            landing_authenticator != minted.authenticator,
            "a landing-domain signature collided with the effect-domain signature",
            errors,
        )
        landing_signed = replace(minted, authenticator=landing_authenticator)
        _control_check(
            not verifier.verifies(landing_signed),
            "an authenticator minted under a landing domain verified as effect authority",
            errors,
        )

        executed.append("law1/effect-class-vocabulary-excludes-landing")
        _control_check(
            {member.value for member in EffectClass}
            == {"destroy-only", "runtime-key-mint-only", "public-exposure-only"},
            "the effect class vocabulary is not the closed three-effect set",
            errors,
        )


def stale_subject_controls(errors: list[str], executed: list[str]) -> None:
    """Watched red: a stale or wrong repository/head/target authority admitted."""
    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        _store, issuer, verifier = _control_authority(directory)
        subject = _control_subject(
            effect_class=EffectClass.RUNTIME_KEY_MINT,
            resource_id="sbx-ctl-run-1",
            parameters=(("spend_limit_usd", "50.00"),),
        )
        minted = issue_effect_authorization(
            subject,
            obligations=_control_obligations(),
            authorization_issuer=issuer,
            issued_at=_CONTROL_ISSUED_AT,
        )
        wrong_subjects = (
            (replace(subject, head_commit=_CONTROL_OTHER_HEAD), "head_commit", "stale head"),
            (
                replace(subject, repository="https://example.invalid/other.git"),
                "repository",
                "foreign repository",
            ),
            (replace(subject, resource_id="sbx-other-run"), "resource_id", "another target"),
            (replace(subject, run_id="ctl-run-2"), "run_id", "another run"),
            (
                replace(subject, parameters=(("spend_limit_usd", "500.00"),)),
                "parameters",
                "a widened spend ceiling",
            ),
        )
        for observed, field_name, label in wrong_subjects:
            executed.append(f"stale/{field_name}")
            result = authorize_effect(minted, observed, verifier)
            _control_check(
                result.observation is Observation.OBSERVED_BAD,
                f"the pre-effect gate admitted {label}",
                errors,
            )
            _control_check(
                field_name in result.reason,
                f"the refusal for {label} did not name {field_name}",
                errors,
            )

        executed.append("stale/non-vacuity-exact-subject-is-admitted")
        exact = authorize_effect(minted, subject, verifier)
        _control_check(
            exact.observation is Observation.OBSERVED_GOOD,
            f"the exactly bound subject was refused: {exact.reason}",
            errors,
        )

        executed.append("stale/spend-ceiling-above-the-bound-cannot-mint")
        try:
            issue_effect_authorization(
                replace(
                    subject,
                    parameters=(("spend_limit_usd", str(RUNTIME_KEY_SPEND_CEILING_USD + 1)),),
                ),
                obligations=_control_obligations(),
                authorization_issuer=issuer,
                issued_at=_CONTROL_ISSUED_AT,
            )
        except EffectNotAuthorized:
            pass
        else:
            errors.append("a spend ceiling above the authorized bound minted authority")


def one_use_controls(errors: list[str], executed: list[str]) -> None:
    """Watched red: a one-use authority reused after consumption."""
    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        _store, issuer, verifier = _control_authority(directory)
        subject = _control_subject()
        minted = issue_effect_authorization(
            subject,
            obligations=_control_obligations(),
            authorization_issuer=issuer,
            issued_at=_CONTROL_ISSUED_AT,
        )

        executed.append("one-use/first-reservation-is-admitted")
        first = authorize_effect(minted, subject, verifier)
        _control_check(
            first.observation is Observation.OBSERVED_GOOD,
            f"the first use of a one-use authority was refused: {first.reason}",
            errors,
        )

        executed.append("one-use/reservation-is-retryable-before-the-effect")
        retry = authorize_effect(minted, subject, verifier)
        _control_check(
            retry.observation is Observation.OBSERVED_GOOD,
            "a reservation that never reached its effect was not retryable",
            errors,
        )

        executed.append("one-use/consumed-authority-is-refused")
        consumed = complete_effect(
            minted,
            OutcomeCheck("vm-absent", Observation.OBSERVED_GOOD, reason="control plane lists no VM"),
            verifier,
        )
        _control_check(
            consumed.observation is Observation.OBSERVED_GOOD,
            f"an authoritatively observed terminal state did not consume the authority: {consumed.reason}",
            errors,
        )
        replayed = authorize_effect(minted, subject, verifier)
        _control_check(
            replayed.observation is Observation.OBSERVED_BAD,
            "a one-use authority was admitted again after consumption",
            errors,
        )
        _control_check(
            "already consumed" in replayed.reason,
            "the replay refusal did not name prior consumption",
            errors,
        )

        executed.append("one-use/non-vacuity-a-fresh-authority-still-mints")
        fresh = issue_effect_authorization(
            subject,
            obligations=_control_obligations(),
            authorization_issuer=issuer,
            issued_at="1970-01-01T00:00:01Z",
        )
        _control_check(
            fresh.authorization_id != minted.authorization_id,
            "a second mint reused the consumed authorization identity",
            errors,
        )
        _control_check(
            authorize_effect(fresh, subject, verifier).observation is Observation.OBSERVED_GOOD,
            "a freshly minted authority was refused after an earlier one was consumed",
            errors,
        )


def post_effect_observation_controls(errors: list[str], executed: list[str]) -> None:
    """Watched red: post-effect success inferred without authoritative observation."""
    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        _store, issuer, verifier = _control_authority(directory)
        subject = _control_subject()

        for observation, label in (
            (Observation.COULD_NOT_OBSERVE, "an unreadable control-plane listing"),
            (Observation.OBSERVED_BAD, "an observed residual resource"),
        ):
            executed.append(f"post-effect/{observation.value}-does-not-complete")
            minted = issue_effect_authorization(
                subject,
                obligations=_control_obligations(),
                authorization_issuer=issuer,
                issued_at=f"1970-01-01T00:00:0{2 if observation is Observation.OBSERVED_BAD else 3}Z",
            )
            authorize_effect(minted, subject, verifier)
            result = complete_effect(
                minted,
                OutcomeCheck("vm-absent", observation, reason=label),
                verifier,
            )
            _control_check(
                result.observation is observation,
                f"{label} did not preserve its own observation value",
                errors,
            )
            _control_check(
                not verifier.completed(minted),
                f"{label} was inferred as post-effect success",
                errors,
            )
            _control_check(
                verifier.reserved(minted),
                f"{label} lost the reservation instead of preserving it for reconciliation",
                errors,
            )

        executed.append("post-effect/non-vacuity-observed-absence-completes")
        good = issue_effect_authorization(
            subject,
            obligations=_control_obligations(),
            authorization_issuer=issuer,
            issued_at="1970-01-01T00:00:04Z",
        )
        authorize_effect(good, subject, verifier)
        completed = complete_effect(
            good,
            OutcomeCheck("vm-absent", Observation.OBSERVED_GOOD, reason="control plane lists no VM"),
            verifier,
        )
        _control_check(
            completed.observation is Observation.OBSERVED_GOOD and verifier.completed(good),
            f"an authoritatively observed terminal state did not complete: {completed.reason}",
            errors,
        )


def pre_effect_gate_blocks_controls(errors: list[str], executed: list[str]) -> None:
    """ROADMAP.md:980 — a fixture pre-effect gate proves stale/wrong/missing authority blocks."""
    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        _store, issuer, verifier = _control_authority(directory)
        subject = _control_subject(
            effect_class=EffectClass.PUBLIC_EXPOSURE,
            parameters=(("port", "4501"), ("visibility", "public")),
        )
        ran: list[str] = []

        def guarded_effect(
            presented: EffectAuthorization | None, observed: EffectSubject
        ) -> EffectGateResult:
            if presented is None:
                return EffectGateResult(Observation.OBSERVED_BAD, "no authority was presented")
            gate = authorize_effect(presented, observed, verifier)
            if not gate.permitted:
                return gate
            ran.append(observed.resource_id)
            return gate

        minted = issue_effect_authorization(
            subject,
            obligations=(
                OutcomeCheck("app-port-listening", Observation.OBSERVED_GOOD, reason=":4501 bound"),
                OutcomeCheck(
                    "single-anonymous-port", Observation.OBSERVED_GOOD, reason="only 4501 is public"
                ),
            ),
            authorization_issuer=issuer,
            issued_at=_CONTROL_ISSUED_AT,
        )
        blocked_cases = (
            (None, subject, "missing authority"),
            (minted, replace(subject, head_commit=_CONTROL_OTHER_HEAD), "stale head"),
            (minted, replace(subject, resource_id="ctl-vm-2"), "wrong target"),
            (
                minted,
                replace(subject, parameters=(("port", "9999"), ("visibility", "public"))),
                "wrong exposure parameters",
            ),
        )
        for presented, observed, label in blocked_cases:
            executed.append(f"pre-effect/{label.replace(' ', '-')}-blocks-before-effect")
            result = guarded_effect(presented, observed)
            _control_check(
                result.observation is Observation.OBSERVED_BAD,
                f"the fixture gate did not refuse {label}",
                errors,
            )
        _control_check(
            ran == [],
            f"the effect ran behind a refused gate: {ran}",
            errors,
        )

        executed.append("pre-effect/non-vacuity-bound-authority-runs-the-effect")
        permitted = guarded_effect(minted, subject)
        _control_check(
            permitted.observation is Observation.OBSERVED_GOOD and ran == [subject.resource_id],
            "the fixture gate blocked an exactly bound authority",
            errors,
        )


def seam_binding_controls(
    errors: list[str], executed: list[str], root: "Path | None" = None
) -> None:
    """Every live effect line sits between its mint/gate and its completion.

    An unreadable seam, or a seam whose named effect line is no longer present,
    is could-not-observe: the control refuses to report a pass it did not reach.
    """
    base = Path(root) if root is not None else REPOSITORY_ROOT
    for seam in LIVE_EFFECT_SEAMS:
        executed.append(f"seam/{seam.effect_class.value}")
        try:
            text = (base / seam.path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"could-not-observe: {seam.path} is unreadable: {exc}")
            continue
        effect_at = text.find(seam.effect_marker)
        if effect_at < 0:
            errors.append(
                f"could-not-observe: {seam.path} no longer contains the named "
                f"{seam.description} line {seam.effect_marker!r}"
            )
            continue
        mint_at = text.find(seam.mint_marker)
        gate_at = text.find(seam.gate_marker)
        complete_at = text.find(seam.complete_marker, effect_at)
        _control_check(
            0 <= mint_at < effect_at,
            f"{seam.path}: {seam.description} is not preceded by a typed authority mint",
            errors,
        )
        _control_check(
            0 <= gate_at < effect_at,
            f"{seam.path}: {seam.description} is not preceded by the pre-effect authority gate",
            errors,
        )
        _control_check(
            0 <= mint_at < gate_at,
            f"{seam.path}: the authority gate does not follow its mint",
            errors,
        )
        _control_check(
            complete_at > effect_at,
            f"{seam.path}: {seam.description} does not complete its one-use authority "
            "on an authoritative post-effect observation",
            errors,
        )


def effect_authority_controls(root: "Path | None" = None) -> tuple[list[str], list[str]]:
    """Run every LAW_1 watched red; return (errors, executed control names)."""
    errors: list[str] = []
    executed: list[str] = []
    marker_is_not_approval_controls(errors, executed)
    landing_authority_is_not_effect_authority_controls(errors, executed)
    stale_subject_controls(errors, executed)
    one_use_controls(errors, executed)
    post_effect_observation_controls(errors, executed)
    pre_effect_gate_blocks_controls(errors, executed)
    seam_binding_controls(errors, executed, root)
    return errors, executed


# ---------------------------------------------------------------------------
# Host CLI — the seam-facing entry point the three recipes call
#
#   python3 -m adws.adw_modules.sandbox_provider mint     --effect ... --out ...
#   python3 -m adws.adw_modules.sandbox_provider gate     --effect ... --authorization ...
#   python3 -m adws.adw_modules.sandbox_provider complete --authorization ... --observed ...
#   python3 -m adws.adw_modules.sandbox_provider controls
#
# Exit codes are the landed three-valued vocabulary from tools/ci_gate.py:
# 0 observed-good, 1 observed-bad, COULD_NOT_OBSERVE_EXIT could-not-observe.
# A caller must never read a nonzero exit as "the effect is fine to run".


def _observation_exit(observation: Observation) -> int:
    if observation is Observation.OBSERVED_GOOD:
        return 0
    if observation is Observation.COULD_NOT_OBSERVE:
        return COULD_NOT_OBSERVE_EXIT
    return 1


def _add_subject_arguments(parser: "argparse.ArgumentParser") -> None:
    parser.add_argument(
        "--effect",
        required=True,
        choices=[member.value for member in EffectClass],
        help="the closed effect class this authority is for",
    )
    parser.add_argument("--run-id", required=True, help="the run this effect belongs to")
    parser.add_argument(
        "--resource", required=True, help="the exact effect target (VM name, key name)"
    )
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="a bounded configuration binding compared exactly at the gate",
    )
    parser.add_argument(
        "--repository",
        default="",
        help="override the observed repository identity (fixtures and controls only)",
    )
    parser.add_argument(
        "--head",
        default="",
        help="override the observed head commit (fixtures and controls only)",
    )
    parser.add_argument("--root", default=None, help="repository root to observe the head in")


def _add_state_arguments(parser: "argparse.ArgumentParser") -> None:
    parser.add_argument(
        "--state",
        default=str(DEFAULT_AUTHORITY_STATE),
        help="durable one-use authorization state file",
    )


def _effect_parser() -> "argparse.ArgumentParser":
    parser = argparse.ArgumentParser(
        prog="python3 -m adws.adw_modules.sandbox_provider",
        description=(
            "Head-bound one-use authority for the live SSSF effect seams. "
            "Repository landing authorization is never configuration-mutation authority."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    mint = subparsers.add_parser("mint", help="mint one-use authority from observed obligations")
    _add_subject_arguments(mint)
    _add_state_arguments(mint)
    mint.add_argument(
        "--obligation",
        action="append",
        default=[],
        metavar="NAME|OBSERVATION|REASON",
        help="a typed pre-effect observation; only observed-good contributes",
    )
    mint.add_argument("--out", required=True, help="where to write the minted authority")
    mint.add_argument(
        "--signing-key",
        default=str(DEFAULT_AUTHORITY_SIGNING_KEY),
        help="host-owned effect signing material",
    )
    mint.add_argument("--issued-at", default="", help="issuance timestamp (defaults to now, UTC)")

    gate = subparsers.add_parser("gate", help="the pre-effect gate; reserves the capability")
    _add_subject_arguments(gate)
    _add_state_arguments(gate)
    gate.add_argument("--authorization", required=True, help="the authority to present")

    complete = subparsers.add_parser(
        "complete", help="consume the capability on an authoritative post-effect observation"
    )
    _add_state_arguments(complete)
    complete.add_argument("--authorization", required=True)
    complete.add_argument(
        "--observed",
        required=True,
        choices=[member.value for member in Observation],
        help="the post-effect terminal-state observation",
    )
    complete.add_argument("--name", default="post-effect-state")
    complete.add_argument("--reason", default="no reason supplied")

    inspect = subparsers.add_parser("inspect", help="read a verified reserved subject")
    _add_state_arguments(inspect)
    inspect.add_argument("--authorization", required=True)
    inspect.add_argument("--run-id", required=True)
    inspect.add_argument(
        "--effect", required=True, choices=[member.value for member in EffectClass]
    )

    controls = subparsers.add_parser(
        "controls", help="run the LAW_1 watched-red controls over the live seams"
    )
    controls.add_argument("--root", default=None, help="repository root to inspect")

    return parser


def _write_authorization(path: "Path | str", authorization: EffectAuthorization) -> None:
    target = Path(path)
    rendered = json.dumps(authorization.to_document(), sort_keys=True, indent=2) + "\n"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        handle = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(rendered)
    except OSError as exc:
        raise EffectStateUnobservable(f"effect authority could not be written: {exc}") from exc


def _run_controls_command(root: "str | None") -> int:
    errors, executed = effect_authority_controls(Path(root) if root else None)
    unobservable = [error for error in errors if error.startswith(CNO_REASON_PREFIX)]
    if unobservable:
        print("SDLC-L1 effect-seam authority controls: COULD-NOT-OBSERVE")
        for error in errors:
            print(f"- {error}")
        return COULD_NOT_OBSERVE_EXIT
    if errors:
        print("SDLC-L1 effect-seam authority controls: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("SDLC-L1 effect-seam authority controls: PASS")
    print(
        "law: control #36 LAW_1 — repository landing authorization is never "
        "configuration-mutation authority"
    )
    print(
        "bound seams: "
        + ", ".join(f"{seam.path} ({seam.description})" for seam in LIVE_EFFECT_SEAMS)
    )
    print("provider-calls: 0 (in-process controls; no exe.dev, OpenRouter, ssh, or network call)")
    print("watched-red: an environment or prose marker treated as approval for a head-bound effect")
    print("watched-red: a stale or wrong repository/head/target authority admitted")
    print("watched-red: a one-use authority reused after consumption")
    print("watched-red: post-effect success inferred without authoritative observation")
    print("positive control: an exactly bound, authentic, unconsumed authority is admitted")
    print(f"watched-red controls executed: {len(executed)}")
    return 0


def effect_cli(argv: "Sequence[str] | None" = None) -> int:
    """Seam-facing entry point.  Every answer is one of the three values."""
    arguments = _effect_parser().parse_args(list(argv) if argv is not None else None)

    if arguments.command == "controls":
        return _run_controls_command(arguments.root)

    try:
        if arguments.command == "mint":
            subject = _subject_from_arguments(arguments)
            issued_at = arguments.issued_at or datetime.now(timezone.utc).isoformat(
                timespec="microseconds"
            ).replace("+00:00", "Z")
            store = JsonFileAuthorizationStateStore(arguments.state)
            issuer = EffectAuthorizationIssuer(
                load_or_create_signing_key(arguments.signing_key), store
            )
            authorization = issue_effect_authorization(
                subject,
                obligations=_parse_obligations(arguments.obligation),
                authorization_issuer=issuer,
                issued_at=issued_at,
            )
            _write_authorization(arguments.out, authorization)
            print(
                f"authority: {subject.effect_class.value} for {subject.resource_id} "
                f"at {subject.head_commit[:12]} (id {authorization.authorization_id[:12]})"
            )
            return 0

        if arguments.command == "inspect":
            authorization = _read_authorization(arguments.authorization)
            store = JsonFileAuthorizationStateStore(arguments.state)
            verifier = EffectAuthorizationVerifier(store)
            if not verifier.verifies(authorization):
                raise EffectNotAuthorized(
                    "effect authority is fabricated, tampered, or unknown"
                )
            if not verifier.reserved(authorization):
                raise EffectNotAuthorized("effect authority is not reserved")
            if authorization.subject.run_id != arguments.run_id:
                raise EffectNotAuthorized("effect authority is bound to a different run")
            if authorization.subject.effect_class is not EffectClass(arguments.effect):
                raise EffectNotAuthorized("effect authority is bound to a different effect")
            print(authorization.subject.resource_id)
            return 0

        if arguments.command == "gate":
            authorization = _read_authorization(arguments.authorization)
            observed = _subject_from_arguments(arguments)
            store = JsonFileAuthorizationStateStore(arguments.state)
            result = authorize_effect(
                authorization, observed, EffectAuthorizationVerifier(store)
            )
        else:
            authorization = _read_authorization(arguments.authorization)
            store = JsonFileAuthorizationStateStore(arguments.state)
            result = complete_effect(
                authorization,
                OutcomeCheck(
                    arguments.name, Observation(arguments.observed), reason=arguments.reason
                ),
                EffectAuthorizationVerifier(store),
            )
    except EffectStateUnobservable as exc:
        print(f"{CNO_REASON_PREFIX}{exc}", file=sys.stderr)
        return COULD_NOT_OBSERVE_EXIT
    except (EffectNotAuthorized, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1

    stream = sys.stdout if result.observation is Observation.OBSERVED_GOOD else sys.stderr
    label = (
        "permitted"
        if result.observation is Observation.OBSERVED_GOOD
        else (
            CNO_REASON_PREFIX.rstrip()
            if result.observation is Observation.COULD_NOT_OBSERVE
            else "refused:"
        )
    )
    print(f"{label} {result.reason}", file=stream)
    return _observation_exit(result.observation)


__all__ = [
    "AggregateResult",
    "ArtifactExportFacts",
    "ArtifactInventoryItem",
    "ArtifactSpec",
    "authorize_effect",
    "CapabilityDisposition",
    "CapabilityFact",
    "CommandSpec",
    "complete_effect",
    "CopyFacts",
    "CopySpec",
    "CreateFacts",
    "DeferredCapability",
    "DestroyAuthorization",
    "DestroyAuthorizationIssuer",
    "DestroyAuthorizationStateStore",
    "DestroyAuthorizationVerifier",
    "DestroyFacts",
    "DestroyNotAuthorized",
    "effect_authority_controls",
    "EFFECT_AUTHORITY_DOMAIN",
    "effect_cli",
    "EffectAuthorization",
    "EffectAuthorizationIssuer",
    "EffectAuthorizationVerifier",
    "EffectClass",
    "EffectGateResult",
    "EffectNotAuthorized",
    "EffectStateUnobservable",
    "EffectSubject",
    "ExecFacts",
    "FactBase",
    "FakeControl",
    "FakeSandboxProvider",
    "fold_aggregate",
    "GitExportFacts",
    "GitExportSpec",
    "InMemoryDestroyAuthorizationStateStore",
    "InMemoryLifecycleRecordStore",
    "InputCopySpec",
    "InspectFacts",
    "InterruptTiming",
    "issue_destroy_authorization",
    "issue_effect_authorization",
    "JsonFileAuthorizationStateStore",
    "LifecycleBoundary",
    "LifecycleOperationRecord",
    "LifecycleRecordStore",
    "LifecycleState",
    "LIVE_EFFECT_SEAMS",
    "LiveEffectSeam",
    "load_or_create_signing_key",
    "Observation",
    "ObservationSummary",
    "observed_repository_head",
    "OperationFacts",
    "OperationKey",
    "OperationKind",
    "OutcomeCheck",
    "ProcessFacts",
    "PromotionAuthority",
    "QuiescenceDomain",
    "QuiescenceFact",
    "ReconciliationFacts",
    "ReconciliationStatus",
    "ResourceBounds",
    "RUNTIME_KEY_SPEND_CEILING_USD",
    "SandboxIdentity",
    "SandboxProvider",
    "SandboxSpec",
    "SandboxStateFacts",
    "SecretRetirementFacts",
    "SourceCopySpec",
    "SourceIdentity",
    "StdinPolicy",
    "StopFacts",
    "TimeoutClock",
    "validate_artifact_export",
    "validate_git_export",
    "WorkspaceMode",
]


if __name__ == "__main__":  # pragma: no cover - host entry point
    raise SystemExit(effect_cli())
