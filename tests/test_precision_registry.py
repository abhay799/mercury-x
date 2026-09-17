"""Behavioral tests for the exact Phase 6 precision capability registry."""

from itertools import permutations

import pytest
from pydantic import ValidationError

from mercury.precision.contracts import ModelPrecisionCapability, PrecisionMode
from mercury.precision.registry import (
    ModelPrecisionCapabilityRegistry,
    PrecisionRegistryIssue,
    canonical_precision_model_identity,
    lookup_exact_precision_capability,
)


def capability(
    *,
    provider: str = "provider-a",
    model_id: str = "model-a",
    family: str = "family-a",
    revision: str = "r1",
    supported_modes: tuple[PrecisionMode, ...] = (PrecisionMode.FP32,),
    evidence_ids: tuple[str, ...] = ("evidence-a",),
    provenance: tuple[str, ...] = ("provenance-a",),
) -> ModelPrecisionCapability:
    return ModelPrecisionCapability(
        provider=provider,
        model_id=model_id,
        family=family,
        revision=revision,
        supported_modes=supported_modes,
        evidence_ids=evidence_ids,
        provenance=provenance,
    )


def test_registry_lookup_requires_exact_revision() -> None:
    first = capability(revision="r1")
    second = capability(revision="r2", supported_modes=(PrecisionMode.FP32, PrecisionMode.BF16))
    registry = ModelPrecisionCapabilityRegistry(records=(second, first))

    assert lookup_exact_precision_capability(registry, "provider-a", "model-a", "family-a", "r1") == first
    assert lookup_exact_precision_capability(registry, "provider-a", "model-a", "family-a", "r2") == second
    assert lookup_exact_precision_capability(registry, "provider-a", "model-a", "family-a", "r3") is None


def test_registry_permutation_has_same_fingerprint() -> None:
    records = (
        capability(provider="provider-b"),
        capability(provider="provider-a", model_id="model-b"),
        capability(provider="provider-a", model_id="model-a", revision="r2"),
    )

    fingerprints = {
        ModelPrecisionCapabilityRegistry(records=order).fingerprint
        for order in permutations(records)
    }

    assert len(fingerprints) == 1
    assert next(iter(fingerprints)).startswith("sha256:")


def test_conflicting_same_identity_declarations_fail_closed() -> None:
    first = capability(supported_modes=(PrecisionMode.FP32,))
    conflicting = capability(supported_modes=(PrecisionMode.FP32, PrecisionMode.INT8))

    with pytest.raises(ValidationError, match="conflicting precision declarations"):
        ModelPrecisionCapabilityRegistry(records=(first, conflicting))


def test_empty_registry_is_valid_and_exact_lookup_returns_none() -> None:
    registry = ModelPrecisionCapabilityRegistry(records=())

    assert registry.records == ()
    assert lookup_exact_precision_capability(registry, "provider", "model", "family", "revision") is None


def test_semantically_identical_duplicates_collapse_deterministically() -> None:
    record = capability()
    registry = ModelPrecisionCapabilityRegistry(records=(record, record))

    assert registry.records == (record,)


def test_registry_preserves_capability_evidence_and_provenance() -> None:
    record = capability(
        evidence_ids=("evidence-b", "evidence-a"),
        provenance=("source-b", "source-a"),
    )
    registry = ModelPrecisionCapabilityRegistry(records=(record,))

    stored = registry.records[0]
    assert stored.evidence_ids == ("evidence-a", "evidence-b")
    assert stored.provenance == ("source-a", "source-b")


def test_canonical_identity_uses_only_exact_model_identity() -> None:
    record = capability(provider="p", model_id="m", family="f", revision="r")

    assert canonical_precision_model_identity(record) == ("p", "m", "f", "r")


@pytest.mark.parametrize(
    ("provider", "model_id", "family", "revision"),
    (
        ("other", "model-a", "family-a", "r1"),
        ("provider-a", "other", "family-a", "r1"),
        ("provider-a", "model-a", "other", "r1"),
        ("provider-a", "model-a", "family-a", "other"),
    ),
)
def test_lookup_rejects_each_nonexact_identity_component(
    provider: str, model_id: str, family: str, revision: str
) -> None:
    registry = ModelPrecisionCapabilityRegistry(records=(capability(),))

    assert lookup_exact_precision_capability(registry, provider, model_id, family, revision) is None


def test_model_name_containing_int8_does_not_create_int8_support() -> None:
    record = capability(model_id="int8-ready-model", supported_modes=(PrecisionMode.FP32,))
    registry = ModelPrecisionCapabilityRegistry(records=(record,))

    assert PrecisionMode.INT8 not in registry.records[0].supported_modes


def test_provider_name_does_not_imply_precision_support() -> None:
    record = capability(provider="bf16-provider", supported_modes=(PrecisionMode.FP32,))
    registry = ModelPrecisionCapabilityRegistry(records=(record,))

    assert registry.records[0].supported_modes == (PrecisionMode.FP32,)


def test_registry_and_issues_are_immutable_and_expose_no_decision_fields() -> None:
    registry = ModelPrecisionCapabilityRegistry(records=(capability(),))
    issue = PrecisionRegistryIssue(issue_id="issue-a", reason="exact identity conflict")
    forbidden = {"rank", "score", "winner", "selected_model", "hardware", "placement", "scheduler", "runtime"}

    with pytest.raises(ValidationError):
        registry.records = ()  # type: ignore[misc]
    with pytest.raises(ValidationError):
        issue.reason = "changed"  # type: ignore[misc]
    assert forbidden.isdisjoint(ModelPrecisionCapabilityRegistry.model_fields)
    assert forbidden.isdisjoint(PrecisionRegistryIssue.model_fields)
