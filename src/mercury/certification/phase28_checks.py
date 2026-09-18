from mercury.datacenter_twin.contracts import CalibrationState, TwinScenario
from mercury.datacenter_twin.engine import DatacenterTwin


def twin_simulation():
    scenario = TwinScenario(
        scenario_id="s-1",
        baseline_generation=3,
        hypothetical_change_id="h-1",
        change_kind="placement",
        calibration_state=CalibrationState.UNCALIBRATED,
        provenance_ids=("p1",),
    )
    result = DatacenterTwin().simulate(
        scenario,
        capacity_delta=0,
        thermal_delta_c=1,
        workload_delta=2,
        uncertainty=0.3,
    )
    return result.advisory_only and result.status in {"VALID", "UNKNOWN"}, "datacenter twin remains advisory and provenance-bound"


CHECKS = {"twin_simulation": twin_simulation}
