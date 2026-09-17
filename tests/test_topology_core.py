import pytest
from mercury.topology.contracts import *
from mercury.topology.graph import build_topology_graph
from mercury.topology.locality import classify_locality
from mercury.topology.paths import find_path, path_metrics

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
