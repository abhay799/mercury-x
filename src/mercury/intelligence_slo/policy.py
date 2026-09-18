def merge_policy_layers(layers):
    merged={}
    provenance=[]
    for layer_name,requirements in layers:
        for req in requirements:
            existing=merged.get(req.metric_id)
            if existing and existing.kind.value=="HARD" and req.kind.value!="HARD":
                raise ValueError("cannot weaken inherited HARD constraint")
            merged[req.metric_id]=req
            provenance.append(f"{layer_name}:{req.requirement_id}")
    return tuple(sorted(merged.values(),key=lambda r:r.requirement_id)),tuple(provenance)

def merge_typed_policy_layers(layers):
    order={scope:index for index,scope in enumerate(PolicyScope)}
    layers=tuple(sorted(layers,key=lambda layer:order[layer.scope]))
    merged={}; provenance=[]
    for layer in layers:
        if type(layer) is not PolicyLayer: raise ValueError("typed policy layer required")
        for req in layer.requirements:
            existing=merged.get(req.metric_id)
            if existing and existing.kind is ConstraintKind.HARD:
                direction=">=" if existing.operator==">=" else "<=" if existing.operator=="<=" else None
                weakens=(req.kind is not ConstraintKind.HARD or
                         (direction==">=" and req.threshold<existing.threshold) or
                         (direction=="<=" and req.threshold>existing.threshold))
                if weakens: raise ValueError("cannot weaken inherited HARD constraint")
            merged[req.metric_id]=req
            provenance.extend((f"{layer.scope.value}:{layer.layer_id}:{req.requirement_id}",*layer.provenance_ids))
    return tuple(sorted(merged.values(),key=lambda req:req.metric_id)),tuple(sorted(set(provenance)))
from enum import Enum
from pydantic import Field
from mercury.contracts.base import ContractModel
from mercury.intelligence_slo.contracts import ConstraintKind

class PolicyScope(str,Enum):
    ORGANIZATION="ORGANIZATION"; TENANT="TENANT"; APPLICATION="APPLICATION"; WORKLOAD_CLASS="WORKLOAD_CLASS"; WORKLOAD="WORKLOAD"

class PolicyLayer(ContractModel):
    layer_id:str; scope:PolicyScope; requirements:tuple
    generation:int=Field(ge=1); provenance_ids:tuple[str,...]
    override_authority_ids:tuple[str,...]=()
