import pytest
from mercury.morphing.contracts import MorphDimension, MorphProfileStatus, MorphPhaseStatus
def test_locked_vocabularies_are_exact():
 assert tuple(x.value for x in MorphDimension)==("DEPTH","WIDTH","EXPERT","ADAPTER","HEAD_CONTEXT")
 assert tuple(x.value for x in MorphProfileStatus)==("VALID","REJECTED")
 assert tuple(x.value for x in MorphPhaseStatus)==("READY","NOT_APPLICABLE","FAIL")
