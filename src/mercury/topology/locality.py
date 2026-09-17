from mercury.topology.contracts import LocalityDomain

def classify_locality(a, b):
    if a.topology_node_id == b.topology_node_id: return LocalityDomain.DEVICE
    for attr, domain in (
        ("host_id",LocalityDomain.HOST),("rack_id",LocalityDomain.RACK),
        ("zone_id",LocalityDomain.ZONE),("region_id",LocalityDomain.REGION),
        ("provider_id",LocalityDomain.PROVIDER),
    ):
        av,bv=getattr(a,attr),getattr(b,attr)
        if av is not None and bv is not None and av==bv: return domain
    return LocalityDomain.UNKNOWN
