from collections import deque
from mercury.topology.contracts import TopologyCapabilityState

def _adj(graph):
    out={n.topology_node_id:[] for n in graph.nodes}
    for l in graph.links:
        out[l.source_node_id].append((l.destination_node_id,l))
        if l.bidirectional:
            out[l.destination_node_id].append((l.source_node_id,l))
    for k in out: out[k].sort(key=lambda x:(x[0],x[1].topology_link_id))
    return out

def find_path(graph, source_node_id, destination_node_id):
    if source_node_id==destination_node_id: return ()
    adj=_adj(graph); q=deque([(source_node_id,())]); seen={source_node_id}
    while q:
        node,path=q.popleft()
        for nxt,link in adj.get(node,()):
            if nxt in seen: continue
            np=path+(link,)
            if nxt==destination_node_id: return np
            seen.add(nxt); q.append((nxt,np))
    return None

def path_capability(graph, source_node_id, destination_node_id):
    p=find_path(graph,source_node_id,destination_node_id)
    if p is None: return TopologyCapabilityState.UNAVAILABLE
    return TopologyCapabilityState.AVAILABLE

def path_metrics(graph, source_node_id, destination_node_id):
    p=find_path(graph,source_node_id,destination_node_id)
    if p is None: return None
    if not p: return {"bottleneck_bandwidth_bytes_per_s":None,"aggregate_latency_us":0.0}
    bw=[l.measured_bandwidth_bytes_per_s or l.declared_bandwidth_bytes_per_s for l in p]
    lat=[l.measured_latency_us or l.declared_latency_us for l in p]
    return {
        "bottleneck_bandwidth_bytes_per_s": min(bw) if all(x is not None for x in bw) else None,
        "aggregate_latency_us": sum(lat) if all(x is not None for x in lat) else None,
    }
