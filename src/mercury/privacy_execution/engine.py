from mercury.privacy_execution.contracts import DataClassification, PrivacyEnvelope, PrivacyPolicy


class PrivacyExecutionEngine:
    def enforce(
        self,
        *,
        workload_id: str,
        classification: DataClassification | str,
        purpose: str,
        scope: str,
        allow_logging: bool = False,
        allow_cache: bool = True,
        provenance_ids: tuple[str, ...] = (),
    ) -> PrivacyEnvelope:
        cls = DataClassification(classification) if not isinstance(classification, DataClassification) else classification
        if cls == DataClassification.UNKNOWN:
            raise ValueError("unknown privacy classification fails closed")
        if not purpose or not scope:
            raise ValueError("purpose and scope required")
        return PrivacyEnvelope(
            envelope_id=f"privacy:{workload_id}",
            workload_id=workload_id,
            classification=cls,
            purpose=purpose,
            scope=scope,
            enforced=True,
            minimum_necessary=True,
            redact_logs=not allow_logging or cls in {DataClassification.SENSITIVE, DataClassification.RESTRICTED},
            allow_cache=allow_cache,
            allow_logging=allow_logging,
            provenance_ids=provenance_ids,
        )

    def validate_policy(self, policy: PrivacyPolicy) -> bool:
        return bool(policy.classification != DataClassification.UNKNOWN and policy.residency_ok)
