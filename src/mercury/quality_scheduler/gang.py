def evaluate_gang(required_candidate_ids, available_candidate_ids):
    required=set(required_candidate_ids); available=set(available_candidate_ids)
    if not required: raise ValueError("gang requires resources")
    return required.issubset(available), tuple(sorted(required-available))

def evaluate_typed_gang(requirement, *, available_candidate_ids, topology_domains):
    from mercury.quality_scheduler.contracts import GangRequirement
    if type(requirement) is not GangRequirement:
        raise ValueError("typed gang requirement required")
    required=set(requirement.required_candidate_ids); available=set(available_candidate_ids)
    missing=required-available
    wrong={candidate for candidate in required & available if topology_domains.get(candidate)!=requirement.required_topology_domain}
    return not missing and not wrong, tuple(sorted(missing|wrong))
