import pytest
from mercury.morphing.contracts import MorphDimension
from mercury.morphing.generation import generate_morph_profiles
from mercury.morphing.registry import ModelMorphCapabilityRegistry
from tests.test_morphing_generation import setup

@pytest.mark.parametrize("dimension",tuple(MorphDimension))
def test_each_registered_dimension_survives_full_generation_path(dimension):
 result=generate_morph_profiles(*setup((dimension,)))
 assert result.status.value=="READY" and result.valid_profiles[0].assignments[0].dimension is dimension

def test_missing_exact_lineage_fails_closed_when_morphing_required():
 requirements,_=setup((MorphDimension.DEPTH,))
 result=generate_morph_profiles(requirements,ModelMorphCapabilityRegistry(records=()))
 assert result.status.value=="FAIL" and result.issues

def test_non_applicable_state_is_explicit_when_no_registered_variant_exists():
 requirements,_=setup((MorphDimension.DEPTH,))
 result=generate_morph_profiles(requirements,ModelMorphCapabilityRegistry(records=()),morphing_required=False)
 assert result.status.value=="NOT_APPLICABLE"

def test_cap_and_input_permutations_are_deterministic():
 requirements,registry=setup(tuple(MorphDimension))
 first=generate_morph_profiles(requirements,registry,max_profiles=1)
 second=generate_morph_profiles(requirements,registry,max_profiles=1)
 assert first==second and first.generation_metadata.truncated

def test_result_exposes_no_forbidden_boundary_decisions():
 result=generate_morph_profiles(*setup((MorphDimension.DEPTH,)))
 forbidden={"rank","score","winner","best_morph","preferred_morph","hardware","placement","scheduler","runtime","self_modification"}
 assert forbidden.isdisjoint(type(result).model_fields)
