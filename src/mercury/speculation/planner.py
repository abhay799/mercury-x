from mercury.disaggregated_execution.contracts import ExecutionSegment, ExecutionSegmentState
from mercury.placement.contracts import PlacementCandidate
from mercury.speculation.contracts import SpeculationPlan, sh


def _candidate_fingerprint(candidate: PlacementCandidate) -> str:
    return sh({"placement_candidate": candidate.model_dump(mode="json")})


def build_speculation_plan(
    *,
    max_branches,
    source_segment_id=None,
    candidate_ids=None,
    source_segment=None,
    placement_candidates=None,
    verification_policy_id="verify",
    commit_policy_id="first_verified",
    cancellation_policy_id="cancel_losers",
):
    if (source_segment is None) != (placement_candidates is None):
        raise ValueError("typed source segment and placement candidates must be supplied together")
    if source_segment is not None:
        if source_segment_id is not None or candidate_ids is not None:
            raise ValueError("typed plan inputs cannot mix with legacy identifiers")
        if type(source_segment) is not ExecutionSegment:
            raise ValueError("speculation requires a typed Phase 12 execution segment")
        source_segment = ExecutionSegment.model_validate(source_segment.model_dump())
        if source_segment.execution_state is not ExecutionSegmentState.READY:
            raise ValueError("speculation requires a READY Phase 12 segment")
        candidates = tuple(placement_candidates)
        if not candidates:
            raise ValueError("placement candidates must be nonempty")
        if any(type(candidate) is not PlacementCandidate for candidate in candidates):
            raise ValueError("speculation requires typed Phase 15 placement candidates")
        candidates = tuple(
            PlacementCandidate.model_validate(candidate.model_dump()) for candidate in candidates
        )
        if any(not candidate.eligible for candidate in candidates):
            raise ValueError("speculation requires eligible Phase 15 candidates")
        if any(candidate.segment_id != source_segment.segment_id for candidate in candidates):
            raise ValueError("placement candidate segment does not match source segment")
        if len({candidate.candidate_id for candidate in candidates}) != len(candidates):
            raise ValueError("duplicate placement candidate")
        candidates = tuple(sorted(candidates, key=lambda candidate: candidate.candidate_id))
        ids = tuple(candidate.candidate_id for candidate in candidates)
        candidate_fingerprints = tuple(
            (candidate.candidate_id, _candidate_fingerprint(candidate)) for candidate in candidates
        )
        source_segment_id = source_segment.segment_id
        source_execution_plan_id = source_segment.execution_plan_id
        namespace_type = source_segment.namespace_type
        namespace_id = source_segment.namespace_id
        source_segment_fingerprint = sh({"execution_segment": source_segment.model_dump(mode="json")})
    else:
        if source_segment_id is None or candidate_ids is None:
            raise ValueError("legacy plan requires source segment and candidate identifiers")
        ids = tuple(sorted(candidate_ids))
        candidate_fingerprints = tuple(
            (candidate_id, sh({"placement_candidate_id": candidate_id})) for candidate_id in ids
        )
        source_execution_plan_id = None
        namespace_type = None
        namespace_id = None
        source_segment_fingerprint = None

    values = {
        "source_segment_id": source_segment_id,
        "placement_candidate_ids": ids,
        "candidate_fingerprints": candidate_fingerprints,
        "max_branches": max_branches,
        "verification_policy_id": verification_policy_id,
        "commit_policy_id": commit_policy_id,
        "cancellation_policy_id": cancellation_policy_id,
        "source_execution_plan_id": source_execution_plan_id,
        "namespace_type": namespace_type,
        "namespace_id": namespace_id,
        "source_segment_fingerprint": source_segment_fingerprint,
    }
    fingerprint = sh(
        {
            **values,
            "namespace_type": namespace_type.value if namespace_type else None,
        }
    )
    return SpeculationPlan(
        speculation_plan_id=sh({"plan": fingerprint}),
        fingerprint=fingerprint,
        **values,
    )
