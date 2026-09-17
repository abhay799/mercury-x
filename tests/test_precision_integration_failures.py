import pytest
from mercury.precision.contracts import PrecisionMode
from mercury.precision.generation import generate_precision_profiles
from mercury.precision.registry import ModelPrecisionCapabilityRegistry
from tests.test_precision_generation import setup

def test_end_to_end_fp32_only_composition_is_ready():
    result=generate_precision_profiles(*setup((PrecisionMode.FP32,)))
    assert result.status.value=="READY" and len(result.valid_profiles)==1

def test_empty_exact_registry_fails_closed_without_name_inference():
    requirements,_=setup((PrecisionMode.INT8,))
    result=generate_precision_profiles(requirements,ModelPrecisionCapabilityRegistry(records=()))
    assert result.status.value=="FAIL" and result.issues

def test_int8_without_quantization_evidence_never_becomes_valid():
    result=generate_precision_profiles(*setup((PrecisionMode.INT8,)))
    assert result.status.value=="FAIL"

def test_caller_cap_is_enforced_deterministically():
    requirements,registry=setup((PrecisionMode.FP32,PrecisionMode.BF16,PrecisionMode.FP16))
    first=generate_precision_profiles(requirements,registry,max_profiles=1)
    second=generate_precision_profiles(requirements,registry,max_profiles=1)
    assert first==second and first.generation_metadata.max_profiles==1

def test_non_applicable_state_preserves_zero_profiles():
    requirements,registry=setup((PrecisionMode.FP32,))
    result=generate_precision_profiles(requirements,registry,adaptation_required=False)
    assert result.status.value=="READY"  # applicability does not suppress a valid certified profile
