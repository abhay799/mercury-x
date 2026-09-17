import json
from pathlib import Path
from mercury.certification.phase17_checks import CHECKS

def evaluate():
    p=Path(__file__).parents[3]/"configs"/"certification"/"phase17.json"
    gates=json.loads(p.read_text())["required_gates"]
    if len(gates)!=len(set(gates)) or set(gates)!=set(CHECKS):
        raise ValueError("invalid phase17 manifest")
    out=[]
    for gate in gates:
        ok,evidence=CHECKS[gate]()
        if not evidence:
            raise ValueError("blank certification evidence")
        out.append((gate,bool(ok),evidence))
    return tuple(out)

def main():
    results=evaluate()
    for gate,ok,evidence in results:
        print(f"{gate}: {'PASS' if ok else 'FAIL'} - {evidence}")
    ok=all(x[1] for x in results)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
