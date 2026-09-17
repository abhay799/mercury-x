import pytest

from mercury.placement.contracts import *
from mercury.placement.predictor import predict_placements
from mercury.placement.features import extract_features
from mercury.placement.candidates import generate_typed_candidates
from mercury.topology.contracts import TopologyNode
from mercury.topology.contracts import make_topology_node_id
from mercury.topology.graph import build_topology_graph
from mercury.hardware_personality.contracts import HardwareRequirement
from tests._phase12_helpers import make_segment
from tests._phase13_helpers import profile
def test_placement_prediction_is_deterministic_and_uncalibrated():
    c=PlacementCandidate(candidate_id="c",segment_id="s",topology_node_id="n",hardware_profile_id="p",eligible=True)
    f=PlacementFeatures(candidate_id="c",compatibility_score=1,locality_score=.5,evidence_score=1,uncertainty_penalty=0)
    a=predict_placements((c,),{"c":f}); b=predict_placements((c,),{"c":f})
    assert a==b
    assert a[0].calibration_state is PlacementCalibrationState.UNCALIBRATED


def test_predictor_rejects_unbounded_backend_score():
    class InvalidBackend:
        def score(self, features):
            return 1.01

    candidate = PlacementCandidate(
        candidate_id="c", segment_id="s", topology_node_id="n", hardware_profile_id="p", eligible=True
    )
    features = PlacementFeatures(
        candidate_id="c", compatibility_score=1, locality_score=1, evidence_score=1, uncertainty_penalty=0
    )
    with pytest.raises(ValueError, match="bounded"):
        predict_placements((candidate,), {"c": features}, backend=InvalidBackend())


def test_feature_extraction_requires_active_typed_topology_nodes():
    candidate = PlacementCandidate(
        candidate_id="c", segment_id="s", topology_node_id="n", hardware_profile_id="p", eligible=True
    )
    with pytest.raises(ValueError, match="TopologyNode"):
        extract_features(candidate, source_node=object(), target_node=object())
    inactive = TopologyNode(topology_node_id="n", hardware_profile_id="p", active=False)
    with pytest.raises(ValueError, match="active"):
        extract_features(candidate, source_node=inactive, target_node=inactive)


def test_typed_generation_requires_ready_phase12_segment_and_preserves_topology_evidence():
    segment = make_segment()
    hardware_profile = profile()
    topology_node = TopologyNode(
        topology_node_id=make_topology_node_id(hardware_profile.hardware_profile_id),
        hardware_profile_id=hardware_profile.hardware_profile_id,
    )
    graph = build_topology_graph(nodes=(topology_node,), links=())
    candidates = generate_typed_candidates(
        segment=segment,
        segments=(segment,),
        handoffs=(),
        requirement=HardwareRequirement(requirement_id="r"),
        topology_graph=graph,
        source_node_id=topology_node.topology_node_id,
        profiles_by_node={topology_node.topology_node_id: hardware_profile},
    )
    assert len(candidates) == 1
    assert candidates[0].topology_graph_id == graph.topology_graph_id
    assert candidates[0].topology_generation == graph.generation


def test_prediction_preserves_backend_identity_without_claiming_calibration():
    class EmpiricalBackend:
        backend_id = "empirical-fixture"
        backend_version = "v1"

        def score(self, features):
            return 0.5

    candidate = PlacementCandidate(
        candidate_id="c", segment_id="s", topology_node_id="n", hardware_profile_id="p", eligible=True
    )
    features = PlacementFeatures(
        candidate_id="c", compatibility_score=1, locality_score=0, evidence_score=0, uncertainty_penalty=1
    )
    prediction = predict_placements((candidate,), {"c": features}, backend=EmpiricalBackend())[0]
    assert prediction.backend_id == "empirical-fixture"
    assert prediction.backend_version == "v1"
    assert prediction.calibration_state is PlacementCalibrationState.UNCALIBRATED
