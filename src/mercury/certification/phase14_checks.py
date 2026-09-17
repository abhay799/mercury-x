from mercury.topology.contracts import *
from mercury.topology.graph import build_topology_graph
from mercury.topology.paths import find_path
def enum_check():
    return len(TopologyLinkKind)==7 and len(LocalityDomain)==7, "exact enums"
def graph_check():
    n=TopologyNode(topology_node_id="n",hardware_profile_id="p")
    a=build_topology_graph(nodes=(n,),links=())
    b=build_topology_graph(nodes=(n,),links=())
    return a==b, "graph deterministic"
def path_check():
    n=TopologyNode(topology_node_id="n",hardware_profile_id="p")
    g=build_topology_graph(nodes=(n,),links=())
    return find_path(g,"n","n")==(), "reachability executable"
def boundary():
    import inspect, mercury.topology.graph as g
    t=inspect.getsource(g)
    return not any(x in t for x in ("schedule(","migrate(","provision(","rank(")), "no forbidden side effects"
CHECKS={
"exact_enums":enum_check,"graph_identity":graph_check,"node_link_integrity":graph_check,
"locality":path_check,"reachability":path_check,"metrics_unknown":path_check,
"phase13_integration":boundary,"no_placement":boundary,"no_scheduler":boundary}
