MERCURY X — Phase 13 Hardware Personality Engine Design

Date: 2026-09-17
Status: Approved architecture
Phase: 13 — Hardware Personality Engine

1. Purpose

Phase 13 builds a deterministic hardware-intelligence layer that understands compute devices and exposes their capabilities, constraints, evidence, and workload affinities as a certified hardware personality.

Its responsibility is to answer:

what hardware exists

what class and architecture it belongs to

what capabilities it declares

what capabilities can be probed

what performance has actually been measured

which precisions and runtime features are supported

which workload families it is suitable for

how trustworthy and fresh the profile is

Phase 13 does not place or schedule workloads.

2. Position in MERCURY X

Static Hardware Descriptor
        +
Runtime Capability Probe
        +
Benchmark / Measurement Evidence
        +
Provider Metadata
        ↓
Hardware Normalization Layer
        ↓
Hardware Personality Profile
        ↓
Capability Matrix
        ↓
Workload Affinity Model
        ↓
Constraint / Compatibility Engine
        ↓
Certified Hardware Personality
        ↓
Phase 14 Topology-Aware Compute
Phase 15 Predictive Compute Placement
Phase 18 Quality-Aware Scheduling
Phase 21 Live AI Workload Migration

3. Fundamental Rule

Hardware personality describes capability, constraints, and evidence; it never performs placement or scheduling.

4. Architectural Boundary

Phase 13 owns:

hardware descriptors

normalized hardware identity

capability probes

evidence records

precision support

memory/runtime/interconnect capabilities

hardware trust state

workload affinity

compatibility evaluation

profile lifecycle

deterministic profile identity/fingerprints

Phase 13 does not own:

model selection

precision selection

provider selection

region selection

machine placement

topology optimization

scheduling

migration

cost negotiation

fleet balancing

autonomous scaling

5. Hardware Classes

Exactly:

CPU
GPU
TPU
NPU
OTHER_ACCELERATOR

Vendor/device details belong in fields, not the top-level class enum.

6. Evidence Classes

Exactly:

DECLARED
PROBED
MEASURED
DERIVED

DECLARED

Vendor/provider or static descriptor data.

PROBED

Observed runtime capability detected from the local or remote execution environment.

MEASURED

Observed benchmark/result evidence.

DERIVED

Deterministic conclusions derived from other evidence.

Declared and measured values must remain distinguishable.

7. Trust States

Exactly:

UNVERIFIED
VERIFIED
STALE
INVALID

UNVERIFIED

Profile exists but has not met certification requirements.

VERIFIED

Profile evidence and structural checks satisfy the certified baseline.

STALE

Profile was previously valid but its evidence is no longer fresh enough for certified use.

INVALID

Profile failed integrity, compatibility, or revocation checks.

8. Capability Support State

Exactly:

CAPABLE
INCAPABLE
UNKNOWN

Absence of evidence must map to UNKNOWN, not INCAPABLE.

9. Precision Capabilities

Certified baseline precision identifiers:

FP32
TF32
FP16
BF16
FP8
INT8
INT4

Precision capability means support, not selection.

Phase 6 remains responsible for adaptive precision decisions.

10. Hardware Personality Profile

The primary Phase 13 object is the Hardware Personality Profile.

It must include at minimum:

hardware_profile_id
hardware_id
hardware_class
vendor
architecture
device_family
device_model
compute_capabilities
supported_precisions
memory_capacity_bytes
declared_memory_bandwidth_bytes_per_s
measured_memory_bandwidth_bytes_per_s
interconnect_capabilities
host_memory_relationship
runtime_capabilities
software_stack
power_constraints
virtualization_state
evidence_record_ids
workload_affinities
profile_generation
profile_fingerprint
trust_state

Fields unsupported by evidence must remain explicitly unknown rather than fabricated.

11. Hardware Descriptor

A normalized hardware descriptor represents identity and static characteristics.

At minimum:

hardware_id
hardware_class
vendor
architecture
device_family
device_model
memory_capacity_bytes
provider_id
region_id
instance_type
virtualization_state

Provider/region fields may be present as metadata but may not be used to perform placement.

12. Deterministic Identity

Equivalent inputs must produce identical:

hardware profile IDs

evidence record IDs

capability IDs

profile fingerprints

compatibility results

workload affinity outputs

Identity must never depend on:

random UUIDs

wall-clock time

process identity

machine-local filesystem ordering

Python hash()

nondeterministic probe order

Use canonical JSON + SHA-256.

13. Evidence Record Contract

Each hardware evidence record must preserve:

evidence_id
hardware_id
evidence_class
property_name
declared_value
observed_value
unit
source_id
probe_id
benchmark_id
sequence
generation
verification_status
evidence_fingerprint

Only fields appropriate to the evidence class may be populated.

Evidence may not silently overwrite other evidence.

14. Declared vs Measured Separation

Example:

declared_memory_bandwidth_bytes_per_s = X
measured_memory_bandwidth_bytes_per_s = Y

They are independent values.

