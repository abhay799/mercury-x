import pytest
from mercury.morphing.contracts import MorphDimension, MorphRequirement
from mercury.morphing.requirements import MorphRequirementDerivationRequest,derive_morph_requirements
def request(requirements=()): return MorphRequirementDerivationRequest(composition_id="sha256:"+"a"*64,precision_profile_id="sha256:"+"b"*64,stage_model_identities=(("stage","p","f","m","lineage","r1"),),explicit_requirements=requirements,provenance=("source",))
def policy(**updates):
 values=dict(requirement_id="req",stage_id="stage",hard_requirement_ids=("hard",),provenance=("policy",)); values.update(updates); return MorphRequirement(**values)
def test_derivation_preserves_exact_lineage_and_precision_profile():
 result=derive_morph_requirements(request())
 assert result.requirement_set.precision_profile_id.endswith("b"*64)
 assert result.requirement_set.stage_model_identities[0][-1]=="r1"
def test_explicit_allowed_denied_and_forbidden_rules_propagate():
 result=derive_morph_requirements(request((policy(morphing_forbidden=True,allowed_dimensions=(MorphDimension.DEPTH,),denied_dimensions=(MorphDimension.ADAPTER,)),)))
 item=result.requirement_set.requirements[0]
 assert item.morphing_forbidden and item.allowed_dimensions==(MorphDimension.DEPTH,) and item.denied_dimensions==(MorphDimension.ADAPTER,)
def test_unknown_stage_fails_closed():
 with pytest.raises(Exception): MorphRequirementDerivationRequest(**{**request().model_dump(),"explicit_requirements":(MorphRequirement(requirement_id="x",stage_id="other",hard_requirement_ids=("h",),provenance=("p",)),)})
