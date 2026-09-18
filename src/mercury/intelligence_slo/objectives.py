from mercury.contracts.base import ContractModel
from enum import Enum
class ObjectiveOperator(str,Enum):
    AND="AND"; OR="OR"; WEIGHTED_SOFT="WEIGHTED_SOFT"; REQUIREMENT="REQUIREMENT"
class ObjectiveNode(ContractModel):
    node_id:str; operator:ObjectiveOperator; child_ids:tuple[str,...]=(); requirement_id:str|None=None; weight:float|None=None
def validate_objective_graph(nodes,hard_requirement_ids=()):
    nodes=tuple(nodes)
    by={n.node_id:n for n in nodes}
    if len(by)!=len(nodes): raise ValueError("duplicate objective node")
    def walk(nid,path):
        if nid in path: raise ValueError("circular objective graph")
        if nid not in by: raise ValueError("dangling objective node")
        n=by[nid]
        if n.requirement_id in hard_requirement_ids and n.weight is not None:
            raise ValueError("HARD constraint cannot be weighted")
        for c in n.child_ids: walk(c,path|{nid})
    for nid in by: walk(nid,set())
    return tuple(sorted(by))
