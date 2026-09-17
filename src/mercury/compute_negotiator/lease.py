def offer_is_valid(offer,*,current_generation,current_resource_snapshot_generation):
    if current_generation>offer.lease_until_generation: return False,"OFFER_EXPIRED"
    if current_resource_snapshot_generation!=offer.resource_snapshot_generation: return False,"RESOURCE_SNAPSHOT_STALE"
    return True,"OFFER_VALID"
