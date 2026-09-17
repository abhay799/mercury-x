import json
from pathlib import Path
from mercury.certification.phase16_checks import CHECKS
PHASE16_CERTIFICATION_SCHEMA="mercury.phase16-certification/v1"
REQUIRED_PHASE16_GATE_IDS=tuple(CHECKS)
def evaluate(config_path: Path | None = None):
    p=config_path or Path(__file__).parents[3]/"configs"/"certification"/"phase16.json"
    try: payload=json.loads(p.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise ValueError("phase16 manifest unavailable or malformed") from exc
    if not isinstance(payload,dict) or set(payload)!={"schema_version","required_gates"} or payload.get("schema_version")!=PHASE16_CERTIFICATION_SCHEMA: raise ValueError("invalid phase16 manifest")
    g=payload.get("required_gates")
    if not isinstance(g,list) or any(not isinstance(x,str) or not x.strip() for x in g) or len(g)!=len(set(g)) or tuple(g)!=REQUIRED_PHASE16_GATE_IDS or tuple(CHECKS)!=REQUIRED_PHASE16_GATE_IDS: raise ValueError("invalid phase16 manifest")
    out=[]
    for x in g:
        passed,evidence=CHECKS[x]()
        if not isinstance(evidence,str) or not evidence.strip(): raise ValueError("blank certification evidence")
        out.append((x,bool(passed),evidence))
    return tuple(out)
def main():
    r=evaluate(); ok=all(x[1] for x in r); print("PASS" if ok else "FAIL"); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