Phase 13 must never replace declared evidence with measured evidence or vice versa.

Derived values may reference both but must preserve lineage.

15. Runtime Capability Probe

A probe is a deterministic capability observation mechanism.

Examples include:

CPU ISA capability

accelerator presence

runtime framework availability

precision support

memory availability

driver/runtime presence

device count

local interconnect presence

CPU-first baseline probes must work without discrete GPU hardware.

GPU/TPU/NPU behavior may be exercised using fixtures until real hardware is available.

16. Probe Safety

Probes must:

be read-only

avoid destructive stress testing

avoid configuration mutation

avoid provider billing actions

avoid cloud instance creation

avoid privileged operations where unnecessary

fail closed on malformed outputs

17. Runtime Capability Matrix

The capability matrix must represent support for properties such as:

supports_fp32
supports_tf32
supports_fp16
supports_bf16
supports_fp8
supports_int8
supports_int4
supports_tensor_core_like_acceleration
supports_peer_to_peer
supports_unified_memory
supports_remote_execution
supports_virtualization
supports_partitioning

Each capability must use CAPABLE, INCAPABLE, or UNKNOWN.

18. Memory Capability Model

Phase 13 may describe:

memory_capacity_bytes
declared_memory_bandwidth_bytes_per_s
measured_memory_bandwidth_bytes_per_s
host_memory_relationship
memory_access_model
memory_partitioning

Measured values must include evidence lineage.

No memory benchmark may be invented.

19. Interconnect Capability Model

Phase 13 may represent:

pcie_generation
pcie_lanes
nvlink_like_support
fabric_support
peer_to_peer_support
network_transport_capabilities

The existence of a capability does not imply topology placement.

Phase 14 owns topology-aware compute.

20. Software Stack Model

The profile may include:

driver_identity
runtime_identity
runtime_version
compiler_stack
framework_support
kernel_capabilities

Software-stack support is evidence-backed.

Missing software must not automatically imply the physical hardware lacks the underlying capability.

21. Virtualization State

Phase 13 may distinguish:

BARE_METAL
VIRTUAL_MACHINE
CONTAINERIZED
PARTITIONED_ACCELERATOR
UNKNOWN

Virtualization affects capability evidence but does not determine placement.

22. Workload Affinity Dimensions

Exactly these certified baseline dimensions:

PREFILL_AFFINITY
DECODE_AFFINITY
EMBEDDING_AFFINITY
TRAINING_AFFINITY
FINE_TUNING_AFFINITY
RETRIEVAL_AFFINITY
TOOL_WORKLOAD_AFFINITY
MEMORY_INTENSITY_TOLERANCE
COMMUNICATION_INTENSITY_TOLERANCE

Affinity is derived from certified hardware evidence.

23. Affinity Scale

Use exactly:

LOW
MEDIUM
HIGH
UNKNOWN

Affinity is not a placement decision.

UNKNOWN must be used when evidence is insufficient.

24. Affinity Rules

Derived workload affinity must be:

deterministic

explainable

evidence-backed

bounded

independent of current scheduler state

independent of cloud price

independent of current queue length

independent of user identity

No hidden ML predictor is required for Phase 13 baseline.

25. Compatibility Engine

The compatibility engine answers whether a hardware personality satisfies explicit workload requirements.

Baseline result states:

COMPATIBLE
INCOMPATIBLE
UNKNOWN

Compatibility may evaluate:

hardware class

required precision

minimum memory

runtime requirement

accelerator requirement

external tool/runtime access

virtualization restriction

It must not choose the best device.

26. Resource Requirements Integration

Phase 12 execution segments may expose declarative requirements.

Phase 13 may evaluate those requirements against a hardware personality.

Conceptually:

Phase 12 Requirement
        +
Phase 13 Hardware Personality
        ↓
Compatibility Result

This is a compatibility check only.

Actual hardware selection belongs to later phases.

27. Profile Lifecycle

Profile lifecycle is driven by explicit evidence generations.

A profile may transition:

UNVERIFIED → VERIFIED
VERIFIED → STALE
UNVERIFIED → INVALID
VERIFIED → INVALID
STALE → VERIFIED
STALE → INVALID

INVALID is terminal for that profile generation.

A new generation may be produced from new evidence.

28. Staleness

Staleness must be deterministic.

Do not call datetime.now() inside profile evaluation.

Use explicit generation/sequence/reference metadata.

If evidence freshness cannot be determined, trust must not be upgraded silently.

29. Profile Generation

Each meaningful evidence refresh creates a new profile generation.

Previous generations remain auditable.

No in-place historical rewrite.

30. Profile Fingerprint

The profile fingerprint must cover canonical:

normalized descriptor

capabilities

precision support

memory fields

runtime/software-stack fields

evidence IDs

workload affinities

generation

trust state

Equivalent profiles must fingerprint identically.

31. Conflict Handling

Evidence may disagree.

Examples:

DECLARED: BF16 supported
PROBED: BF16 unavailable

Conflicts must remain visible.

