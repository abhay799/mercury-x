import json
from pathlib import Path
from mercury.certification.phase14_checks import CHECKS
PHASE14_CERTIFICATION_SCHEMA="mercury.phase14-certification/v1"
REQUIRED_PHASE14_GATE_IDS=tuple(CHECKS)
def evaluate(config_path: Path | None = None):
    p=config_path or Path(__file__).parents[3]/"configs"/"certification"/"phase14.json"
    try: payload=json.loads(p.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise ValueError("phase14 manifest unavailable or malformed") from exc
    if not isinstance(payload,dict) or set(payload)!={"schema_version","required_gates"} or payload.get("schema_version")!=PHASE14_CERTIFICATION_SCHEMA: raise ValueError("invalid phase14 manifest")
    gates=payload.get("required_gates")
    if not isinstance(gates,list) or any(not isinstance(g,str) or not g.strip() for g in gates) or len(gates)!=len(set(gates)) or tuple(gates)!=REQUIRED_PHASE14_GATE_IDS or tuple(CHECKS)!=REQUIRED_PHASE14_GATE_IDS: raise ValueError("invalid phase14 manifest")
    out=[]
    for g in gates:
        ok,e=CHECKS[g]()
        if not e: raise ValueError("blank evidence")
        out.append((g,bool(ok),e))
    return tuple(out)
def main():
    r=evaluate(); bad=[x for x in r if not x[1]]
    print("PASS" if not bad else "FAIL"); return 0 if not bad else 1
if __name__=="__main__": raise SystemExit(main())
