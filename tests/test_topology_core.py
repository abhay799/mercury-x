import pytest
from mercury.topology.contracts import *
from mercury.topology.graph import build_topology_graph
from mercury.topology.locality import classify_locality
from mercury.topology.paths import find_path, path_metrics, path_capability
from mercury.topology.integration import node_from_hardware_profile
from mercury.hardware_personality.contracts import HardwarePersonalityProfile
from mercury.hardware_personality.lifecycle import transition_hardware_trust
from mercury.hardware_personality.contracts import HardwareTrustState
from tests._phase13_helpers import profile

def node(i,host=None):
    return TopologyNode(topology_node_id=f"n{i}",hardware_profile_id=f"p{i}",host_id=host)

def link(a,b,bw=None,lat=None,bidir=True):
    return TopologyLink(
        topology_link_id=make_topology_link_id(a,b,TopologyLinkKind.ETHERNET,bidir),
        source_node_id=a,destination_node_id=b,link_kind=TopologyLinkKind.ETHERNET,
        bidirectional=bidir,declared_bandwidth_bytes_per_s=bw,declared_latency_us=lat,
    )

def test_topology_graph_path_and_metrics():
    a,b,c=node(1,"h1"),node(2,"h1"),node(3,"h2")
    g=build_topology_graph(nodes=(c,b,a),links=(link("n1","n2",100,1),link("n2","n3",50,2)))
    assert classify_locality(a,b) is LocalityDomain.HOST
    p=find_path(g,"n1","n3")
    assert len(p)==2
    m=path_metrics(g,"n1","n3")
    assert m["bottleneck_bandwidth_bytes_per_s"]==50
    assert m["aggregate_latency_us"]==3

def test_dangling_link_fails():
    with pytest.raises(ValueError):
        build_topology_graph(nodes=(node(1),),links=(link("n1","missing"),))


def test_raw_graph_contract_rejects_integrity_bypass_and_fingerprint_tampering():
    graph = build_topology_graph(nodes=(node(1), node(2)), links=(link("n1", "n2"),))
    payload = graph.model_dump(mode="json")
    payload["nodes"].append(payload["nodes"][0])
    with pytest.raises(ValueError, match="duplicate topology node"):
        TopologyGraph.model_validate(payload)

    payload = graph.model_dump(mode="json")
    payload["fingerprint"] = "forged"
    with pytest.raises(ValueError, match="fingerprint"):
        TopologyGraph.model_validate(payload)


def test_unknown_endpoints_are_unknown_not_unavailable_or_a_zero_hop_path():
    graph = build_topology_graph(nodes=(node(1),), links=())
    assert find_path(graph, "missing", "missing") is None
    assert path_capability(graph, "missing", "n1") is TopologyCapabilityState.UNKNOWN


def test_path_metrics_preserve_declared_and_measured_evidence_separately():
    a, b = node(1), node(2)
    topology_link = TopologyLink(
        topology_link_id=make_topology_link_id("n1", "n2", TopologyLinkKind.ETHERNET, True),
        source_node_id="n1",
        destination_node_id="n2",
        link_kind=TopologyLinkKind.ETHERNET,
        bidirectional=True,
        declared_bandwidth_bytes_per_s=100,
        measured_bandwidth_bytes_per_s=75,
        declared_latency_us=2.0,
        measured_latency_us=3.0,
        evidence_ids=("e1",),
    )
    graph = build_topology_graph(nodes=(a, b), links=(topology_link,))
    metrics = path_metrics(graph, "n1", "n2")
    assert metrics["declared_bottleneck_bandwidth_bytes_per_s"] == 100
    assert metrics["measured_bottleneck_bandwidth_bytes_per_s"] == 75
    assert metrics["declared_aggregate_latency_us"] == 2.0
    assert metrics["measured_aggregate_latency_us"] == 3.0
    assert metrics["evidence_ids"] == ("e1",)


def test_directed_asymmetric_disconnected_cyclic_and_multihop_paths_are_explicit_and_deterministic():
    nodes = tuple(node(index) for index in range(1, 7))
    directed = TopologyLink(
        topology_link_id=make_topology_link_id("n1", "n2", TopologyLinkKind.PCIE, False),
        source_node_id="n1", destination_node_id="n2", link_kind=TopologyLinkKind.PCIE,
        bidirectional=False, evidence_ids=("directed",),
    )
    cycle_first = TopologyLink(
        topology_link_id=make_topology_link_id("n2", "n3", TopologyLinkKind.ETHERNET, True),
        source_node_id="n2", destination_node_id="n3", link_kind=TopologyLinkKind.ETHERNET,
        bidirectional=True, evidence_ids=("cycle-first",),
    )
    cycle_second = TopologyLink(
        topology_link_id=make_topology_link_id("n3", "n4", TopologyLinkKind.ETHERNET, True),
        source_node_id="n3", destination_node_id="n4", link_kind=TopologyLinkKind.ETHERNET,
        bidirectional=True, evidence_ids=("cycle-second",),
    )
    cycle_close = TopologyLink(
        topology_link_id=make_topology_link_id("n4", "n2", TopologyLinkKind.ETHERNET, False),
        source_node_id="n4", destination_node_id="n2", link_kind=TopologyLinkKind.ETHERNET,
        bidirectional=False, evidence_ids=("cycle-close",),
    )
    graph = build_topology_graph(
        nodes=tuple(reversed(nodes)), links=(cycle_close, cycle_second, directed, cycle_first),
    )

    assert tuple(link.topology_link_id for link in find_path(graph, "n1", "n4")) == (
        directed.topology_link_id, cycle_first.topology_link_id, cycle_second.topology_link_id,
    )
    assert find_path(graph, "n2", "n1") is None
    assert path_capability(graph, "n2", "n1") is TopologyCapabilityState.UNAVAILABLE
    assert path_capability(graph, "n1", "n6") is TopologyCapabilityState.UNAVAILABLE
    assert path_capability(graph, "missing", "n1") is TopologyCapabilityState.UNKNOWN


