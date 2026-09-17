class ResourceReservationGuard:
    def __init__(self): self._claims={}
    def claim(self,resource_key,agreement_id,generation):
        current=self._claims.get(resource_key)
        if current and current[1]==generation and current[0]!=agreement_id:
            raise ValueError("exclusive resource generation already claimed")
        self._claims[resource_key]=(agreement_id,generation)
        return True
