import pytest
from pydantic import ValidationError

from mercury.global_memory.contracts import GlobalMemoryNamespace


def test_contract_module_imports():
    from mercury.context_prediction.contracts import (
        MAX_CONTEXT_PREDICTIONS,
        MAX_PREDICTION_CANDIDATES,
        MAX_REASON_CODES,
        MAX_SOURCE_RECORDS_PER_PREDICTION,
        ContextConfidenceBand,
        ContextPrediction,
        ContextPredictionCandidate,
        ContextPredictionFeatureVector,
        ContextPredictionHorizon,
        ContextPredictionReasonCode,
        ContextPredictionRequest,
        ContextPredictionResult,
        make_context_prediction_candidate_id,
        make_context_prediction_id,
    )

    assert MAX_PREDICTION_CANDIDATES == 256
    assert MAX_CONTEXT_PREDICTIONS == 64
    assert MAX_SOURCE_RECORDS_PER_PREDICTION == 128
    assert MAX_REASON_CODES == 16

    assert ContextPrediction
    assert ContextPredictionCandidate
    assert ContextPredictionFeatureVector
    assert ContextPredictionRequest
    assert ContextPredictionResult
    assert make_context_prediction_candidate_id
    assert make_context_prediction_id

    assert {
        member.value
        for member in ContextPredictionHorizon
    } == {
        "NEXT_TURN",
        "NEXT_TASK",
        "SESSION_NEAR_TERM",
    }

    assert {
        member.value
        for member in ContextConfidenceBand
    } == {
        "LOW",
        "MEDIUM",
        "HIGH",
    }

    assert {
        member.value
        for member in ContextPredictionReasonCode
    } == {
        "TASK_CONTINUITY",
        "CONTEXT_RECURRENCE",
        "DEPENDENCY_ADJACENCY",
        "SOURCE_LINEAGE_OVERLAP",
        "ARTIFACT_CONTINUITY",
        "SESSION_GLOBAL_AGREEMENT",
        "CONFLICT_PRESENT",
        "NEAR_TERM_SESSION_SIGNAL",
    }


def _candidate_payload():
    from mercury.context_prediction.contracts import (
        make_context_prediction_candidate_id,
    )

    payload = {
        "namespace_type": GlobalMemoryNamespace.PROJECT,
        "namespace_id": "project-alpha",
        "context_key": "customer-risk",
        "source_global_record_ids": (
            "global-001",
            "global-002",
        ),
        "source_phase8_record_ids": (
            "session-001",
        ),
        "source_artifact_ids": (
            "artifact-001",
        ),
        "conflict_present": False,
        "creation_sequence": 1,
    }

    payload["candidate_id"] = (
        make_context_prediction_candidate_id(
            namespace_type=payload["namespace_type"],
            namespace_id=payload["namespace_id"],
            context_key=payload["context_key"],
            source_global_record_ids=payload[
                "source_global_record_ids"
            ],
            source_phase8_record_ids=payload[
                "source_phase8_record_ids"
            ],
            source_artifact_ids=payload[
                "source_artifact_ids"
            ],
            conflict_present=payload[
                "conflict_present"
            ],
            creation_sequence=payload[
                "creation_sequence"
            ],
        )
    )

    return payload


def test_candidate_contract_accepts_canonical_identity():
    from mercury.context_prediction.contracts import (
        ContextPredictionCandidate,
    )

    candidate = ContextPredictionCandidate(
        **_candidate_payload()
    )

    assert candidate.context_key == "customer-risk"
    assert candidate.namespace_id == "project-alpha"
    assert candidate.creation_sequence == 1
    assert candidate.conflict_present is False


def test_candidate_identity_is_deterministic():
    from mercury.context_prediction.contracts import (
        make_context_prediction_candidate_id,
    )

    kwargs = {
        "namespace_type": GlobalMemoryNamespace.PROJECT,
        "namespace_id": "project-alpha",
        "context_key": "customer-risk",
        "source_global_record_ids": (
            "global-001",
            "global-002",
        ),
        "source_phase8_record_ids": (
            "session-001",
        ),
        "source_artifact_ids": (
            "artifact-001",
        ),
        "conflict_present": False,
        "creation_sequence": 1,
    }

    first = make_context_prediction_candidate_id(
        **kwargs
    )

    second = make_context_prediction_candidate_id(
        **kwargs
    )

    assert first == second
    assert len(first) == 64


