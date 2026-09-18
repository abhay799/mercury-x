from mercury.certification import phase18
from mercury.certification import phase18_checks
from mercury.quality_scheduler.contracts import AdmissionState, SchedulingDecision


def test_phase18_certification():
    results = phase18.evaluate()
    assert results
    assert all(ok for _, ok, _ in results)
    assert len({id(check) for check in phase18.CHECKS.values()}) == len(phase18.CHECKS)
    assert len({evidence for _, _, evidence in results}) == len(results)


def test_phase18_admission_gate_fails_independently(monkeypatch):
    def always_admit(**kwargs):
        return AdmissionState.ADMIT, ("FORCED",)

    monkeypatch.setattr(phase18_checks, "decide_admission", always_admit)
    assert not phase18_checks.admission()[0]
    assert phase18_checks.no_quality_degrade()[0]


def test_phase18_quality_gate_fails_independently(monkeypatch):
    real = phase18_checks.schedule_request

    def lower_floor(request, features, *, admission_state, selected_candidate_ids=()):
        decision = real(
            request, features, admission_state=admission_state, selected_candidate_ids=selected_candidate_ids,
        )
        payload = decision.model_dump() | {"required_quality_floor": request.required_quality_floor - .2}
        payload.pop("fingerprint")
        payload.pop("decision_id")
        from mercury.reasoning_budget.contracts import canonical_hash
        identity = {
            "workload_id": payload["workload_id"], "admission_state": payload["admission_state"].value,
            "priority_class": payload["priority_class"].value, "rank_score": payload["rank_score"],
            "selected_candidate_ids": list(payload["selected_candidate_ids"]),
            "queue_generation": payload["queue_generation"], "decision_generation": payload["decision_generation"],
            "previous_decision_id": payload["previous_decision_id"],
            "required_quality_floor": payload["required_quality_floor"],
            "provenance_ids": list(payload["provenance_ids"]),
        }
        fingerprint = canonical_hash(identity)
        return SchedulingDecision(**payload, fingerprint=fingerprint, decision_id=canonical_hash({"scheduling_decision": fingerprint}))

    monkeypatch.setattr(phase18_checks, "schedule_request", lower_floor)
    monkeypatch.setattr(phase18_checks.SchedulingDecision, "model_validate", lambda payload: payload)
    assert not phase18_checks.no_quality_degrade()[0]
    assert phase18_checks.admission()[0]
