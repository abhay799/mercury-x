from threading import Lock
class HealingLedger:
    def __init__(self):
        self._lock=Lock(); self._ids=set(); self._events=[]
    def append(self, event_id:str, payload:dict):
        with self._lock:
            if event_id in self._ids: raise ValueError("duplicate healing event")
            self._ids.add(event_id); self._events.append((event_id, dict(payload)))
    def events(self): return tuple((i,dict(p)) for i,p in self._events)
