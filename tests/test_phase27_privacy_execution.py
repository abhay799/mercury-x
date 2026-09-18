import pytest

from mercury.privacy_execution.contracts import (
    DataClassification,
    PrivacyEnvelope,
    PrivacyPolicy,
    evaluate_privacy_policy,
)
from mercury.privacy_execution.engine import PrivacyExecutionEngine


def test_privacy_policy_fails_closed_on_unknown_classification():
    policy = PrivacyPolicy(
        policy_id="policy-1",
        classification=DataClassification.SENSITIVE,
        purpose="model-inference",
        scope="job-1",
        residency_ok=True,
        retention_days=30,
        provenance_ids=("p1",),
    )
    assert evaluate_privacy_policy(policy, classification=DataClassification.SENSITIVE)
    assert not evaluate_privacy_policy(policy, classification=None)


def test_privacy_envelope_restricts_access_and_logging():
    envelope = PrivacyExecutionEngine().enforce(
        workload_id="job-1",
        classification=DataClassification.RESTRICTED,
        purpose="research",
        scope="job-1",
        allow_logging=False,
        allow_cache=True,
    )
    assert envelope.enforced
    assert envelope.redact_logs is True
    assert envelope.minimum_necessary is True