Phase 13 must not silently collapse disagreement.

Certified resolution rules must preserve:

all source evidence IDs

evidence classes

verification status

conflict reason

resulting support state

A genuine unresolved conflict should normally produce UNKNOWN rather than fabricated certainty.

32. Measurement Evidence

Measurements must contain:

benchmark identity

input size/configuration

observed metric

units

hardware ID

runtime/software context

evidence fingerprint

No synthetic value may be marked as measured production evidence.

Fixtures in tests must be clearly test-only.

33. CPU-First Development

All Phase 13 control-plane logic must run on the user's CPU-only laptop.

Baseline certification must not require:

CUDA

Triton

vLLM

NVIDIA GPU

TPU

NPU

RDMA

multi-GPU

Synthetic fixtures may represent unavailable hardware classes.

Real GPU/cloud evidence can be added later without changing contracts.

34. Local CPU Personality

The implementation should support a real CPU-only personality path so Phase 13 is not fixture-only.

A local CPU profile may use read-only system/runtime probes that are available without privileged actions.

The test suite must remain deterministic by isolating live probes behind adapters and fixtures.

35. Provider Metadata

Provider metadata may describe a hardware offering.

It may include:

provider_id
instance_type
region_id
declared_hardware
declared_memory
declared_accelerator_count

Phase 13 must not:

rank providers

compare prices

choose providers

provision instances

36. Forbidden Responsibilities

Phase 13 must not:

choose a model

rank models

select precision

convert precision

choose hardware for execution

choose provider

choose region

optimize topology

schedule jobs

migrate workloads

rebalance clusters

negotiate cost

optimize fleet utilization

provision infrastructure

autonomously scale infrastructure

create personal/user profiles

37. Task Structure

Phase 13 uses exactly eight implementation tasks.

Task 1 — Hardware Personality Contract Baseline

Create:

hardware enums

evidence enums

trust states

capability states

affinity dimensions/scales

descriptor contracts

evidence contracts

personality profile

deterministic ID helpers

Task 2 — Hardware Descriptor & Normalization Engine

Implement:

descriptor normalization

canonical vendor/architecture/device fields

exact identity

deterministic ordering

malformed descriptor rejection

Task 3 — Capability Probe & Evidence Model

Implement:

probe adapter boundary

CPU-safe probe implementation

synthetic accelerator fixtures

evidence record construction

declared/probed/measured/derived separation

Task 4 — Precision / Memory / Runtime Capability Matrix

Implement:

precision capabilities

memory capabilities

runtime/software support

interconnect capabilities

conflict-aware support resolution

Task 5 — Workload Affinity & Compatibility Engine

Implement:

affinity derivation

evidence-backed reasons

compatibility states

Phase 12 requirement compatibility

no placement/ranking behavior

Task 6 — Profile Lifecycle, Trust & Deterministic Identity

Implement:

verification

staleness

invalidation

generation updates

deterministic fingerprinting

immutable history

Task 7 — Integration & Adversarial Hardening

Exercise:

real CPU path

GPU/TPU/NPU synthetic fixtures

conflicting evidence

missing evidence

unsupported precision

stale evidence

invalid evidence

provider metadata boundaries

Phase 12 compatibility

no scheduler/placement leakage

Task 8 — Phase 13 Certification

Create:

configs/certification/phase13.json
src/mercury/certification/phase13.py
tests/test_phase13_certification.py

Certification must fail closed.

38. Certification Gates

At minimum verify:

exact hardware classes

exact evidence classes

exact trust states

exact capability states

exact precision identifiers

exact affinity dimensions

exact affinity scale

deterministic hardware identity

deterministic evidence identity

deterministic profile identity

deterministic profile fingerprint

descriptor normalization

declared/measured separation

evidence lineage

evidence conflict preservation

unknown-on-insufficient-evidence

precision capability resolution

memory capability handling

runtime capability handling

software-stack handling

interconnect capability handling

virtualization handling

CPU-first probe path

synthetic accelerator fixtures

affinity determinism

affinity evidence reasons

compatibility determinism

compatibility unknown behavior

Phase 12 requirement integration

profile generation

trust transitions

deterministic staleness

invalid profile terminality

no model selection

no precision selection

no provider selection

no region selection

no hardware placement

no global scheduling

no migration

no autonomous scaling

adversarial integration

39. Testing Strategy

Every implementation task follows:

RED
→ verify expected failure
→ minimal GREEN
→ focused tests
→ full regression once
→ checkpoint

Fast-track bundles may group related files, but final verification requires:

focused Phase 13 suite

Phase 13 certification PASS

Phase 12 compatibility tests

full MERCURY regression

clean Git status

40. Completion Definition

Phase 13 is complete only when:

all eight tasks are implemented

all focused Phase 13 tests pass

certification returns PASS

Phase 12 compatibility remains green

full repository regression is green

working tree is clean

no scheduler, placement, migration, or provider-selection responsibility leaks into Phase 13

Phase 14 may then consume certified hardware personalities for topology-aware compute.