def fragmentation_penalty(*,required_units,free_blocks):
    if required_units<=0: raise ValueError("required_units must be positive")
    blocks=tuple(sorted(free_blocks,reverse=True))
    total=sum(blocks)
    if total<required_units: return 1.0,("INSUFFICIENT_TOTAL_CAPACITY",)
    if any(b>=required_units for b in blocks): return 0.0,("CONTIGUOUS_CAPACITY_AVAILABLE",)
    return .75,("FRAGMENTED_CAPACITY",)
