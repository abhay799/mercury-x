from mercury.topology.contracts import (
    TopologyGraph,
    make_topology_graph_id,
    topology_graph_fingerprint,
)

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
    fp = topology_graph_fingerprint(nodes=nodes, links=links, generation=generation)
    gid = make_topology_graph_id(fp)
    return TopologyGraph(topology_graph_id=gid,nodes=nodes,links=links,generation=generation,fingerprint=fp)
