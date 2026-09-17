import pytest
from mercury.morphing.contracts import ModelMorphCapability,MorphAssignment,MorphDimension,MorphRequirement
from mercury.morphing.compatibility import evaluate_morph_compatibility
def capability(dimension): return ModelMorphCapability(provider="p",family="f",base_model_id="m",lineage_id="l",source_revision="r1",variant_id="v",dimension=dimension,provenance=("evidence",))
def requirement(): return MorphRequirement(requirement_id="req",stage_id="stage",hard_requirement_ids=("hard",),provenance=("policy",))
def assignment(dimension): return MorphAssignment(stage_id="stage",provider="p",family="f",base_model_id="m",lineage_id="l",source_revision="r1",variant_id="v",dimension=dimension,hard_requirement_ids=("hard",),provenance=("candidate",))
@pytest.mark.parametrize("dimension",tuple(MorphDimension))
def test_registered_dimension_is_compatible(dimension): assert evaluate_morph_compatibility(capability(dimension),requirement(),assignment(dimension)).compatible
def test_lineage_or_variant_mismatch_is_rejected(): assert not evaluate_morph_compatibility(capability(MorphDimension.DEPTH),requirement(),assignment(MorphDimension.WIDTH)).compatible
