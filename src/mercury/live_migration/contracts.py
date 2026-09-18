
from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Mapping, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _hash_payload(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class MigrationTrigger(str, Enum):
    NODE_DEGRADATION = "NODE_DEGRADATION"
    OVERLOAD = "OVERLOAD"
    TOPOLOGY_CHANGE = "TOPOLOGY_CHANGE"
    RESOURCE_LOSS = "RESOURCE_LOSS"
    SCHEDULED_MAINTENANCE = "SCHEDULED_MAINTENANCE"
    PLACEMENT_REEVALUATION = "PLACEMENT_REEVALUATION"
    SLO_PRESSURE = "SLO_PRESSURE"
    MANUAL_REQUEST = "MANUAL_REQUEST"


class MigrationMode(str, Enum):
    COLD = "COLD"
    WARM = "WARM"
    LIVE = "LIVE"


class MigrationLifecycle(str, Enum):
    REQUESTED = "REQUESTED"
    QUALIFYING = "QUALIFYING"
    CHECKPOINTING = "CHECKPOINTING"
    TRANSFERRING = "TRANSFERRING"
    RESTORING = "RESTORING"
    VERIFYING = "VERIFYING"
    CUTOVER_READY = "CUTOVER_READY"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"
    ABORTED = "ABORTED"
    FAILED = "FAILED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class MigrationEligibilityState(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    DEFER = "DEFER"
    UNKNOWN = "UNKNOWN"


class FrozenArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    fingerprint: str | None = None

    def _fingerprint_payload(self) -> dict:
        return self.model_dump(mode="json", exclude={"fingerprint"})

    def expected_fingerprint(self) -> str:
        return _hash_payload(self._fingerprint_payload())

    @model_validator(mode="after")
    def _seal_or_verify_fingerprint(self):
        expected = self.expected_fingerprint()
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
            return self
        if self.fingerprint != expected:
            raise ValueError("artifact fingerprint mismatch")
        return self


class MigrationRequest(FrozenArtifact):
    migration_request_id: str
    workload_id: str
    execution_id: str
    source_node_id: str
    trigger: MigrationTrigger

    model_id: str
    model_version: str
    precision: str
    execution_graph_id: str
    execution_graph_position: str

    hardware_profile_id: str
    hardware_profile_generation: int = Field(ge=0)
    topology_generation: int = Field(ge=0)
    placement_decision_id: str
    placement_generation: int = Field(ge=0)
    speculation_plan_id: str
    speculation_generation: int = Field(ge=0)
    reasoning_budget_id: str
    reasoning_budget_generation: int = Field(ge=0)
    scheduler_decision_id: str
    scheduler_generation: int = Field(ge=0)
    intelligence_slo_id: str
    intelligence_slo_version: int = Field(ge=1)
    compute_agreement_id: str
    compute_agreement_generation: int = Field(ge=0)
    authorization_context_id: str
    authorization_generation: int = Field(ge=0)
    execution_generation: int = Field(ge=0)
    provenance_ids: Tuple[str, ...]

    @field_validator(
        "migration_request_id","workload_id","execution_id","source_node_id","model_id","model_version","precision",
        "execution_graph_id","execution_graph_position","hardware_profile_id","placement_decision_id",
        "speculation_plan_id","reasoning_budget_id","scheduler_decision_id","intelligence_slo_id",
        "compute_agreement_id","authorization_context_id",
    )
    @classmethod
    def _non_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("identity fields must be non-blank")
        return value

    @field_validator("provenance_ids")
    @classmethod
    def _provenance(cls, value: Tuple[str, ...]) -> Tuple[str, ...]:
        if not value or any(not x.strip() for x in value):
            raise ValueError("provenance_ids must be non-empty and non-blank")
        if len(set(value)) != len(value):
            raise ValueError("duplicate provenance identity")
        return value


class MigrationEligibility(FrozenArtifact):
    migration_request_id: str
    state: MigrationEligibilityState
    reasons: Tuple[str, ...]
    evaluated_generation: int = Field(ge=0)


class DestinationCandidate(FrozenArtifact):
    candidate_id: str
    node_id: str
    hardware_profile_id: str
    hardware_profile_generation: int = Field(ge=0)
    topology_generation: int = Field(ge=0)
    placement_decision_id: str
    placement_generation: int = Field(ge=0)
    authorization_context_id: str
    authorization_generation: int = Field(ge=0)
    supports_model: bool
    supports_precision: bool
    supports_runtime: bool
    capacity_sufficient: bool
    quality_preserving: bool
    provenance_ids: Tuple[str, ...]


class MigrationStateSnapshot(FrozenArtifact):
    snapshot_id: str
    migration_request_id: str
    execution_generation: int = Field(ge=0)
    model_id: str
    model_version: str
    precision: str
    execution_graph_position: str
    session_context_ref: str
    kv_cache_ref: str | None = None
    verification_state_ref: str | None = None
    reasoning_state_ref: str
    speculation_state_ref: str
    scheduler_state_ref: str
    slo_ref: str
    agreement_ref: str
    authorization_context_id: str
    authorization_generation: int = Field(ge=0)
    payload_digest: str


class MigrationCheckpoint(FrozenArtifact):
    checkpoint_id: str
    migration_request_id: str
    snapshot: MigrationStateSnapshot
    source_execution_generation: int = Field(ge=0)
    checkpoint_generation: int = Field(ge=0)
    sealed: bool = True


class MigrationPlan(FrozenArtifact):
    migration_plan_id: str
    migration_request_id: str
    destination_candidate_id: str
    destination_node_id: str
    mode: MigrationMode
    source_execution_generation: int = Field(ge=0)
    topology_generation: int = Field(ge=0)
    placement_generation: int = Field(ge=0)
    scheduler_generation: int = Field(ge=0)
    agreement_generation: int = Field(ge=0)
    authorization_generation: int = Field(ge=0)
    checkpoint_required: bool = True


class TransferReceipt(FrozenArtifact):
    transfer_id: str
    migration_plan_id: str
    checkpoint_id: str
    destination_node_id: str
    transferred_digest: str
    bytes_transferred: int = Field(ge=0)
    complete: bool


class RestoreReceipt(FrozenArtifact):
    restore_id: str
    migration_plan_id: str
    destination_node_id: str
    checkpoint_id: str
    restored_execution_generation: int = Field(ge=0)
    restored_digest: str
    ready_for_verification: bool


class MigrationVerification(FrozenArtifact):
    verification_id: str
    migration_plan_id: str
    destination_node_id: str
    model_identity_match: bool
    precision_match: bool
    graph_position_match: bool
    context_digest_match: bool
    reasoning_state_match: bool
    speculation_state_match: bool
    slo_match: bool
    authorization_match: bool
    quality_preserved: bool

    @property
    def equivalent(self) -> bool:
        return all((
            self.model_identity_match, self.precision_match, self.graph_position_match,
            self.context_digest_match, self.reasoning_state_match, self.speculation_state_match,
            self.slo_match, self.authorization_match, self.quality_preserved,
        ))


class CutoverRecord(FrozenArtifact):
    cutover_id: str
    migration_plan_id: str
    source_execution_id: str
    destination_execution_id: str
    authority_generation: int = Field(ge=0)
    committed: bool


class RollbackRecord(FrozenArtifact):
    rollback_id: str
    migration_plan_id: str
    restored_source_execution_id: str
    rollback_generation: int = Field(ge=0)
    reason: str


class MigrationAgreementView(FrozenArtifact):
    agreement_id: str
    agreement_generation: int = Field(ge=0)
    quality_floor: float = Field(ge=0.0, le=1.0)
    verification_required: bool
    authorization_context_id: str
    authorization_generation: int = Field(ge=0)


class MigrationLedgerEvent(FrozenArtifact):
    event_id: str
    migration_request_id: str
    event_type: str
    lifecycle: MigrationLifecycle
    generation: int = Field(ge=0)
    detail: str