def test_candidate_identity_rejects_noncanonical_sources():
    from mercury.context_prediction.contracts import (
        make_context_prediction_candidate_id,
    )

    with pytest.raises(ValueError):
        make_context_prediction_candidate_id(
            namespace_type=GlobalMemoryNamespace.PROJECT,
            namespace_id="project-alpha",
            context_key="customer-risk",
            source_global_record_ids=(
                "global-002",
                "global-001",
            ),
            source_phase8_record_ids=(),
            source_artifact_ids=(),
            conflict_present=False,
            creation_sequence=1,
        )


def test_candidate_rejects_duplicate_source_ids():
    from mercury.context_prediction.contracts import (
        ContextPredictionCandidate,
    )

    payload = _candidate_payload()

    payload["source_global_record_ids"] = (
        "global-001",
        "global-001",
    )

    with pytest.raises(ValidationError):
        ContextPredictionCandidate(
            **payload
        )


def test_candidate_rejects_more_than_source_limit():
    from mercury.context_prediction.contracts import (
        ContextPredictionCandidate,
        make_context_prediction_candidate_id,
    )

    source_ids = tuple(
        f"global-{index:03d}"
        for index in range(129)
    )

    candidate_id = (
        make_context_prediction_candidate_id(
            namespace_type=GlobalMemoryNamespace.PROJECT,
            namespace_id="project-alpha",
            context_key="customer-risk",
            source_global_record_ids=source_ids,
            source_phase8_record_ids=(),
            source_artifact_ids=(),
            conflict_present=False,
            creation_sequence=1,
        )
    )

    with pytest.raises(ValidationError):
        ContextPredictionCandidate(
            namespace_type=GlobalMemoryNamespace.PROJECT,
            namespace_id="project-alpha",
            context_key="customer-risk",
            candidate_id=candidate_id,
            source_global_record_ids=source_ids,
            source_phase8_record_ids=(),
            source_artifact_ids=(),
            conflict_present=False,
            creation_sequence=1,
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "recency",
        "task_continuity",
        "context_key_recurrence",
        "dependency_adjacency",
        "source_lineage_overlap",
        "artifact_continuity",
        "session_global_agreement",
        "lifecycle_eligibility",
        "conflict_state",
        "horizon_compatibility",
    ),
)
def test_feature_values_are_bounded(field_name):
    from mercury.context_prediction.contracts import (
        ContextPredictionFeatureVector,
    )

    payload = {
        "candidate_id": "candidate-001",
        "recency": 0.5,
        "task_continuity": 0.5,
        "context_key_recurrence": 0.5,
        "dependency_adjacency": 0.5,
        "source_lineage_overlap": 0.5,
        "artifact_continuity": 0.5,
        "session_global_agreement": 0.5,
        "lifecycle_eligibility": 1.0,
        "conflict_state": 1.0,
        "horizon_compatibility": 0.5,
    }

    payload[field_name] = 1.01

    with pytest.raises(ValidationError):
        ContextPredictionFeatureVector(
            **payload
        )

    payload[field_name] = -0.01

    with pytest.raises(ValidationError):
        ContextPredictionFeatureVector(
            **payload
        )


def test_request_requires_exact_namespace_authorization():
    from mercury.context_prediction.contracts import (
        ContextPredictionRequest,
    )

    with pytest.raises(ValidationError):
        ContextPredictionRequest(
            namespace_type=GlobalMemoryNamespace.PROJECT,
            namespace_id="project-alpha",
            authorized_namespace_type=(
                GlobalMemoryNamespace.PROJECT
            ),
            authorized_namespace_id="project-beta",
            predictor_id="phase10-baseline",
            predictor_version="1",
        )


def test_request_rejects_blank_predictor_identity():
    from mercury.context_prediction.contracts import (
        ContextPredictionRequest,
    )

    with pytest.raises(ValidationError):
        ContextPredictionRequest(
            namespace_type=GlobalMemoryNamespace.PROJECT,
            namespace_id="project-alpha",
            authorized_namespace_type=(
                GlobalMemoryNamespace.PROJECT
            ),
            authorized_namespace_id="project-alpha",
            predictor_id="",
            predictor_version="1",
        )

    with pytest.raises(ValidationError):
        ContextPredictionRequest(
            namespace_type=GlobalMemoryNamespace.PROJECT,
            namespace_id="project-alpha",
            authorized_namespace_type=(
                GlobalMemoryNamespace.PROJECT
            ),
            authorized_namespace_id="project-alpha",
            predictor_id="phase10-baseline",
            predictor_version="",
        )


