from mercury.privacy_execution.contracts import DataClassification, PrivacyPolicy
from mercury.privacy_execution.engine import PrivacyExecutionEngine


def privacy_envelope():
    policy = PrivacyPolicy(
        policy_id="policy-1",
        classification=DataClassification.RESTRICTED,
        purpose="research",
        scope="job-1",
        residency_ok=True,
        retention_days=30,
        provenance_ids=("p1",),
    )
    envelope = PrivacyExecutionEngine().enforce(
        workload_id="job-1",
        classification=DataClassification.RESTRICTED,
        purpose="research",
        scope="job-1",
        allow_logging=False,
        allow_cache=True,
    )
    return envelope.enforced and envelope.redact_logs and envelope.minimum_necessary and policy.residency_ok, "privacy envelope enforces minimum necessary access and redacted logging"


CHECKS = {"privacy_envelope": privacy_envelope}
