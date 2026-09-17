"""Executable, side-effect-free Phase 14 topology certification checks."""

from mercury.hardware_personality.contracts import HardwareEvidenceClass, HardwareTrustState, make_evidence_id
from mercury.hardware_personality.lifecycle import build_hardware_personality_profile, transition_hardware_trust
from mercury.hardware_personality.normalization import normalize_hardware_descriptor
from mercury.topology.contracts import (
    LocalityDomain, TopologyCapabilityState, TopologyGraph, TopologyLink,
    TopologyLinkKind, TopologyNode, make_topology_graph_id, make_topology_link_id,
)
from mercury.topology.graph import build_topology_graph
from mercury.topology.integration import node_from_hardware_profile
from mercury.topology.locality import classify_locality
from mercury.topology.paths import find_path, path_capability, path_metrics


def _rejects(action):
    try:
        action()
    except (TypeError, ValueError):
        return True
    return False


def _n(index, host=None):
    return TopologyNode(topology_node_id=f"n{index}", hardware_profile_id=f"p{index}", host_id=host)


def _l(a, b, *, bidirectional=True, declared_bw=None, measured_bw=None, declared_lat=None, measured_lat=None, evidence=()):
    return TopologyLink(
        topology_link_id=make_topology_link_id(a, b, TopologyLinkKind.ETHERNET, bidirectional),
        source_node_id=a, destination_node_id=b, link_kind=TopologyLinkKind.ETHERNET,
        bidirectional=bidirectional, declared_bandwidth_bytes_per_s=declared_bw,
        measured_bandwidth_bytes_per_s=measured_bw, declared_latency_us=declared_lat,
        measured_latency_us=measured_lat, evidence_ids=evidence,
    )


def _g(nodes, links=(), generation=1):
    return build_topology_graph(nodes=tuple(nodes), links=tuple(links), generation=generation)


def _profile():
    descriptor = normalize_hardware_descriptor({"hardware_class": "CPU", "vendor": "cert", "architecture": "x86", "device_family": "cpu", "device_model": "phase14"})
    eid, fingerprint = make_evidence_id(hardware_id=descriptor.hardware_id, evidence_class=HardwareEvidenceClass.PROBED, property_name="precision.FP32", source_id="phase14", sequence=1, generation=1, observed_value="supported")
    from mercury.hardware_personality.contracts import HardwareEvidenceRecord
    evidence = HardwareEvidenceRecord(evidence_id=eid, hardware_id=descriptor.hardware_id, evidence_class=HardwareEvidenceClass.PROBED, property_name="precision.FP32", observed_value="supported", source_id="phase14", probe_id="probe", sequence=1, generation=1, verification_status=True, evidence_fingerprint=fingerprint)
    return build_hardware_personality_profile(descriptor=descriptor, evidence=(evidence,), trust_state=HardwareTrustState.VERIFIED)


def exact_enums():
    valid = {x.value for x in TopologyLinkKind} == {"PCIE", "NVLINK_LIKE", "HIGH_SPEED_FABRIC", "ETHERNET", "INFINIBAND", "SHARED_MEMORY", "UNKNOWN"} and {x.value for x in LocalityDomain} == {"DEVICE", "HOST", "RACK", "ZONE", "REGION", "PROVIDER", "UNKNOWN"}
    return valid and _rejects(lambda: TopologyLinkKind("INVALID")) and _rejects(lambda: LocalityDomain("GLOBAL")), "exact vocabularies accept certified values and reject unknown values"


def graph_identity():
    graph = _g((_n(1), _n(2)), (_l("n1", "n2"),))
    payload = graph.model_dump(); payload["topology_graph_id"] = "forged"
    return graph.topology_graph_id == make_topology_graph_id(graph.fingerprint) and _rejects(lambda: TopologyGraph.model_validate(payload)), "canonical graph ID accepted and forged ID rejected"


def node_link_integrity():
    valid = _g((_n(1), _n(2)), (_l("n1", "n2"),))
    return bool(valid.links) and _rejects(lambda: _g((_n(1), _n(1)))) and _rejects(lambda: _g((_n(1),), (_l("n1", "missing"),))), "valid links accepted; duplicate nodes and dangling links rejected"


def locality():
    return classify_locality(_n(1, "host"), _n(2, "host")) is LocalityDomain.HOST and classify_locality(_n(3, "left"), _n(4, "right")) is LocalityDomain.UNKNOWN, "evidenced same-host locality and unknown locality remain distinct"


def directed_paths():
    graph = _g((_n(1), _n(2)), (_l("n1", "n2", bidirectional=False),))
    return find_path(graph, "n1", "n2") is not None and find_path(graph, "n2", "n1") is None, "directed link permits only its declared direction"


def asymmetric_links():
    graph = _g((_n(1), _n(2), _n(3)), (_l("n1", "n2"), _l("n2", "n3", bidirectional=False)))
    return find_path(graph, "n2", "n1") is not None and find_path(graph, "n3", "n1") is None, "mixed links preserve declared asymmetry"


def disconnected_graphs():
    graph = _g((_n(1), _n(2), _n(3)), (_l("n1", "n2"),))
    return path_capability(graph, "n1", "n3") is TopologyCapabilityState.UNAVAILABLE and path_capability(graph, "missing", "n1") is TopologyCapabilityState.UNKNOWN, "disconnected known endpoints unavailable; unknown endpoints unknown"


