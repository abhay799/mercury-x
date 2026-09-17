import pytest

from mercury.precision.contracts import (
    ModelPrecisionCapability, PrecisionAssignment, PrecisionEvidenceConstraint,
    PrecisionMode, PrecisionProfileDraft, PrecisionRequirement,
)
from mercury.precision.compatibility import evaluate_precision_compatibility


def capability(modes=(PrecisionMode.FP32,)):
    return ModelPrecisionCapability(provider="p", model_id="m", family="f", revision="r1", supported_modes=modes, provenance=("source",))


def requirement(**updates):
    values = dict(requirement_id="req", stage_id="stage", hard_requirement_ids=("hard",), provenance=("policy",))
    values.update(updates)
    return PrecisionRequirement(**values)


def assignment(mode):
    return PrecisionAssignment(stage_id="stage", provider="p", model_id="m", family="f", revision="r1", mode=mode, hard_requirement_ids=("hard",), provenance=("candidate",))


@pytest.mark.parametrize("mode", (PrecisionMode.FP32, PrecisionMode.BF16, PrecisionMode.FP16))
def test_explicitly_supported_standard_modes_are_compatible(mode):
    result = evaluate_precision_compatibility(capability((mode,)), requirement(), assignment(mode))
    assert result.compatible


def test_reduced_precision_ban_blocks_bf16():
    assert not evaluate_precision_compatibility(capability((PrecisionMode.BF16,)), requirement(reduced_precision_forbidden=True), assignment(PrecisionMode.BF16)).compatible


def test_fp16_stability_rule_blocks_fp16():
    assert not evaluate_precision_compatibility(capability((PrecisionMode.FP16,)), requirement(fp16_forbidden=True), assignment(PrecisionMode.FP16)).compatible


def test_int8_requires_explicit_acceptable_quantization_evidence():
    plain = evaluate_precision_compatibility(capability((PrecisionMode.INT8,)), requirement(), assignment(PrecisionMode.INT8))
    proven = evaluate_precision_compatibility(capability((PrecisionMode.INT8,)), requirement(), assignment(PrecisionMode.INT8), (PrecisionEvidenceConstraint(constraint_id="q", stage_id="stage", mode=PrecisionMode.INT8, requires_evidence=True, evidence_ids=("quantization-evidence",), provenance=("source",)),))
    assert not plain.compatible
    assert proven.compatible


def test_exact_model_revision_mismatch_is_rejected():
    wrong = assignment(PrecisionMode.FP32).model_copy(update={"revision": "r2"})
    assert not evaluate_precision_compatibility(capability(), requirement(), wrong).compatible


def test_unsupported_mode_and_model_name_do_not_infer_support():
    result = evaluate_precision_compatibility(capability(), requirement(), assignment(PrecisionMode.INT8))
    assert not result.compatible


def test_compatibility_result_is_immutable_and_has_no_decision_fields():
    result = evaluate_precision_compatibility(capability(), requirement(), assignment(PrecisionMode.FP32))
    with pytest.raises(Exception): result.compatible = False
    assert {"rank", "score", "winner", "hardware", "scheduler", "runtime"}.isdisjoint(type(result).model_fields)
