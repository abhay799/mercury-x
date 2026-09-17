from mercury.contracts.base import ContractModel
class ObjectiveNode(ContractModel):
    node_id:str; operator:str; child_ids:tuple[str,...]=(); requirement_id:str|None=None; weight:float|None=None
def validate_objective_graph(nodes,hard_requirement_ids=()):
    by={n.node_id:n for n in nodes}
    def walk(nid,path):
        if nid in path: raise ValueError("circular objective graph")
        n=by[nid]
        if n.requirement_id in hard_requirement_ids and n.weight is not None:
            raise ValueError("HARD constraint cannot be weighted")
        for c in n.child_ids: walk(c,path|{nid})
    for nid in by: walk(nid,set())
    return tuple(sorted(by))
