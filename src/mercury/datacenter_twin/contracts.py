from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Tuple

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _fp(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class CalibrationState(str, Enum):
    UNCALIBRATED = "UNCALIBRATED"
    CALIBRATED = "CALIBRATED"
    DRIFTED = "DRIFTED"


class FrozenArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    fingerprint: str | None = None

    def expected_fingerprint(self) -> str:
        return _fp(self.model_dump(mode="json", exclude={"fingerprint"}))

    @model_validator(mode="after")
    def _seal(self):
        expected = self.expected_fingerprint()
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint mismatch")
        return self


class TwinScenario(FrozenArtifact):
    scenario_id: str
    baseline_generation: int = Field(ge=0)
    hypothetical_change_id: str
    change_kind: str
    calibration_state: CalibrationState = CalibrationState.UNCALIBRATED
    provenance_ids: Tuple[str, ...]


class TwinResult(FrozenArtifact):
    result_id: str
    scenario_id: str
    status: str = "VALID"
    advisory_only: bool = True
    uncertainty: float = Field(ge=0, le=1)
    calibration_state: CalibrationState = CalibrationState.UNCALIBRATED
    reason_codes: Tuple[str, ...] = ()


def validate_twin_scenario(scenario: TwinScenario) -> bool:
    return bool(scenario.provenance_ids and scenario.hypothetical_change_id)
