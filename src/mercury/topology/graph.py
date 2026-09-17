import hashlib, json
from mercury.topology.contracts import TopologyGraph

def build_topology_graph(*, nodes, links, generation=1):
    nodes = tuple(sorted(nodes, key=lambda x: x.topology_node_id))
    links = tuple(sorted(links, key=lambda x: x.topology_link_id))
    if not nodes: raise ValueError("topology requires nodes")
    ids = [n.topology_node_id for n in nodes]
    if len(ids) != len(set(ids)): raise ValueError("duplicate topology node")
    lids = [l.topology_link_id for l in links]
    if len(lids) != len(set(lids)): raise ValueError("duplicate topology link")
    node_ids = set(ids)
    for l in links:
        if l.source_node_id not in node_ids or l.destination_node_id not in node_ids:
            raise ValueError("dangling topology link")
    body = {"nodes":[n.model_dump(mode="json") for n in nodes],
            "links":[l.model_dump(mode="json") for l in links],
            "generation":generation}
    fp = hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    gid = hashlib.sha256(("topology:"+fp).encode()).hexdigest()
    return TopologyGraph(topology_graph_id=gid,nodes=nodes,links=links,generation=generation,fingerprint=fp)
