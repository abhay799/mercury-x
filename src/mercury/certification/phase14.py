import json
from pathlib import Path
from mercury.certification.phase14_checks import CHECKS
def evaluate(config_path: Path | None = None):
    p=config_path or Path(__file__).parents[3]/"configs"/"certification"/"phase14.json"
    gates=json.loads(p.read_text())["required_gates"]
    if len(gates)!=len(set(gates)) or set(gates)!=set(CHECKS): raise ValueError("invalid phase14 manifest")
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
