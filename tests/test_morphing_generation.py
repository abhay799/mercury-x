import pytest
from mercury.morphing.contracts import ModelMorphCapability,MorphDimension,MorphRequirement
from mercury.morphing.generation import generate_morph_profiles
from mercury.morphing.registry import ModelMorphCapabilityRegistry
from mercury.morphing.requirements import MorphRequirementDerivationRequest,derive_morph_requirements
def setup(dimensions=(MorphDimension.DEPTH,)):
 req=derive_morph_requirements(MorphRequirementDerivationRequest(composition_id="sha256:"+"a"*64,precision_profile_id="sha256:"+"b"*64,stage_model_identities=(("stage","p","f","m","l","r1"),),provenance=("source",))).requirement_set
 registry=ModelMorphCapabilityRegistry(records=tuple(ModelMorphCapability(provider="p",family="f",base_model_id="m",lineage_id="l",source_revision="r1",variant_id=d.value,dimension=d,provenance=("e",)) for d in dimensions))
 return req,registry
def test_registered_profile_is_ready():
 result=generate_morph_profiles(*setup())
 assert result.status.value=="READY" and len(result.valid_profiles)==1
def test_cap_and_invalid_limits_are_fail_closed():
 req,registry=setup(tuple(MorphDimension))
 assert len(generate_morph_profiles(req,registry,max_profiles=1).valid_profiles)==1
 for cap in (0,-1,129):
  with pytest.raises(ValueError): generate_morph_profiles(req,registry,max_profiles=cap)
