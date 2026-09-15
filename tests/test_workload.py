from mercury.contracts.workload import (
    CognitiveWorkload,
    ComputeRequirement,
    Modality,
    PrivacyLevel,
    ReasoningLevel,
    WorkloadConstraints,
)


def test_create_multimodal_workload():
    workload = CognitiveWorkload(
        intent="multimodal_financial_analysis",
        modalities=[
            Modality.DOCUMENT,
            Modality.IMAGE,
        ],
        compute_requirements=[
            ComputeRequirement.DOCUMENT_PARSING,
            ComputeRequirement.RETRIEVAL,
            ComputeRequirement.VISION,
            ComputeRequirement.REASONING,
            ComputeRequirement.VERIFICATION,
            ComputeRequirement.GENERATION,
        ],
        reasoning_level=ReasoningLevel.HIGH,
        priority=90,
        constraints=WorkloadConstraints(
            max_latency_ms=8000,
            max_cost=0.50,
            min_quality=0.93,
            min_reliability=0.95,
            privacy_level=PrivacyLevel.PRIVATE,
        ),
        requires_verification=True,
    )

    assert workload.intent == "multimodal_financial_analysis"
    assert workload.priority == 90
    assert workload.constraints.min_quality == 0.93
    assert workload.requires_verification is True
    assert Modality.IMAGE in workload.modalities
    assert ComputeRequirement.REASONING in workload.compute_requirements
