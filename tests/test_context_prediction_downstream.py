"""Real Phase 10 prediction identities remain advisory across Phases 11/12."""

import pytest

from mercury.context_prediction.contracts import (
    ContextConfidenceBand,
    ContextPrediction,
    ContextPredictionHorizon,
    ContextPredictionReasonCode,
    ContextPredictionResult,
    make_context_prediction_id,
)
from mercury.disaggregated_execution.contracts import ExecutionSegmentState
from mercury.disaggregated_execution.graph import build_disaggregated_execution_plan
from mercury.disaggregated_execution.integration import apply_prediction_hints
from mercury.disaggregated_execution.readiness import (
    evaluate_segment_readiness,
    transition_segment_state,
)
from mercury.disaggregated_execution.results import stitch_execution_results
from mercury.global_memory.contracts import GlobalMemoryNamespace
from mercury.semantic_kv_cache.contracts import (
    SemanticKVCacheState,
    SemanticKVLookupRequest,
    SemanticKVReuseMode,
)
from mercury.semantic_kv_cache.lookup import lookup_semantic_kv_cache
from mercury.semantic_kv_cache.store import SemanticKVCacheStore
from tests._phase11_helpers import make_entry
from tests._phase12_helpers import make_segment, make_segment_result


def _predictions():
    payload = dict(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        context_key="sem",
        source_global_record_ids=("g1",),
        source_phase8_record_ids=("s1",),
        prediction_horizon=ContextPredictionHorizon.NEXT_TASK,
        confidence=0.8,
        confidence_band=ContextConfidenceBand.HIGH,
        reason_codes=(ContextPredictionReasonCode.SOURCE_LINEAGE_OVERLAP,),
        creation_sequence=1,
        predictor_id="phase10-baseline",
        predictor_version="1",
    )
    prediction = ContextPrediction(
        prediction_id=make_context_prediction_id(**payload), **payload
    )
    return ContextPredictionResult(predictions=(prediction,))


def _prediction_ids(result):
    return tuple(prediction.prediction_id for prediction in result.predictions)


def _lookup_request(**overrides):
    payload = dict(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        authorized_namespace_type=GlobalMemoryNamespace.PROJECT,
        authorized_namespace_id="p1",
        semantic_key="sem",
        semantic_fingerprint="fp",
        model_id="m",
        model_version="1",
        tokenizer_id="tok",
        attention_layout="gqa",
        kv_format="paged",
        precision="FP16",
        context_generation=1,
    )
    payload.update(overrides)
    return SemanticKVLookupRequest(**payload)


def _plan(*segments):
    return build_disaggregated_execution_plan(
        namespace_type=GlobalMemoryNamespace.PROJECT,
        namespace_id="p1",
        source_execution_graph_id="graph-1",
        segments=segments,
    )


def test_real_prediction_identity_is_preserved_in_compatible_cache_lineage():
    predictions = _predictions()
    ids = _prediction_ids(predictions)
    hinted = make_entry(prediction_ids=ids, creation_sequence=2)
    unhinted = make_entry(prediction_ids=(), creation_sequence=1)
    store = SemanticKVCacheStore(entries=(unhinted, hinted))
    before = (predictions.model_dump(), store.model_dump(), store.fingerprint)

    baseline = lookup_semantic_kv_cache(_lookup_request(), store)
    assert baseline.matches[0].entry == unhinted
    result = lookup_semantic_kv_cache(_lookup_request(), store, prediction_ids=ids)

    assert result.matches[0].entry == hinted
    assert result.matches[0].entry.source_prediction_ids == ids
    assert result.matches[0].compatibility.physical_kv_reuse_allowed
    assert result == lookup_semantic_kv_cache(
        _lookup_request(),
        SemanticKVCacheStore(entries=(hinted, unhinted)),
        prediction_ids=reversed(ids),
    )
    assert before == (predictions.model_dump(), store.model_dump(), store.fingerprint)


def test_prediction_hint_does_not_supply_namespace_authorization():
    ids = _prediction_ids(_predictions())
    store = SemanticKVCacheStore(entries=(make_entry(prediction_ids=ids),))
    with pytest.raises(ValueError, match="namespace authorization mismatch"):
        lookup_semantic_kv_cache(
            _lookup_request(authorized_namespace_id="p2"),
            store,
            prediction_ids=ids,
        )


