def enforce_advisory_only(result):
    if result.advisory_only is not True:
        raise ValueError("counterfactual result must remain advisory")
    if result.calibration_state != "UNCALIBRATED":
        raise ValueError("baseline simulator cannot claim calibration")
    return True
