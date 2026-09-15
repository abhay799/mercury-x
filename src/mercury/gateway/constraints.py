from __future__ import annotations

from enum import Enum

from pydantic import field_validator, model_validator

from mercury.contracts.base import ContractModel
from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.identity import GatewayIdentity


class ConstraintKind(str, Enum):
    LATENCY = "latency"
    QUALITY = "quality"
    COST = "cost"
    PRIVACY = "privacy"
    PRIORITY = "priority"
    REGION = "region"
    CAPABILITY = "capability"


class CanonicalConstraint(ContractModel):
    constraint_id: str
    kind: ConstraintKind
    operator: str
    value: str | int | float
    unit: str | None
    required: bool
    source_field: str

    @field_validator("constraint_id", "operator", "unit", "source_field")
    @classmethod
    def text_evidence_is_non_empty_when_present(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("constraint evidence must be non-empty")
        return value

    @field_validator("value")
    @classmethod
    def string_value_is_non_empty(cls, value: str | int | float) -> str | int | float:
        if isinstance(value, str) and not value.strip():
            raise ValueError("constraint value must be non-empty")
        return value


class ConstraintNormalizationResult(ContractModel):
    request_id: str
    workload_id: str
    session_id: str
    constraints: tuple[CanonicalConstraint, ...]
    issues: tuple[str, ...]
    canonicalized: bool

    @field_validator("request_id", "workload_id", "session_id")
    @classmethod
    def identity_is_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("constraint identity must be non-empty")
        return value

    @field_validator("issues")
    @classmethod
    def issues_are_non_empty(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not value.strip() for value in values):
            raise ValueError("constraint issues must be non-empty")
        return values

    @model_validator(mode="after")
    def outcome_has_explicit_evidence(self) -> ConstraintNormalizationResult:
        if not self.canonicalized and not self.issues:
            raise ValueError("failed canonicalization requires explicit issue evidence")
        return self


def _workload_constraints(workload: WorkloadRequest) -> list[CanonicalConstraint]:
    prefix = workload.workload_id
    constraints = [
        CanonicalConstraint(
            constraint_id=f"{prefix}:latency",
            kind=ConstraintKind.LATENCY,
            operator="less_than_or_equal",
            value=workload.latency_target_ms,
            unit="ms",
            required=True,
            source_field="latency_target_ms",
        ),
        CanonicalConstraint(
            constraint_id=f"{prefix}:quality",
            kind=ConstraintKind.QUALITY,
            operator="greater_than_or_equal",
            value=workload.quality_target,
            unit="score",
            required=True,
            source_field="quality_target",
        ),
        CanonicalConstraint(
            constraint_id=f"{prefix}:privacy",
            kind=ConstraintKind.PRIVACY,
            operator="equals",
            value=workload.privacy_level,
            unit=None,
            required=True,
            source_field="privacy_level",
        ),
        CanonicalConstraint(
            constraint_id=f"{prefix}:priority",
            kind=ConstraintKind.PRIORITY,
            operator="equals",
            value=workload.priority,
            unit="priority",
            required=True,
            source_field="priority",
        ),
    ]
    if workload.cost_budget is not None:
        constraints.append(
            CanonicalConstraint(
                constraint_id=f"{prefix}:cost",
                kind=ConstraintKind.COST,
                operator="less_than_or_equal",
                value=workload.cost_budget,
                unit="budget",
                required=True,
                source_field="cost_budget",
            )
        )
    for index, raw_constraint in enumerate(workload.hardware_constraints):
        value = raw_constraint.strip()
        if value.startswith("region:"):
            kind = ConstraintKind.REGION
            value = value.removeprefix("region:").strip()
        else:
            kind = ConstraintKind.CAPABILITY
        constraints.append(
            CanonicalConstraint(
                constraint_id=f"{prefix}:{kind.value}:{index}",
                kind=kind,
                operator="equals",
                value=value,
                unit=None,
                required=True,
                source_field="hardware_constraints",
            )
        )
    return constraints


def canonicalize_gateway_constraints(
    identity: GatewayIdentity,
    workload_request: WorkloadRequest,
    *,
    additional_constraints: tuple[CanonicalConstraint, ...] = (),
) -> ConstraintNormalizationResult:
    candidates = (*_workload_constraints(workload_request), *additional_constraints)
    constraints: list[CanonicalConstraint] = []
    issues: list[str] = []
    by_id: dict[str, CanonicalConstraint] = {}
    semantic_keys: set[tuple[object, ...]] = set()

    for candidate in candidates:
        semantic_key = (
            candidate.kind,
            candidate.operator,
            candidate.value,
            candidate.unit,
            candidate.required,
            candidate.source_field,
        )
        existing = by_id.get(candidate.constraint_id)
        if existing is not None:
            if existing != candidate:
                issues.append(f"constraint conflict for {candidate.constraint_id}")
            continue
        if semantic_key in semantic_keys:
            continue
        constraints.append(candidate)
        by_id[candidate.constraint_id] = candidate
        semantic_keys.add(semantic_key)

    if identity.workload_id != workload_request.workload_id:
        issues.append("workload identity does not match constraint source")
    if identity.session_id != workload_request.session_id:
        issues.append("session identity does not match constraint source")

    return ConstraintNormalizationResult(
        request_id=identity.request_id,
        workload_id=identity.workload_id,
        session_id=identity.session_id,
        constraints=tuple(constraints),
        issues=tuple(issues),
        canonicalized=not issues,
    )