def test_path_selection_and_metrics_are_permutation_invariant_and_unknown_without_link_evidence():
    nodes = tuple(node(index) for index in range(1, 5))
    left = TopologyLink(
        topology_link_id=make_topology_link_id("n1", "n2", TopologyLinkKind.ETHERNET, True),
        source_node_id="n1", destination_node_id="n2", link_kind=TopologyLinkKind.ETHERNET,
        bidirectional=True, declared_bandwidth_bytes_per_s=100, declared_latency_us=2.0,
        evidence_ids=("left",),
    )
    right = TopologyLink(
        topology_link_id=make_topology_link_id("n2", "n4", TopologyLinkKind.ETHERNET, True),
        source_node_id="n2", destination_node_id="n4", link_kind=TopologyLinkKind.ETHERNET,
        bidirectional=True, declared_bandwidth_bytes_per_s=50, declared_latency_us=3.0,
        evidence_ids=("right",),
    )
    alternative = TopologyLink(
        topology_link_id=make_topology_link_id("n1", "n3", TopologyLinkKind.ETHERNET, True),
        source_node_id="n1", destination_node_id="n3", link_kind=TopologyLinkKind.ETHERNET,
        bidirectional=True, declared_bandwidth_bytes_per_s=70, declared_latency_us=1.0,
        evidence_ids=("alternative",),
    )
    alternative_end = TopologyLink(
        topology_link_id=make_topology_link_id("n3", "n4", TopologyLinkKind.ETHERNET, True),
        source_node_id="n3", destination_node_id="n4", link_kind=TopologyLinkKind.ETHERNET,
        bidirectional=True, declared_bandwidth_bytes_per_s=70, declared_latency_us=1.0,
        evidence_ids=("alternative-end",),
    )
    first = build_topology_graph(nodes=nodes, links=(left, right, alternative, alternative_end))
    second = build_topology_graph(nodes=tuple(reversed(nodes)), links=(alternative_end, alternative, right, left))
    assert find_path(first, "n1", "n4") == find_path(second, "n1", "n4")
    assert path_metrics(first, "n1", "n4") == path_metrics(second, "n1", "n4")

    unknown = build_topology_graph(nodes=(node(8), node(9)), links=(link("n8", "n9"),))
    metrics = path_metrics(unknown, "n8", "n9")
    assert metrics["bottleneck_bandwidth_bytes_per_s"] is None
    assert metrics["aggregate_latency_us"] is None
    assert metrics["evidence_ids"] == ()


def test_raw_topology_contract_rejects_blank_link_evidence_and_graph_identities():
    a, b = node(1), node(2)
    valid_link = link("n1", "n2")
    graph = build_topology_graph(nodes=(a, b), links=(valid_link,))

    link_payload = valid_link.model_dump()
    link_payload["topology_link_id"] = ""
    with pytest.raises(ValueError, match="nonblank"):
        TopologyLink.model_validate(link_payload)

    link_payload = valid_link.model_dump()
    link_payload["evidence_ids"] = ("",)
    with pytest.raises(ValueError, match="evidence"):
        TopologyLink.model_validate(link_payload)

    graph_payload = graph.model_dump()
    graph_payload["topology_graph_id"] = ""
    with pytest.raises(ValueError, match="nonblank"):
        TopologyGraph.model_validate(graph_payload)


def test_phase13_stale_and_invalid_profiles_cannot_be_integrated_into_topology():
    valid = profile()
    stale = transition_hardware_trust(valid, HardwareTrustState.STALE)
    with pytest.raises(ValueError, match="VERIFIED"):
        node_from_hardware_profile(stale)

    raw = {field_name: getattr(valid, field_name) for field_name in type(valid).model_fields}
    raw["profile_fingerprint"] = "forged"
    forged = HardwarePersonalityProfile.model_construct(**raw)
    with pytest.raises(ValueError, match="integrity"):
        node_from_hardware_profile(forged)
