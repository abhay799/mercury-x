from typing import Protocol
from mercury.placement.scoring import score_features
class PlacementBackend(Protocol):
    def score(self,features): ...
class DeterministicPlacementBackend:
    def score(self,features):
        return score_features(features)
