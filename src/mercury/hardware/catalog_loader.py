import json
from pathlib import Path
from mercury.hardware.provider_spec import HardwareProviderCatalog

def load_hardware_provider_catalog(path: str | Path) -> HardwareProviderCatalog:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return HardwareProviderCatalog.model_validate(payload)
