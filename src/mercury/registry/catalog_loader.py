import json
from pathlib import Path

from mercury.contracts.hardware_profile import HardwareProfile
from mercury.contracts.model_profile import ModelProfile


def _read_catalog(path: str | Path) -> list[dict]:
    catalog_path = Path(path)
    with catalog_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError(f"Registry catalog must contain a JSON list: {catalog_path}")
    return payload


def load_model_catalog(path: str | Path) -> list[ModelProfile]:
    return [ModelProfile.model_validate(item) for item in _read_catalog(path)]


def load_hardware_catalog(path: str | Path) -> list[HardwareProfile]:
    return [HardwareProfile.model_validate(item) for item in _read_catalog(path)]
