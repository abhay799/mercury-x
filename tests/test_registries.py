from pathlib import Path
import json
import pytest

from mercury.contracts.hardware_profile import HardwareProfile
from mercury.contracts.model_profile import ModelProfile
from mercury.registry.hardware_registry import HardwareRegistry
from mercury.registry.model_registry import ModelRegistry
from mercury.registry.catalog_loader import load_hardware_catalog, load_model_catalog
from mercury.registry.errors import DuplicateRegistryEntryError, RegistryEntryNotFoundError


def model(model_id: str, capabilities=None, precisions=None, labels=None):
    return ModelProfile(
        model_id=model_id,
        provider="simulation",
        family="test-family",
        version="1.0",
        capabilities=capabilities or ["generation"],
        supported_precisions=precisions or ["fp32"],
        context_window_tokens=4096,
        min_memory_gb=1.0,
        capability_labels=labels or ["SIMULATED"],
    )


def hardware(hardware_id: str, *, kind="CPU", memory=8.0, available=6.0,
             precisions=None, evidence="SIMULATED", labels=None):
    return HardwareProfile(
        hardware_id=hardware_id,
        provider="simulation",
        hardware_type=kind,
        memory_gb=memory,
        available_memory_gb=available,
        supported_precisions=precisions or ["fp32", "int8"],
        topology_tags=["virtual"],
        runtime_tags=["python"],
        capability_labels=labels or ["SIMULATED"],
        evidence_type=evidence,
    )


def test_model_registry_registers_and_fetches_exact_profile():
    registry = ModelRegistry()
    profile = model("model-a")
    registry.register(profile)
    assert registry.get("model-a") == profile
    assert registry.ids() == ["model-a"]


def test_model_registry_rejects_duplicate_ids_and_missing_lookup():
    registry = ModelRegistry([model("model-a")])
    with pytest.raises(DuplicateRegistryEntryError):
        registry.register(model("model-a"))
    with pytest.raises(RegistryEntryNotFoundError):
        registry.get("missing")


def test_model_registry_filters_capabilities_without_ranking():
    registry = ModelRegistry([
        model("text", capabilities=["generation"], precisions=["fp32", "int8"]),
        model("vision", capabilities=["vision", "generation"], precisions=["fp16"]),
        model("embed", capabilities=["embedding"], precisions=["fp32"]),
    ])
    matches = registry.find(required_capabilities={"generation"})
    assert [item.model_id for item in matches] == ["text", "vision"]
    assert registry.find(required_capabilities={"vision"}, required_precision="fp16")[0].model_id == "vision"


def test_hardware_registry_filters_hard_attributes_without_selecting_winner():
    registry = HardwareRegistry([
        hardware("cpu", kind="CPU", memory=16, available=12, precisions=["fp32", "int8"]),
        hardware("gpu-small", kind="GPU", memory=8, available=6, precisions=["fp16", "int8"]),
        hardware("gpu-large", kind="GPU", memory=24, available=20, precisions=["fp16", "int8"]),
    ])
    matches = registry.find(hardware_type="GPU", min_available_memory_gb=8, required_precision="fp16")
    assert [item.hardware_id for item in matches] == ["gpu-large"]


def test_hardware_registry_rejects_duplicate_ids():
    registry = HardwareRegistry([hardware("cpu")])
    with pytest.raises(DuplicateRegistryEntryError):
        registry.register(hardware("cpu"))


def test_catalog_loaders_parse_simulated_baseline_configs():
    root = Path(__file__).resolve().parents[1]
    models = load_model_catalog(root / "configs" / "registries" / "models.json")
    hardware_items = load_hardware_catalog(root / "configs" / "registries" / "hardware.json")
    assert len(models) >= 2
    assert len(hardware_items) >= 2
    assert all("SIMULATED" in item.capability_labels for item in models)
    assert all(item.evidence_type == "SIMULATED" for item in hardware_items)
