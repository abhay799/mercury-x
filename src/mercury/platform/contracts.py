from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Tuple

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _fp(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class PlatformMode(str, Enum):
    RESEARCH = "RESEARCH"
    PRODUCTION = "PRODUCTION"


class PlatformStatus(str, Enum):
    OK = "OK"
    UNKNOWN = "UNKNOWN"
    FAIL = "FAIL"


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


class PlatformConfig(FrozenArtifact):
    config_id: str
    mode: PlatformMode
    cpu_local_demo: bool = True
    allow_cloud: bool = False
    allow_gpu: bool = False
    production_safe_defaults: bool = True
    provenance_ids: Tuple[str, ...] = ()
