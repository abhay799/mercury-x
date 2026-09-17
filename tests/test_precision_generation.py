from itertools import islice
import pytest
from mercury.precision.contracts import ModelPrecisionCapability, PrecisionMode, PrecisionRequirement
from mercury.precision.generation import generate_precision_profiles
from mercury.precision.registry import ModelPrecisionCapabilityRegistry
from mercury.precision.requirements import PrecisionRequirementDerivationRequest, derive_precision_requirements
from tests.test_precision_requirements import candidate

def setup(modes=(PrecisionMode.FP32,), required=True):
    composition=candidate("stage")
    requirement=PrecisionRequirement(requirement_id="req",stage_id="stage",hard_requirement_ids=("hard-requirement",),provenance=("policy",))
    requirements=derive_precision_requirements(PrecisionRequirementDerivationRequest(composition=composition,explicit_requirements=(requirement,))).requirement_set
    registry=ModelPrecisionCapabilityRegistry(records=(ModelPrecisionCapability(provider="provider",model_id="model-stage",family="family",revision="r1",supported_modes=modes,provenance=("source",)),))
    return requirements,registry

def test_fp32_only_emits_one_ready_profile():
    result=generate_precision_profiles(*setup())
    assert result.status.value == "READY" and len(result.valid_profiles)==1

def test_modes_enumerate_in_canonical_nonpreferential_order():
    result=generate_precision_profiles(*setup((PrecisionMode.FP16,PrecisionMode.FP32,PrecisionMode.BF16)))
    assert [item.assignments[0].mode for item in result.valid_profiles] == [PrecisionMode.BF16,PrecisionMode.FP16,PrecisionMode.FP32]

def test_empty_exact_registry_fails_when_adaptation_required():
    requirements,_=setup()
    result=generate_precision_profiles(requirements,ModelPrecisionCapabilityRegistry(records=()))
    assert result.status.value == "FAIL"

def test_smaller_positive_limit_is_supported_and_invalid_limits_fail_closed():
    requirements,registry=setup((PrecisionMode.FP32,PrecisionMode.BF16,PrecisionMode.FP16))
    assert len(generate_precision_profiles(requirements,registry,max_profiles=1).valid_profiles)==1
    for limit in (0,-1,129):
        with pytest.raises(ValueError): generate_precision_profiles(requirements,registry,max_profiles=limit)

def test_generation_result_is_immutable_and_has_no_selection_fields():
    result=generate_precision_profiles(*setup())
    with pytest.raises(Exception): result.status="FAIL"
    assert {"rank","score","winner","hardware","scheduler","runtime"}.isdisjoint(type(result).model_fields)
