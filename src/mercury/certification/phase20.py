from pathlib import Path
from mercury.certification.phase20_checks import CHECKS
from mercury.certification.manifest import load_certification_manifest

def evaluate(manifest_path=None):
    p=Path(manifest_path) if manifest_path else Path(__file__).parents[3]/"configs"/"certification"/"phase20.json"
    gates=load_certification_manifest(p,phase=20,known_gates=CHECKS)
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
