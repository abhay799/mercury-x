"""Composition boundary for the deterministic Phase 2 intelligence pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from mercury.gateway.constraints import ConstraintNormalizationResult
from mercury.gateway.normalization import NormalizationResult
from mercury.intelligence.calibration import (
    CalibrationStatus,
    CalibratedWorkloadIntelligence,
    calibrate_workload_intelligence,
)
from mercury.intelligence.inference import infer_workload_intelligence
from mercury.intelligence.models import WorkloadIntelligenceProfile
from mercury.intelligence.signals import WorkloadSignals, extract_workload_signals


class PipelineStatus(str, Enum):
    PASS = "pass"
    DEGRADED = "degraded"
    FAIL = "fail"


@dataclass(frozen=True)
class PipelineProvenance:
    stage: str
    status: PipelineStatus
    reason: str

    def __post_init__(self) -> None:
        if not self.stage.strip():
            raise ValueError("stage must be nonblank")
        if not self.reason.strip():
            raise ValueError("reason must be nonblank")


@dataclass(frozen=True)
class WorkloadIntelligencePipelineResult:
    request_id: str
    workload_id: str
    session_id: str
    signals: WorkloadSignals | None
    profile: WorkloadIntelligenceProfile | None
    calibration: CalibratedWorkloadIntelligence | None
    status: PipelineStatus
    provenance: tuple[PipelineProvenance, ...]

    def __post_init__(self) -> None:
        identity = (self.request_id, self.workload_id, self.session_id)
        if any(not isinstance(value, str) or not value.strip() for value in identity):
            raise ValueError("pipeline identity must be nonblank")
        for stage in (self.signals, self.profile):
            if stage is not None and (stage.request_id, stage.workload_id, stage.session_id) != identity:
                raise ValueError("pipeline stage identity does not match result identity")
        if self.calibration is not None:
            calibration_profile = self.calibration.profile
            if (calibration_profile.request_id, calibration_profile.workload_id, calibration_profile.session_id) != identity:
                raise ValueError("calibration identity does not match result identity")
            if self.profile is not calibration_profile:
                raise ValueError("calibration must preserve the pipeline profile")
        if self.status is not PipelineStatus.FAIL and (
            self.signals is None or self.profile is None or self.calibration is None
        ):
            raise ValueError("successful pipeline status requires every Phase 2 stage")
        if self.calibration is not None:
            expected = PipelineStatus(self.calibration.status.value)
            if self.status is not expected:
                raise ValueError("pipeline status must match calibration status")
        provenance = tuple(sorted(set(self.provenance), key=lambda item: (item.stage, item.reason)))
        if not provenance:
            raise ValueError("pipeline provenance must not be empty")
        object.__setattr__(self, "provenance", provenance)

    @classmethod
    def from_stages(
        cls,
        signals: WorkloadSignals,
        profile: WorkloadIntelligenceProfile,
        calibration: CalibratedWorkloadIntelligence,
    ) -> WorkloadIntelligencePipelineResult:
        status = PipelineStatus(calibration.status.value)
        return cls(
            request_id=signals.request_id,
            workload_id=signals.workload_id,
            session_id=signals.session_id,
            signals=signals,
            profile=profile,
            calibration=calibration,
            status=status,
            provenance=(
                PipelineProvenance("signal_extraction", PipelineStatus.PASS, "explicit request signals were extracted"),
                PipelineProvenance("inference", PipelineStatus.PASS, "intelligence profile was inferred from signals"),
                PipelineProvenance("calibration", status, "confidence and evidence were calibrated"),
            ),
        )


def _failure(
    normalization: NormalizationResult,
    reason: str,
    signals: WorkloadSignals | None = None,
) -> WorkloadIntelligencePipelineResult:
    return WorkloadIntelligencePipelineResult(
        request_id=normalization.request_id,
        workload_id=normalization.workload_id,
        session_id=normalization.session_id,
        signals=signals,
        profile=None,
        calibration=None,
        status=PipelineStatus.FAIL,
        provenance=(PipelineProvenance("pipeline", PipelineStatus.FAIL, reason),),
    )


def analyze_workload(
    normalization: NormalizationResult,
    constraints: ConstraintNormalizationResult,
) -> WorkloadIntelligencePipelineResult:
    """Run the Task 2 → Task 3 → Task 4 pipeline from Phase 1 contracts."""
    if not isinstance(normalization, NormalizationResult) or not isinstance(
        constraints, ConstraintNormalizationResult
    ):
        raise ValueError("pipeline requires normalized and canonical Phase 1 contracts")
    if any(
        not isinstance(value, str) or not value.strip()
        for value in (normalization.request_id, normalization.workload_id, normalization.session_id)
    ):
        raise ValueError("normalization identity must be nonblank")
    try:
        signals = extract_workload_signals(normalization, constraints)
    except ValueError as error:
        return _failure(normalization, f"signal extraction failed: {error}")
    try:
        profile = infer_workload_intelligence(signals)
    except ValueError as error:
        return _failure(normalization, f"intelligence inference failed: {error}", signals)
    calibration = calibrate_workload_intelligence(signals, profile)
    return WorkloadIntelligencePipelineResult.from_stages(signals, profile, calibration)
