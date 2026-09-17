from collections import deque
from mercury.topology.contracts import (
    LocalityDomain, PathResult, TopologyCapabilityState, make_path_result_id,
    path_result_fingerprint,
)
from mercury.topology.locality import classify_locality

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


def _ordered_nodes(source_node_id, links):
    current = source_node_id
    result = [current]
    for link in links:
        if link.source_node_id == current:
            current = link.destination_node_id
        elif link.bidirectional and link.destination_node_id == current:
            current = link.source_node_id
        else:
            raise ValueError("path direction does not form an ordered route")
        result.append(current)
    return tuple(result)


def build_path_result(graph, source_node_id, destination_node_id, *, provenance_ids=()):
    capability = path_capability(graph, source_node_id, destination_node_id)
    links = find_path(graph, source_node_id, destination_node_id)
    nodes_by_id = {node.topology_node_id: node for node in graph.nodes}
    if capability is TopologyCapabilityState.AVAILABLE:
        ordered_links = tuple(links)
        ordered_nodes = _ordered_nodes(source_node_id, ordered_links)
        metrics = path_metrics(graph, source_node_id, destination_node_id)
        locality = classify_locality(nodes_by_id[source_node_id], nodes_by_id[destination_node_id])
    else:
        ordered_links = ()
        ordered_nodes = ()
        metrics = None
        locality = LocalityDomain.UNKNOWN
    values = dict(
        graph_id=graph.topology_graph_id, graph_fingerprint=graph.fingerprint,
        graph_generation=graph.generation, ordered_node_ids=ordered_nodes,
        ordered_link_ids=tuple(link.topology_link_id for link in ordered_links),
        source_node_id=source_node_id, destination_node_id=destination_node_id,
        locality=locality,
        declared_aggregate_latency_us=None if metrics is None else metrics["declared_aggregate_latency_us"],
        measured_aggregate_latency_us=None if metrics is None else metrics["measured_aggregate_latency_us"],
        declared_bottleneck_bandwidth_bytes_per_s=None if metrics is None else metrics["declared_bottleneck_bandwidth_bytes_per_s"],
        measured_bottleneck_bandwidth_bytes_per_s=None if metrics is None else metrics["measured_bottleneck_bandwidth_bytes_per_s"],
        metric_evidence_ids=() if metrics is None else metrics["evidence_ids"],
        capability_state=capability, provenance_ids=tuple(provenance_ids),
    )
    draft = PathResult.model_construct(path_result_id="pending", fingerprint="pending", **values)
    fingerprint = path_result_fingerprint(draft)
    return PathResult(path_result_id=make_path_result_id(fingerprint), fingerprint=fingerprint, **values)


def validate_current_path_result(path_result, graph):
    if type(path_result) is not PathResult:
        raise ValueError("typed PathResult required")
    path_result = PathResult.model_validate(path_result.model_dump())
    if (
        path_result.graph_id != graph.topology_graph_id
        or path_result.graph_fingerprint != graph.fingerprint
        or path_result.graph_generation != graph.generation
    ):
        raise ValueError("stale path result graph generation")
    current = build_path_result(
        graph, path_result.source_node_id, path_result.destination_node_id,
        provenance_ids=path_result.provenance_ids,
    )
    if current != path_result:
        raise ValueError("stale path result does not match current graph")
    return path_result
