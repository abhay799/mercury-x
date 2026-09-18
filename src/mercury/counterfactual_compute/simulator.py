from mercury.counterfactual_compute.contracts import CounterfactualResult, CounterfactualStatus

class CounterfactualComputeSimulator:
    def simulate(self, scenario, *, quality_delta=None, latency_delta_ms=None, resource_delta=None,
                 uncertainty:float=1.0, evidence_ids=()):
        status = CounterfactualStatus.UNKNOWN if any(v is None for v in (quality_delta,latency_delta_ms,resource_delta)) else CounterfactualStatus.VALID
        return CounterfactualResult(
            result_id=f"cf:{scenario.scenario_id}",
            scenario_id=scenario.scenario_id,
            status=status,
            predicted_quality_delta=quality_delta,
            predicted_latency_delta_ms=latency_delta_ms,
            predicted_resource_delta=resource_delta,
            uncertainty=uncertainty,
            calibration_state="UNCALIBRATED",
            advisory_only=True,
            evidence_ids=tuple(evidence_ids),
        )
