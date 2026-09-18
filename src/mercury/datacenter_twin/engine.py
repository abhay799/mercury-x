from mercury.datacenter_twin.contracts import CalibrationState, TwinResult, TwinScenario, validate_twin_scenario


class DatacenterTwin:
    def simulate(
        self,
        scenario: TwinScenario | str | None = None,
        *,
        scenario_id: str | None = None,
        baseline_generation: int = 0,
        hypothetical_change_id: str | None = None,
        change_kind: str = "placement",
        calibration_state: CalibrationState | str = CalibrationState.UNCALIBRATED,
        provenance_ids: tuple[str, ...] = (),
        capacity_delta: float | None = None,
        thermal_delta_c: float | None = None,
        workload_delta: float | None = None,
        uncertainty: float = 0.0,
    ) -> TwinResult:
        if isinstance(scenario, str):
            scenario = TwinScenario(
                scenario_id=scenario,
                baseline_generation=baseline_generation,
                hypothetical_change_id=hypothetical_change_id or "default-change",
                change_kind=change_kind,
                calibration_state=CalibrationState(calibration_state),
                provenance_ids=provenance_ids or ("default",),
            )
        if scenario is None:
            scenario = TwinScenario(
                scenario_id=scenario_id or "default-scenario",
                baseline_generation=baseline_generation,
                hypothetical_change_id=hypothetical_change_id or "default-change",
                change_kind=change_kind,
                calibration_state=CalibrationState(calibration_state),
                provenance_ids=provenance_ids or ("default",),
            )
        if not validate_twin_scenario(scenario):
            raise ValueError("twin scenario rejected")
        status = "UNKNOWN" if any(v is None for v in (capacity_delta, thermal_delta_c, workload_delta)) else "VALID"
        return TwinResult(
            result_id=f"twin:{scenario.scenario_id}",
            scenario_id=scenario.scenario_id,
            status=status,
            advisory_only=True,
            uncertainty=min(max(float(uncertainty), 0.0), 1.0),
            calibration_state=scenario.calibration_state,
            reason_codes=("SIMULATION_ONLY",),
        )
