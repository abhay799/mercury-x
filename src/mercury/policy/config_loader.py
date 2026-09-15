from __future__ import annotations

import json
from pathlib import Path

from mercury.contracts.policy import PolicySet
from mercury.contracts.slo import SLODefinition


def _load_json(path: str | Path) -> dict:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"configuration root must be a JSON object: {source}")
    return data


def load_policy_set(path: str | Path) -> PolicySet:
    return PolicySet.model_validate(_load_json(path))


def load_slo_definition(path: str | Path) -> SLODefinition:
    return SLODefinition.model_validate(_load_json(path))
