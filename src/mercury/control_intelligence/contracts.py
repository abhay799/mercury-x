from __future__ import annotations

import hashlib
import json
from typing import Tuple

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _fp(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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


class ControlObjective(FrozenArtifact):
    objective_id: str
    name: str
    hard_constraints: Tuple[str, ...]
    evidence_quality: float = Field(ge=0.0, le=1.0)
    provenance_ids: Tuple[str, ...]


class ControlSignal(FrozenArtifact):
    signal_id: str
    name: str
    value: float
    provenance_ids: Tuple[str, ...]


class ControlDecision(FrozenArtifact):
    decision_id: str
    objective_id: str
    action: str
    human_escalation_required: bool = True
    reason_codes: Tuple[str, ...] = ()
    evidence_quality: float = 0.0
    allowed_autonomous: bool = False
