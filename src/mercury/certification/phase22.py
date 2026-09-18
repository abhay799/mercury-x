from pathlib import Path
import json
from mercury.certification.phase22_checks import CHECKS

def evaluate(manifest_path=None):
    path=Path(manifest_path) if manifest_path else Path(__file__).parents[3]/"configs"/"certification"/"phase22.json"
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("invalid phase22 certification manifest") from exc
    if set(data)!={"schema_version","required_gates"}: raise ValueError("unsupported manifest fields")
    if data["schema_version"]!="phase22-cert-v1": raise ValueError("unsupported manifest schema")
    gates=data["required_gates"]
    if not isinstance(gates,list) or not gates or any(not isinstance(x,str) or not x.strip() for x in gates): raise ValueError("invalid gates")
    if len(set(gates))!=len(gates): raise ValueError("duplicate gates")
    if set(gates)!=set(CHECKS): raise ValueError("manifest/registry mismatch")
    out=[]
    for gate in gates:
        ok,evidence=CHECKS[gate]()
        if not evidence: raise ValueError("blank evidence")
        out.append((gate,bool(ok),evidence))
    return tuple(out)

def main():
    results=evaluate()
    for gate,ok,evidence in results: print(f"{gate}: {'PASS' if ok else 'FAIL'} - {evidence}")
    ok=all(x[1] for x in results); print("PASS" if ok else "FAIL"); return 0 if ok else 1

if __name__=="__main__": raise SystemExit(main())
