"""Tests for deterministic, evidence-only precision requirement derivation."""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from mercury.composition.contracts import CompositionCandidate, CompositionValidity
from mercury.precision.contracts import PrecisionMode, PrecisionRequirement
from mercury.precision.requirements import (
    PrecisionRequirementDerivationRequest,
    derive_precision_requirements,
)


def candidate(*stage_ids: str) -> CompositionCandidate:
    nodes = tuple(
        SimpleNamespace(
            stage_id=stage_id,
            model_record=SimpleNamespace(
                provider="provider", model_id=f"model-{stage_id}", family="family", revision="r1"
            ),
        )
        for stage_id in stage_ids
    )
    edges = tuple(
        SimpleNamespace(source_stage_id=source, target_stage_id=target)
        for source, target in zip(stage_ids, stage_ids[1:], strict=False)
    )
    return CompositionCandidate.model_construct(
        composition_id="sha256:" + "a" * 64,
        request_id="request", workload_id="workload", session_id="session", graph_id="graph",
        pattern_id="single", topology="single", nodes=nodes, edges=edges,
        satisfied_requirement_ids=("hard-requirement",), evidence_assessments=(), provenance=("source",),
        validity=CompositionValidity.VALID, rejection_reasons=(),
    )


def requirement(stage_id: str, **updates: object) -> PrecisionRequirement:
    values: dict[str, object] = {
        "requirement_id": f"requirement-{stage_id}", "stage_id": stage_id,
        "hard_requirement_ids": ("hard-requirement",), "provenance": ("explicit-policy",),
    }
    values.update(updates)
    return PrecisionRequirement(**values)


def request(*stage_ids: str, requirements: tuple[PrecisionRequirement, ...] = ()) -> PrecisionRequirementDerivationRequest:
    return PrecisionRequirementDerivationRequest(composition=candidate(*stage_ids), explicit_requirements=requirements)


def test_derives_stable_requirement_for_a_single_certified_stage() -> None:
    result = derive_precision_requirements(request("primary"))

    assert result.requirement_set.requirements[0].stage_id == "primary"
    assert result.requirement_set.requirements[0].hard_requirement_ids == ("hard-requirement",)
    assert result.requirement_set.stage_model_identities == (("primary", "provider", "model-primary", "family", "r1"),)


def test_derives_one_requirement_per_stage_in_certified_order() -> None:
    result = derive_precision_requirements(request("primary", "verifier"))

    assert tuple(item.stage_id for item in result.requirement_set.requirements) == ("primary", "verifier")


def test_repeated_explicit_input_is_deterministic() -> None:
    first = derive_precision_requirements(request("primary", requirements=(requirement("primary"),)))
    second = derive_precision_requirements(request("primary", requirements=(requirement("primary"),)))

    assert first == second


def test_reduced_precision_prohibition_blocks_all_reduced_modes() -> None:
    result = derive_precision_requirements(request("primary", requirements=(requirement("primary", reduced_precision_forbidden=True),)))

    derived = result.requirement_set.requirements[0]
    assert {PrecisionMode.BF16, PrecisionMode.FP16, PrecisionMode.INT8}.issubset(derived.denied_modes)


def test_quantization_prohibition_blocks_int8() -> None:
    result = derive_precision_requirements(request("primary", requirements=(requirement("primary", quantization_forbidden=True),)))

    assert PrecisionMode.INT8 in result.requirement_set.requirements[0].denied_modes


def test_explicit_allow_and_deny_rules_are_preserved_as_hard_constraints() -> None:
    source = requirement("primary", allowed_modes=(PrecisionMode.FP32, PrecisionMode.BF16), denied_modes=(PrecisionMode.BF16,))
    result = derive_precision_requirements(request("primary", requirements=(source,)))

    derived = result.requirement_set.requirements[0]
    assert derived.allowed_modes == (PrecisionMode.FP32, PrecisionMode.BF16)
    assert derived.denied_modes == (PrecisionMode.BF16,)


def test_raw_text_cannot_change_precision_derivation() -> None:
    first = derive_precision_requirements(request("primary"))
    second = derive_precision_requirements(request("primary"))

    assert first == second


def test_model_and_provider_names_do_not_infer_precision_support() -> None:
    result = derive_precision_requirements(request("int8-model"))

    assert result.requirement_set.requirements[0].allowed_modes == ()


def test_missing_or_extra_explicit_stage_requirement_fails_closed() -> None:
    with pytest.raises(ValidationError, match="stage"):
        PrecisionRequirementDerivationRequest(
            composition=candidate("primary"), explicit_requirements=(requirement("other"),)
        )


def test_rejected_composition_fails_closed() -> None:
    rejected = candidate("primary").model_copy(update={"validity": CompositionValidity.REJECTED, "rejection_reasons": (SimpleNamespace(reason="bad"),)})
    with pytest.raises(ValidationError, match="valid"):
        PrecisionRequirementDerivationRequest(composition=rejected, explicit_requirements=())


def test_provenance_and_source_composition_are_preserved_without_mutation() -> None:
    source = candidate("primary")
    result = derive_precision_requirements(PrecisionRequirementDerivationRequest(composition=source, explicit_requirements=()))

    assert result.requirement_set.composition is source
    assert result.provenance
    assert source.nodes[0].model_record.revision == "r1"


def test_requirement_contracts_expose_no_later_phase_decision_fields() -> None:
    result = derive_precision_requirements(request("primary"))
    forbidden = {"rank", "score", "winner", "hardware", "placement", "scheduler", "runtime", "cost", "latency"}

    assert forbidden.isdisjoint(type(result).model_fields)
    assert forbidden.isdisjoint(type(result.requirement_set).model_fields)
