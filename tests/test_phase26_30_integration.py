from mercury.federated_execution.engine import FederatedExecutionEngine
from mercury.privacy_execution.engine import PrivacyExecutionEngine
from mercury.datacenter_twin.engine import DatacenterTwin
from mercury.control_intelligence.engine import ControlIntelligenceEngine
from mercury.platform.engine import PlatformManager


def test_phase_26_30_control_chain_is_safe_and_human_gated():
    placement = FederatedExecutionEngine().plan(
        identity_id="fed-1",
        domain_id="edge-a",
        domain_class="EDGE",
        generation=2,
        authorization_context_id="auth-edge",
        authorization_generation=1,
        capability_id="cap-1",
        destination_domain_id="cloud-b",
        destination_class="CLOUD",
        residency_ok=True,
        auth_preserved=True,
        quality_preserved=True,
        provenance_ids=("p1",),
    )
    assert placement.residency_ok is True

    privacy = PrivacyExecutionEngine().enforce(
        workload_id="job-1",
        classification="SENSITIVE",
        purpose="model-inference",
        scope="job-1",
        allow_logging=False,
        allow_cache=True,
    )
    assert privacy.enforced is True

    twin = DatacenterTwin().simulate(
        scenario_id="s-1",
        baseline_generation=3,
        hypothetical_change_id="h-1",
        change_kind="placement",
        calibration_state="UNCALIBRATED",
        provenance_ids=("p1",),
    )
    assert twin.advisory_only is True

    control = ControlIntelligenceEngine().resolve(
        objective_id="obj-1",
        objective_name="safety-first",
        hard_constraints=("privacy", "safety", "authorization"),
        evidence_quality=0.2,
        provenance_ids=("e1",),
        signals=(("resource_pressure", 0.8),),
        allow_autonomous=False,
    )
    assert control.human_escalation_required is True

    platform = PlatformManager().validate_config(
        mode="RESEARCH",
        cpu_local_demo=True,
        allow_cloud=False,
        allow_gpu=False,
        production_safe_defaults=True,
        provenance_ids=("p1",),
    )
    assert platform == "OK"
