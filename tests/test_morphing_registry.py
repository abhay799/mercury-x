from mercury.morphing.contracts import ModelMorphCapability,MorphDimension
from mercury.morphing.registry import ModelMorphCapabilityRegistry,lookup_exact_morph_capability
import pytest
def test_exact_lineage_lookup_and_revision_isolation():
 a=ModelMorphCapability(provider="p",family="f",base_model_id="m",lineage_id="l",source_revision="r1",variant_id="v",dimension=MorphDimension.DEPTH,provenance=("x",)); r=ModelMorphCapabilityRegistry(records=(a,))
 assert lookup_exact_morph_capability(r,"p","f","m","l","r1")==a
 assert lookup_exact_morph_capability(r,"p","f","m","l","r2") is None
def test_duplicates_collapse_and_conflicts_fail_closed():
 a=ModelMorphCapability(provider="p",family="f",base_model_id="m",lineage_id="l",source_revision="r1",variant_id="v",dimension=MorphDimension.DEPTH,provenance=("x",))
 assert len(ModelMorphCapabilityRegistry(records=(a,a)).records)==1
 with pytest.raises(Exception): ModelMorphCapabilityRegistry(records=(a,a.model_copy(update={"provenance":("other",)})))