def test_prediction_hint_never_includes_another_namespace():
    ids = _prediction_ids(_predictions())
    store = SemanticKVCacheStore(
        entries=(make_entry(namespace_id="p2", prediction_ids=ids),)
    )
    result = lookup_semantic_kv_cache(_lookup_request(), store, prediction_ids=ids)
    assert result.matches == ()


@pytest.mark.parametrize(
    "state,reason",
    (
        (SemanticKVCacheState.STALE, None),
        (SemanticKVCacheState.INVALIDATED, "source revoked"),
    ),
)
def test_prediction_hint_never_reactivates_ineligible_cache(state, reason):
    ids = _prediction_ids(_predictions())
    entry = make_entry(
        prediction_ids=ids, state=state, invalidation_reason=reason
    )
    store = SemanticKVCacheStore(entries=(entry,))
    before = store.model_dump()
    assert lookup_semantic_kv_cache(
        _lookup_request(), store, prediction_ids=ids
    ).matches == ()
    assert store.model_dump() == before


@pytest.mark.parametrize(
    "overrides,reason",
    (
        ({"model_version": "2"}, "MODEL_VERSION_MISMATCH"),
        ({"precision": "INT8"}, "PRECISION_MISMATCH"),
        ({"tokenizer_id": "other"}, "TOKENIZER_MISMATCH"),
    ),
)
def test_prediction_hint_cannot_upgrade_physical_compatibility(overrides, reason):
    ids = _prediction_ids(_predictions())
    entry = make_entry(prediction_ids=ids, **overrides)
    result = lookup_semantic_kv_cache(
        _lookup_request(), SemanticKVCacheStore(entries=(entry,)), prediction_ids=ids
    )
    assert len(result.matches) == 1
    compatibility = result.matches[0].compatibility
    assert compatibility.reuse_mode is SemanticKVReuseMode.SEMANTIC_COMPATIBLE
    assert compatibility.semantic_reuse_allowed
    assert not compatibility.physical_kv_reuse_allowed
    assert reason in compatibility.reason_codes


def test_real_prediction_hints_preserve_plan_and_dependency_readiness():
    predictions = _predictions()
    first = make_segment()
    second = make_segment(sequence=2, dependencies=(first.segment_id,))
    plan = _plan(first, second)
    before = (predictions.model_dump(), plan.model_dump(), plan.plan_fingerprint)

    hinted = apply_prediction_hints(plan, prediction_ids=_prediction_ids(predictions))

    assert hinted is plan
    assert evaluate_segment_readiness(first, segments=hinted.segments, handoffs=())
    assert not evaluate_segment_readiness(
        second, segments=hinted.segments, handoffs=()
    )
    assert before == (predictions.model_dump(), plan.model_dump(), plan.plan_fingerprint)


def test_prediction_hints_cannot_supply_a_missing_required_handoff():
    ids = _prediction_ids(_predictions())
    segment = make_segment(required_handoffs=("required-context-handoff",))
    plan = _plan(segment)
    hinted = apply_prediction_hints(plan, prediction_ids=ids)
    assert hinted is plan
    assert not evaluate_segment_readiness(
        hinted.segments[0], segments=hinted.segments, handoffs=hinted.handoffs
    )


def test_prediction_hints_do_not_replace_success_verification():
    ids = _prediction_ids(_predictions())
    segment = make_segment(state=ExecutionSegmentState.RUNNING)
    plan = _plan(segment)
    hinted = apply_prediction_hints(plan, prediction_ids=ids)
    before = hinted.model_dump()

    with pytest.raises(ValueError, match="verification required before success"):
        transition_segment_state(
            hinted.segments[0], ExecutionSegmentState.SUCCEEDED, verified=False
        )
    with pytest.raises(ValueError, match="successful segment result must be verified"):
        make_segment_result(hinted.segments[0], verified=False)
    # Even an unvalidated copied artifact cannot bypass result verification.
    unverified = make_segment_result(hinted.segments[0]).model_copy(
        update={"verified": False}
    )
    with pytest.raises(ValueError, match="terminal result not verified"):
        stitch_execution_results(
            execution_plan_id=hinted.execution_plan_id,
            namespace_type=hinted.namespace_type,
            namespace_id=hinted.namespace_id,
            terminal_segment_ids=hinted.terminal_segment_ids,
            results=(unverified,),
            stitching_policy_id="stitch-1",
        )
    assert hinted is plan
    assert hinted.model_dump() == before
