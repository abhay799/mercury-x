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
    adj = _adj(graph)
    if source_node_id not in adj or destination_node_id not in adj:
        return None
    if source_node_id==destination_node_id: return ()
    q=deque([(source_node_id,())]); seen={source_node_id}
    while q:
        node,path=q.popleft()
        for nxt,link in adj.get(node,()):
            if nxt in seen: continue
            np=path+(link,)
            if nxt==destination_node_id: return np
            seen.add(nxt); q.append((nxt,np))
    return None

def path_capability(graph, source_node_id, destination_node_id):
    node_ids = {node.topology_node_id for node in graph.nodes}
    if source_node_id not in node_ids or destination_node_id not in node_ids:
        return TopologyCapabilityState.UNKNOWN
    p=find_path(graph,source_node_id,destination_node_id)
    if p is None: return TopologyCapabilityState.UNAVAILABLE
    return TopologyCapabilityState.AVAILABLE

def path_metrics(graph, source_node_id, destination_node_id):
    p=find_path(graph,source_node_id,destination_node_id)
    if p is None: return None
    if not p:
        return {
            "bottleneck_bandwidth_bytes_per_s": None,
            "aggregate_latency_us": None,
            "declared_bottleneck_bandwidth_bytes_per_s": None,
            "measured_bottleneck_bandwidth_bytes_per_s": None,
            "declared_aggregate_latency_us": None,
            "measured_aggregate_latency_us": None,
            "evidence_ids": (),
        }
    declared_bw = [link.declared_bandwidth_bytes_per_s for link in p]
    measured_bw = [link.measured_bandwidth_bytes_per_s for link in p]
    declared_lat = [link.declared_latency_us for link in p]
    measured_lat = [link.measured_latency_us for link in p]
    bw=[l.measured_bandwidth_bytes_per_s or l.declared_bandwidth_bytes_per_s for l in p]
    lat=[l.measured_latency_us or l.declared_latency_us for l in p]
    return {
        "bottleneck_bandwidth_bytes_per_s": min(bw) if all(x is not None for x in bw) else None,
        "aggregate_latency_us": sum(lat) if all(x is not None for x in lat) else None,
        "declared_bottleneck_bandwidth_bytes_per_s": min(declared_bw) if all(x is not None for x in declared_bw) else None,
        "measured_bottleneck_bandwidth_bytes_per_s": min(measured_bw) if all(x is not None for x in measured_bw) else None,
        "declared_aggregate_latency_us": sum(declared_lat) if all(x is not None for x in declared_lat) else None,
        "measured_aggregate_latency_us": sum(measured_lat) if all(x is not None for x in measured_lat) else None,
        "evidence_ids": tuple(sorted({evidence_id for link in p for evidence_id in link.evidence_ids})),
    }
