from __future__ import annotations

import pytest
from pydantic import ValidationError

from mercury.certification.phase0 import (
    REQUIRED_PHASE0_GATE_IDS,
    Phase0CertificationConfig,
    Phase0Gate,
    evaluate_phase0_certification,
)
from mercury.context.models import (
    ContextArtifact,
    ContextArtifactKind,
    ContextPortability,
    ContextStorageTier,
)
from mercury.runtime.events import RuntimeEventEvidence, RuntimeEventType, RuntimeStateTransition
from mercury.runtime.failure_scenarios import (
    ExpectedRecoveryOutcome,
    FailureInjectionScenario,
    FailureScenarioKind,
)
from mercury.runtime.prerequisites import (
    PrerequisiteCheck,
    PrerequisiteKind,
    PrerequisiteStatus,
    PrerequisiteValidationResult,
    RequiredArtifact,
)
from mercury.runtime.provenance import (
    ConstraintEvidence,
    DecisionAlternative,
    DecisionProvenance,
    PredictedMetric,
)
from mercury.runtime.recovery_state import CheckpointReference, ExecutionRecoveryState
from mercury.runtime.state import RuntimeNodeStatus
from mercury.runtime.trace_context import ExecutionIdentity, TraceContext
from mercury.telemetry.evidence import ExecutionMeasurement, MeasurementSource, TelemetryEvidenceRecord
from mercury.telemetry.slo_evidence import SLOComparison, SLOEvaluationEvidence, SLOMetricEvaluation


def gates(**overrides: bool) -> tuple[Phase0Gate, ...]:
    return tuple(
        Phase0Gate(
            gate_id=gate_id,
            passed=overrides.get(gate_id, True),
            evidence=f"{gate_id} evidence",
        )
        for gate_id in REQUIRED_PHASE0_GATE_IDS
    )


def config(**overrides: bool) -> Phase0CertificationConfig:
    return Phase0CertificationConfig(gates=gates(**overrides))


def test_execution_identity_flows_through_trace_event_telemetry_and_slo_evidence():
    identity = ExecutionIdentity(
        request_id="request-1", workload_id="workload-1", execution_id="execution-1"
    )
    trace = TraceContext(
        trace_id="trace-1",
        span_id="span-1",
        identity=identity,
        node_id="node-1",
        attempt=0,
    )
    transition = RuntimeStateTransition(
        transition_id="transition-1",
        execution_id=identity.execution_id,
        node_id=trace.node_id,
        from_status=RuntimeNodeStatus.PENDING,
        to_status=RuntimeNodeStatus.RUNNING,
        event_type=RuntimeEventType.NODE_STARTED,
        attempt=trace.attempt,
        reason="node started",
    )
    event = RuntimeEventEvidence(
        event_id="event-1",
        trace_id=trace.trace_id,
        span_id=trace.span_id,
        execution_id=identity.execution_id,
        node_id=trace.node_id,
        event_type=RuntimeEventType.NODE_STARTED,
        transition=transition,
    )
    measurement = ExecutionMeasurement(
        metric_name="latency_ms", value=25.0, unit="ms", source=MeasurementSource.MEASURED
    )
    telemetry = TelemetryEvidenceRecord(
        record_id="record-1",
        request_id=identity.request_id,
        workload_id=identity.workload_id,
        execution_id=event.execution_id,
        node_id=event.node_id,
        trace_id=event.trace_id,
        span_id=event.span_id,
        model_id="model-1",
        hardware_id="hardware-1",
        precision="fp16",
        context_strategy="isolated",
        measurements=(measurement,),
    )
    slo = SLOEvaluationEvidence(
        evaluation_id="slo-evaluation-1",
        workload_id=telemetry.workload_id,
        execution_id=telemetry.execution_id,
        slo_version="mercury.slo/v1",
        overall_passed=True,
        metric_evaluations=(
            SLOMetricEvaluation(
                metric_name=measurement.metric_name,
                observed_value=measurement.value,
                target_value=30.0,
                unit=measurement.unit,
                comparison=SLOComparison.LESS_THAN_OR_EQUAL,
                passed=True,
                source=measurement.source,
            ),
        ),
    )
    assert slo.execution_id == identity.execution_id
    assert telemetry.trace_id == trace.trace_id