def cyclic_graphs():
    graph = _g((_n(1), _n(2), _n(3)), (_l("n1", "n2", bidirectional=False), _l("n2", "n3", bidirectional=False), _l("n3", "n1", bidirectional=False)))
    path = find_path(graph, "n1", "n3")
    return path is not None and len(path) == 2 and path_capability(graph, "n3", "n2") is TopologyCapabilityState.AVAILABLE, "cyclic physical graph terminates and retains reachability"


def multihop_paths():
    graph = _g(tuple(_n(i) for i in range(1, 5)), tuple(_l(f"n{i}", f"n{i + 1}", bidirectional=False) for i in range(1, 4)))
    path = find_path(graph, "n1", "n4")
    return path is not None and len(path) == 3 and find_path(graph, "n4", "n1") is None, "three-hop path found and reverse-only path rejected"


def deterministic_path_selection():
    nodes = tuple(_n(i) for i in range(1, 5)); links = (_l("n1", "n2", bidirectional=False), _l("n2", "n4", bidirectional=False), _l("n1", "n3", bidirectional=False), _l("n3", "n4", bidirectional=False))
    first, second = _g(nodes, links), _g(reversed(nodes), reversed(links))
    return find_path(first, "n1", "n4") == find_path(second, "n1", "n4"), "equal-hop path selection is deterministic across permutations"


def metrics_unknown():
    graph = _g((_n(1), _n(2)), (_l("n1", "n2", evidence=("link",)),))
    metrics = path_metrics(graph, "n1", "n2")
    return metrics["bottleneck_bandwidth_bytes_per_s"] is None and metrics["aggregate_latency_us"] is None and path_metrics(graph, "missing", "n2") is None, "missing metric evidence remains unknown"


def declared_measured_metrics():
    graph = _g((_n(1), _n(2)), (_l("n1", "n2", declared_bw=100, measured_bw=75, declared_lat=2.0, measured_lat=3.0, evidence=("measure",)),))
    metrics = path_metrics(graph, "n1", "n2")
    return (metrics["declared_bottleneck_bandwidth_bytes_per_s"], metrics["measured_bottleneck_bandwidth_bytes_per_s"], metrics["declared_aggregate_latency_us"], metrics["measured_aggregate_latency_us"], metrics["bottleneck_bandwidth_bytes_per_s"], metrics["aggregate_latency_us"]) == (100, 75, 2.0, 3.0, 75, 3.0), "declared and measured bandwidth/latency stay separate"


def path_provenance():
    graph = _g((_n(1), _n(2), _n(3)), (_l("n1", "n2", evidence=("e2", "e1")), _l("n2", "n3", evidence=("e3",))))
    return path_metrics(graph, "n1", "n3")["evidence_ids"] == ("e1", "e2", "e3"), "path provenance aggregates all link evidence canonically"


def phase13_integration():
    profile = _profile(); valid = node_from_hardware_profile(profile).hardware_profile_id == profile.hardware_profile_id
    stale = _rejects(lambda: node_from_hardware_profile(transition_hardware_trust(profile, HardwareTrustState.STALE)))
    raw = {field: getattr(profile, field) for field in type(profile).model_fields}; raw["profile_fingerprint"] = "forged"
    return valid and stale and _rejects(lambda: node_from_hardware_profile(type(profile).model_construct(**raw))), "valid verified profile accepted; stale and invalid Phase 13 profiles rejected"


def graph_generation():
    nodes, links = (_n(1), _n(2)), (_l("n1", "n2"),)
    return _g(nodes, links, 1).topology_graph_id != _g(nodes, links, 2).topology_graph_id and _rejects(lambda: _g(nodes, links, 0)), "generation changes identity and nonpositive generations reject"


def permutation_invariance():
    nodes, links = (_n(1), _n(2), _n(3)), (_l("n1", "n2"), _l("n2", "n3"))
    first, second = _g(nodes, links), _g(reversed(nodes), reversed(links))
    return first == second and path_metrics(first, "n1", "n3") == path_metrics(second, "n1", "n3"), "graph and path outputs are input-order invariant"


def malformed_contract_rejection():
    payload = _l("n1", "n2").model_dump(); payload["topology_link_id"] = ""
    blank_link = _rejects(lambda: TopologyLink.model_validate(payload))
    payload = _l("n1", "n2").model_dump(); payload["evidence_ids"] = ("",)
    return blank_link and _rejects(lambda: TopologyLink.model_validate(payload)), "malformed raw identity and evidence contracts reject"


def no_placement():
    payload = _n(1).model_dump(); payload["placement"] = "forbidden"
    return _rejects(lambda: TopologyNode.model_validate(payload)), "extra placement authority is rejected"


def no_scheduler():
    payload = _g((_n(1),)).model_dump(); payload["scheduler"] = "forbidden"
    return _rejects(lambda: TopologyGraph.model_validate(payload)), "extra scheduler authority is rejected"


CHECKS = {name: globals()[name] for name in (
    "exact_enums", "graph_identity", "node_link_integrity", "locality", "directed_paths", "asymmetric_links", "disconnected_graphs", "cyclic_graphs", "multihop_paths", "deterministic_path_selection", "metrics_unknown", "declared_measured_metrics", "path_provenance", "phase13_integration", "graph_generation", "permutation_invariance", "malformed_contract_rejection", "no_placement", "no_scheduler",
)}
