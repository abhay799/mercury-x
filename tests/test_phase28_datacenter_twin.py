from mercury.datacenter_twin.contracts import (
    CalibrationState,
    TwinScenario,
    TwinResult,
    validate_twin_scenario,
)
from mercury.datacenter_twin.engine import DatacenterTwin


def test_twin_scenario_requires_provenance_and_calibration_state():
    scenario = TwinScenario(
        scenario_id="s-1",
        baseline_generation=3,
        hypothetical_change_id="h-1",
        change_kind="placement",
        calibration_state=CalibrationState.UNCALIBRATED,
        provenance_ids=("p1",),
    )
    assert validate_twin_scenario(scenario)

    result = DatacenterTwin().simulate(
        scenario,
        capacity_delta=0,
        thermal_delta_c=1,
        workload_delta=2,
        uncertainty=0.3,
    )
    assert result.status in {"VALID", "UNKNOWN"}
    assert result.advisory_only is True
