class SLOTemplateRegistry:
    def __init__(self): self._items={}
    def register(self,name,requirements):
        if name in self._items: raise ValueError("duplicate template")
        self._items[name]=tuple(requirements)
    def expand(self,name):
        if name not in self._items: raise ValueError("unknown template")
        return tuple(self._items[name])
