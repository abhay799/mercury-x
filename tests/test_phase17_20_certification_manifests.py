import json
import pytest

from mercury.certification import phase17, phase18, phase19, phase20


@pytest.mark.parametrize("module,phase", ((phase17,17),(phase18,18),(phase19,19),(phase20,20)))
def test_certification_manifest_fails_closed(tmp_path,module,phase):
    malformed=tmp_path/"bad.json"
    malformed.write_text("{")
    with pytest.raises(ValueError): module.evaluate(malformed)
    unknown=tmp_path/"unknown.json"
    unknown.write_text(json.dumps({"schema_version":"mercury.certification/v1","phase":phase,"required_gates":["unknown"]}))
    with pytest.raises(ValueError): module.evaluate(unknown)
    duplicate=tmp_path/"duplicate.json"
    gates=list(module.CHECKS)
    duplicate.write_text(json.dumps({"schema_version":"mercury.certification/v1","phase":phase,"required_gates":gates+[gates[0]]}))
    with pytest.raises(ValueError): module.evaluate(duplicate)
