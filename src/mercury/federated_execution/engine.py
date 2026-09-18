from mercury.federated_execution.contracts import (
    DomainClass,
    FederationCapability,
    FederationIdentity,
    FederatedPlacementDecision,
    FederatedTopologySnapshot,
    validate_federated_placement,
)


class FederatedExecutionEngine:
    def plan(
        self,
        identity: FederationIdentity | str | None = None,
        capability: FederationCapability | None = None,
        snapshot: FederatedTopologySnapshot | None = None,
        *,
        identity_id: str | None = None,
        domain_id: str | None = None,
        domain_class: DomainClass | str | None = None,
        generation: int | None = None,
        authorization_context_id: str | None = None,
        authorization_generation: int | None = None,
        capability_id: str | None = None,
        destination_domain_id: str | None = None,
        destination_domain_class: DomainClass | str | None = None,
        destination_class: DomainClass | str | None = None,
        workload_id: str | None = None,
        residency_ok: bool = True,
        auth_preserved: bool = True,
        quality_preserved: bool = True,
        provenance_ids: tuple[str, ...] = (),
    ) -> FederatedPlacementDecision:
        if identity is None:
            identity_obj = FederationIdentity(
                identity_id=identity_id or "default-identity",
                domain_id=domain_id or destination_domain_id or "local",
                domain_class=DomainClass(domain_class or DomainClass.EDGE),
                generation=generation or 0,
                authorization_context_id=authorization_context_id or "default-auth",
                authorization_generation=authorization_generation or 0,
                provenance_ids=provenance_ids or ("default",),
            )
        elif isinstance(identity, str):
            identity_obj = FederationIdentity(
                identity_id=identity,
                domain_id=domain_id or destination_domain_id or "local",
                domain_class=DomainClass(domain_class or DomainClass.EDGE),
                generation=generation or 0,
                authorization_context_id=authorization_context_id or "default-auth",
                authorization_generation=authorization_generation or 0,
                provenance_ids=provenance_ids or ("default",),
            )
        else:
            identity_obj = identity

        if capability is None:
            capability_obj = FederationCapability(
                capability_id=capability_id or "default-capability",
                domain_id=destination_domain_id or (identity_obj.domain_id if identity_obj else "default"),
                domain_class=DomainClass(destination_class or destination_domain_class or DomainClass.CLOUD),
                generation=generation or identity_obj.generation,
                residency_allowed=residency_ok,
                supports_model=True,
                supports_precision=True,
                capacity_available=True,
                latency_ms=25,
                quality_preserving=quality_preserved,
                authorization_context_id=identity_obj.authorization_context_id,
                authorization_generation=identity_obj.authorization_generation,
                provenance_ids=provenance_ids or ("default",),
            )
        else:
            capability_obj = capability

        if not residency_ok or not auth_preserved or not quality_preserved:
            raise ValueError("federated placement failed closed")

        decision = FederatedPlacementDecision(
            decision_id=f"fed-placement:{workload_id or identity_obj.identity_id}:{generation or identity_obj.generation}",
            workload_id=workload_id or identity_obj.identity_id,
            destination_domain_id=destination_domain_id or capability_obj.domain_id,
            destination_domain_class=DomainClass(destination_class or destination_domain_class or capability_obj.domain_class),
            residency_ok=residency_ok,
            auth_preserved=auth_preserved,
            quality_preserved=quality_preserved,
            generation=generation or identity_obj.generation,
            evidence_ids=provenance_ids or capability_obj.provenance_ids,
        )
        if not validate_federated_placement(decision):
            raise ValueError("federated placement rejected")
        return decision
