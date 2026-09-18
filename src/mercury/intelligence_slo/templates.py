from pydantic import Field
from mercury.contracts.base import ContractModel

class SLOTemplate(ContractModel):
    template_id:str; version:int=Field(ge=1); workload_class:str
    requirements:tuple; provenance_ids:tuple[str,...]

class SLOTemplateRegistry:
    def __init__(self): self._items={}
    def register(self,name,requirements=None):
        if isinstance(name,SLOTemplate):
            template=name; name=template.template_id; requirements=template
        if name in self._items: raise ValueError("duplicate template")
        self._items[name]=requirements if isinstance(requirements,SLOTemplate) else tuple(requirements)
    def expand(self,name):
        if name not in self._items: raise ValueError("unknown template")
        item=self._items[name]
        if isinstance(item,SLOTemplate):
            return item.requirements,tuple(sorted(item.provenance_ids+(f"template:{item.template_id}:v{item.version}",)))
        return tuple(item)
