from pathlib import Path
import pytest
from mercury.hardware.catalog_loader import load_hardware_provider_catalog
from mercury.hardware.provider_spec import HardwareProviderCatalog, HardwareProviderSpec

CONFIG = Path("configs/hardware/providers.json")

def test_provider_catalog_loads_and_has_local_cpu():
    catalog = load_hardware_provider_catalog(CONFIG)
    assert catalog.get("local-cpu").provider_kind == "LOCAL_CPU"
    assert catalog.get("local-cpu").enabled is True

def test_gpu_providers_declare_gpu_support():
    catalog = load_hardware_provider_catalog(CONFIG)
    for provider in catalog.providers:
        if provider.provider_kind.endswith("_GPU"):
            assert provider.supports_gpu is True

def test_remote_gpu_providers_declare_remote_execution():
    catalog = load_hardware_provider_catalog(CONFIG)
    remote_kinds = {"KAGGLE_GPU", "COLAB_GPU", "FRIEND_GPU", "CLOUD_GPU"}
    for provider in catalog.providers:
        if provider.provider_kind in remote_kinds:
            assert provider.supports_remote_execution is True

def test_paid_cloud_is_disabled_by_default():
    catalog = load_hardware_provider_catalog(CONFIG)
    cloud = catalog.get("cloud-gpu")
    assert cloud.enabled is False
    assert cloud.cost_class == "PAID"

def test_duplicate_provider_ids_are_rejected():
    provider = HardwareProviderSpec(
        provider_id="local-cpu",
        provider_kind="LOCAL_CPU",
        trust_level="LOCAL_TRUSTED",
        supports_gpu=False,
        supports_cpu=True,
        supports_remote_execution=False,
        evidence_support="MEASURED",
        cost_class="FREE",
    )
    with pytest.raises(ValueError):
        HardwareProviderCatalog(providers=[provider, provider])

def test_invalid_remote_gpu_shape_is_rejected():
    with pytest.raises(ValueError):
        HardwareProviderSpec(
            provider_id="bad-kaggle",
            provider_kind="KAGGLE_GPU",
            trust_level="APPROVED_REMOTE",
            supports_gpu=True,
            supports_cpu=True,
            supports_remote_execution=False,
            evidence_support="MEASURED",
            cost_class="FREE",
        )
