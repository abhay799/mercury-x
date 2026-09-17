def evaluate_gang(required_candidate_ids, available_candidate_ids):
    required=set(required_candidate_ids); available=set(available_candidate_ids)
    if not required: raise ValueError("gang requires resources")
    return required.issubset(available), tuple(sorted(required-available))