def test_request_limit_is_bounded():
    from mercury.context_prediction.contracts import (
        ContextPredictionRequest,
    )

    with pytest.raises(ValidationError):
        ContextPredictionRequest(
            namespace_type=GlobalMemoryNamespace.PROJECT,
            namespace_id="project-alpha",
            authorized_namespace_type=(
                GlobalMemoryNamespace.PROJECT
            ),
            authorized_namespace_id="project-alpha",
            predictor_id="phase10-baseline",
            predictor_version="1",
            limit=65,
        )


def _prediction_payload():
    from mercury.context_prediction.contracts import (
        ContextConfidenceBand,
        ContextPredictionHorizon,
        ContextPredictionReasonCode,
        make_context_prediction_id,
    )

    payload = {
        "namespace_type": GlobalMemoryNamespace.PROJECT,
        "namespace_id": "project-alpha",
        "context_key": "customer-risk",
        "source_global_record_ids": (
            "global-001",
        ),
        "source_phase8_record_ids": (
            "session-001",
        ),
        "prediction_horizon": (
            ContextPredictionHorizon.NEXT_TASK
        ),
        "confidence": 0.8,
        "confidence_band": (
            ContextConfidenceBand.HIGH
        ),
        "reason_codes": (
            ContextPredictionReasonCode
            .SOURCE_LINEAGE_OVERLAP,
        ),
        "creation_sequence": 1,
        "predictor_id": "phase10-baseline",
        "predictor_version": "1",
    }

    payload["prediction_id"] = (
        make_context_prediction_id(
            namespace_type=payload["namespace_type"],
            namespace_id=payload["namespace_id"],
            context_key=payload["context_key"],
            source_global_record_ids=payload[
                "source_global_record_ids"
            ],
            source_phase8_record_ids=payload[
                "source_phase8_record_ids"
            ],
            prediction_horizon=payload[
                "prediction_horizon"
            ],
            confidence=payload["confidence"],
            confidence_band=payload[
                "confidence_band"
            ],
            reason_codes=payload[
                "reason_codes"
            ],
            creation_sequence=payload[
                "creation_sequence"
            ],
            predictor_id=payload[
                "predictor_id"
            ],
            predictor_version=payload[
                "predictor_version"
            ],
        )
    )

    return payload


def test_prediction_contract_accepts_valid_prediction():
    from mercury.context_prediction.contracts import (
        ContextPrediction,
    )

    prediction = ContextPrediction(
        **_prediction_payload()
    )

    assert prediction.confidence == 0.8
    assert prediction.predictor_id == "phase10-baseline"


@pytest.mark.parametrize(
    "confidence",
    (
        -0.01,
        1.01,
        float("nan"),
        float("inf"),
        float("-inf"),
    ),
)
def test_prediction_rejects_invalid_confidence(
    confidence,
):
    from mercury.context_prediction.contracts import (
        ContextPrediction,
    )

    payload = _prediction_payload()
    payload["confidence"] = confidence

    with pytest.raises(ValidationError):
        ContextPrediction(
            **payload
        )


def test_prediction_rejects_duplicate_reason_codes():
    from mercury.context_prediction.contracts import (
        ContextPrediction,
        ContextPredictionReasonCode,
    )

    payload = _prediction_payload()

    payload["reason_codes"] = (
        ContextPredictionReasonCode
        .TASK_CONTINUITY,
        ContextPredictionReasonCode
        .TASK_CONTINUITY,
    )

    with pytest.raises(ValidationError):
        ContextPrediction(
            **payload
        )


def test_prediction_rejects_more_than_reason_limit():
    from mercury.context_prediction.contracts import (
        ContextPrediction,
        ContextPredictionReasonCode,
    )

    payload = _prediction_payload()

    payload["reason_codes"] = tuple(
        ContextPredictionReasonCode
        .TASK_CONTINUITY
        for _ in range(17)
    )

    with pytest.raises(ValidationError):
        ContextPrediction(
            **payload
        )


def test_prediction_identity_is_deterministic():
    from mercury.context_prediction.contracts import (
        make_context_prediction_id,
    )

    payload = _prediction_payload()

    kwargs = {
        key: value
        for key, value in payload.items()
        if key != "prediction_id"
    }

    first = make_context_prediction_id(
        **kwargs
    )

    second = make_context_prediction_id(
        **kwargs
    )

    assert first == second
    assert len(first) == 64


def test_result_rejects_more_than_prediction_limit():
    from mercury.context_prediction.contracts import (
        ContextPrediction,
        ContextPredictionResult,
    )

    prediction = ContextPrediction(
        **_prediction_payload()
    )

    with pytest.raises(ValidationError):
        ContextPredictionResult(
            predictions=tuple(
                prediction
                for _ in range(65)
            )
        )