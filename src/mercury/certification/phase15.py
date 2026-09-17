import json
from pathlib import Path
from mercury.certification.phase15_checks import CHECKS
def evaluate():
    p=Path(__file__).parents[3]/"configs"/"certification"/"phase15.json"
    g=json.loads(p.read_text())["required_gates"]
    if set(g)!=set(CHECKS) or len(g)!=len(set(g)): raise ValueError("invalid phase15 manifest")
    return tuple((x,*CHECKS[x]()) for x in g)
def main():
    r=evaluate(); ok=all(x[1] for x in r); print("PASS" if ok else "FAIL"); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