def test_recovery_state_references_context_and_checkpoint_evidence_coherently():
    context = ContextArtifact(
        artifact_id="context-1",
        owner_id="owner-1",
        tenant_id="tenant-1",
        authorized_owner_ids=("owner-1",),
        authorized_tenant_ids=("tenant-1",),
        kind=ContextArtifactKind.INPUT_CONTEXT,
        portability=ContextPortability.PORTABLE,
        storage_tier=ContextStorageTier.SYSTEM_RAM,
        privacy_level="confidential",
        reference_uri="mercury://context/1",
        integrity_evidence="sha256:" + "a" * 64,
    )
    checkpoint = CheckpointReference(
        checkpoint_id="checkpoint-1",
        node_id="node-1",
        reference_uri="mercury://checkpoint/1",
    )
    state = ExecutionRecoveryState(
        workload_id="workload-1",
        execution_id="execution-1",
        graph_version="mercury.execution-graph/v1",
        current_node_id="node-1",
        pending_node_ids=("node-1",),
        context_artifact_ids=(context.artifact_id,),
        checkpoint_references=(checkpoint,),
    )
    assert state.context_artifact_ids == (context.artifact_id,)
    assert state.checkpoint_references[0].checkpoint_id == checkpoint.checkpoint_id


def test_decision_provenance_preserves_model_hardware_and_context_evidence():
    provenance = DecisionProvenance(
        decision_id="decision-1",
        workload_id="workload-1",
        execution_id="execution-1",
        selected_model_id="model-1",
        selected_model_configuration_id="config-1",
        selected_precision="fp16",
        selected_hardware_id="hardware-1",
        selected_context_strategy="isolated",
        policy_version="mercury.policy/v1",
        slo_version="mercury.slo/v1",
        predicted_metrics=(PredictedMetric(metric_name="latency_ms", value=25.0),),
        constraints_satisfied=(ConstraintEvidence(constraint_id="privacy-1", satisfied=True),),
        alternatives_considered=(
            DecisionAlternative(
                alternative_id="alternative-1",
                model_id="model-1",
                model_configuration_id="config-1",
                precision="fp16",
                hardware_id="hardware-1",
                context_strategy="isolated",
                selected=True,
            ),
        ),
        rejection_reasons=(),
    )
    assert (provenance.selected_model_id, provenance.selected_hardware_id) == (
        "model-1",
        "hardware-1",
    )
    assert provenance.selected_context_strategy == "isolated"


def test_failure_scenario_preserves_expected_recovery_evidence():
    scenario = FailureInjectionScenario(
        scenario_id="scenario-1",
        scenario_kind=FailureScenarioKind.WORKER_CRASH,
        target_execution_id="execution-1",
        target_node_id="node-1",
        trigger_attempt=0,
        description="worker exits",
        expected_recovery=ExpectedRecoveryOutcome.RESCHEDULE,
    )
    assert scenario.expected_recovery is ExpectedRecoveryOutcome.RESCHEDULE


def test_prerequisite_failure_prevents_certification_pass():
    required = RequiredArtifact(
        artifact_id="model-1", kind=PrerequisiteKind.MODEL_ARTIFACT, required=True
    )
    check = PrerequisiteCheck(
        artifact_id="model-1", status=PrerequisiteStatus.MISSING, reason="artifact missing"
    )
    prerequisites = PrerequisiteValidationResult(
        workload_id="workload-1",
        execution_id="execution-1",
        required_artifacts=(required,),
        checks=(check,),
    )
    result = evaluate_phase0_certification(config(prerequisite_validation=prerequisites.passed))
    assert result.overall_passed is False


def test_missing_required_gate_prevents_pass():
    result = evaluate_phase0_certification(Phase0CertificationConfig(gates=gates()[:-1]))
    assert result.overall_passed is False
    assert result.missing_gate_ids


def test_failed_gate_forces_overall_failure():
    result = evaluate_phase0_certification(config(runtime_events=False))
    assert result.overall_passed is False


def test_blank_gate_evidence_is_rejected():
    with pytest.raises(ValidationError):
        Phase0Gate(gate_id="runtime_events", passed=False, evidence=" ")


def test_duplicate_gate_ids_are_rejected():
    item = Phase0Gate(gate_id="runtime_events", passed=True, evidence="verified")
    with pytest.raises(ValidationError):
        Phase0CertificationConfig(gates=(item, item))


def test_certification_result_is_immutable():
    result = evaluate_phase0_certification(config())
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        result.overall_passed = False


def test_simulated_telemetry_remains_distinguishable_from_measured_telemetry():
    measured = ExecutionMeasurement(
        metric_name="measured_latency", value=25.0, unit="ms", source=MeasurementSource.MEASURED
    )
    simulated = ExecutionMeasurement(
        metric_name="simulated_latency", value=20.0, unit="ms", source=MeasurementSource.SIMULATED
    )
    assert measured.source is MeasurementSource.MEASURED
    assert simulated.source is MeasurementSource.SIMULATED


def test_complete_valid_phase0_evidence_set_returns_pass():
    result = evaluate_phase0_certification(config())
    assert result.overall_passed is True
    assert result.passed_gate_count == len(REQUIRED_PHASE0_GATE_IDS)
    assert result.failed_gate_count == 0
