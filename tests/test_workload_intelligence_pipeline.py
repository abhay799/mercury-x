from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime

import pytest

from mercury.contracts.workload_request import WorkloadRequest
from mercury.gateway.constraints import canonicalize_gateway_constraints
from mercury.gateway.identity import GatewayIdentity
from mercury.gateway.models import GatewayRequestEnvelope, GatewayValidationEvidence, GatewayValidationStatus
from mercury.gateway.normalization import normalize_gateway_request
from mercury.intelligence.calibration import CalibrationDecision, CalibrationSeverity, CalibrationStatus, CalibratedWorkloadIntelligence, EvidenceStrength
from mercury.intelligence.inference import infer_workload_intelligence
from mercury.intelligence.pipeline import PipelineProvenance, PipelineStatus, WorkloadIntelligencePipelineResult, analyze_workload
from mercury.intelligence.signals import extract_workload_signals


def phase1(**overrides: object):
    values: dict[str, object] = {
        "workload_id": "workload-1", "session_id": "session-1", "task_type": "inference",
        "input": {"text": "hello"}, "context": {}, "latency_target_ms": 100.0,
        "quality_target": 0.9, "cost_budget": None, "privacy_level": "confidential",
        "priority": 50, "hardware_constraints": (),
    }
    values.update(overrides)
    request = WorkloadRequest(**values)
    identity = GatewayIdentity(request_id="request-1", workload_id="workload-1", session_id="session-1")
    envelope = GatewayRequestEnvelope(
        gateway_request_id="gateway-request-1", identity=identity, workload_request=request,
        received_at=datetime(2026, 9, 16, tzinfo=UTC), normalized=False,
        validation_status=GatewayValidationStatus.ACCEPTED,
        validation_evidence=GatewayValidationEvidence(status=GatewayValidationStatus.ACCEPTED, reasons=()),
    )
    normalization = normalize_gateway_request(envelope)
    assert normalization.normalized_request is not None
    return normalization, canonicalize_gateway_constraints(identity, normalization.normalized_request), request


def test_valid_text_request_completes_full_pipeline_and_preserves_stages() -> None:
    normalization, constraints, _ = phase1()
    result = analyze_workload(normalization, constraints)

    assert result.status is PipelineStatus.DEGRADED
    assert result.signals is not None and result.profile is not None and result.calibration is not None
    assert result.calibration.profile is result.profile


def test_valid_multimodal_request_completes_pipeline() -> None:
    normalization, constraints, _ = phase1(input={"text": "hello", "images": ["image-1"]})
    assert analyze_workload(normalization, constraints).status is PipelineStatus.DEGRADED


def test_identity_and_explicit_constraint_requirements_propagate_end_to_end() -> None:
    normalization, constraints, _ = phase1(input={"text": "hello", "tool_use": True, "structured_output_required": True}, latency_target_ms=200.0, quality_target=0.95, privacy_level="restricted")
    result = analyze_workload(normalization, constraints)

    assert (result.request_id, result.workload_id, result.session_id) == ("request-1", "workload-1", "session-1")
    assert result.profile is not None
    assert result.profile.tool_requirements.external_execution_required is True
    assert result.profile.privacy_requirement.value == "restricted"
    assert result.profile.latency_sensitivity.value == "realtime"
    assert result.profile.quality_requirement.value == "critical"
    assert result.profile.required_capabilities[-1].value in {"tool_use", "vision", "structured_output", "speech", "retrieval", "reasoning", "generation", "code_execution"}


def test_identical_inputs_produce_equal_pipeline_results() -> None:
    normalization, constraints, _ = phase1()
    assert analyze_workload(normalization, constraints) == analyze_workload(normalization, constraints)


def test_explicit_complete_evidence_maps_calibration_pass_to_pipeline_pass() -> None:
    normalization, constraints, _ = phase1(input={"text": "hello", "tool_use": True, "structured_output_required": True}, context={"conversation": ["prior"], "long_context": True, "references": ["retrieval://1"]})
    result = analyze_workload(normalization, constraints)
    assert result.calibration is not None and result.calibration.status is CalibrationStatus.PASS
    assert result.status is PipelineStatus.PASS


def test_calibration_fail_maps_to_pipeline_fail() -> None:
    normalization, constraints, _ = phase1()
    signals = extract_workload_signals(normalization, constraints)
    profile = infer_workload_intelligence(signals)
    failed = CalibratedWorkloadIntelligence(profile, 0.0, CalibrationStatus.FAIL, (CalibrationDecision("evidence", EvidenceStrength.DEFAULTED, CalibrationSeverity.ERROR, "malformed evidence"),))
    result = WorkloadIntelligencePipelineResult.from_stages(signals, profile, failed)
    assert result.status is PipelineStatus.FAIL


def test_identity_mismatch_and_no_keyword_guessing_fail_closed() -> None:
    normalization, constraints, _ = phase1()
    mismatch = constraints.model_copy(update={"session_id": "other"})
    assert analyze_workload(normalization, mismatch).status is PipelineStatus.FAIL
    notes_normalization, notes_constraints, _ = phase1(input={"notes": "image tool use"})
    assert analyze_workload(notes_normalization, notes_constraints).status is PipelineStatus.FAIL


def test_phase1_inputs_are_not_mutated_and_result_is_immutable() -> None:
    normalization, constraints, request = phase1()
    before = (request.model_dump(mode="python"), normalization.model_dump(mode="python"), constraints.model_dump(mode="python"))
    result = analyze_workload(normalization, constraints)

    assert (request.model_dump(mode="python"), normalization.model_dump(mode="python"), constraints.model_dump(mode="python")) == before
    with pytest.raises(FrozenInstanceError):
        result.status = PipelineStatus.FAIL  # type: ignore[misc]
    assert isinstance(result.provenance, tuple)


def test_pipeline_provenance_is_nonblank_and_forbidden_fields_absent() -> None:
    normalization, constraints, _ = phase1()
    result = analyze_workload(normalization, constraints)
    forbidden = {"model_id", "provider", "model_family", "hardware", "device", "cpu", "gpu", "region", "placement", "scheduler_decision", "execution_graph", "runtime_execution", "speculative_execution", "migration", "recovery_policy", "optimization_decision"}
    assert all(item.reason.strip() for item in result.provenance)
    assert forbidden.isdisjoint({field.name for field in fields(WorkloadIntelligencePipelineResult)})
