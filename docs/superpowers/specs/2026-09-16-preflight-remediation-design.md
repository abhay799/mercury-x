# MERCURY X Pre-Flight Remediation Design

## Scope

This design repairs only the pre-development certification gate. It does not
implement the compiler, scheduler, runtime, workers, GPU execution, or any
Phase 0 capability.

## Decisions

### Versioned logical execution graph boundary

Add a new immutable, strict boundary contract in
`src/mercury/contracts/execution_graph.py` with schema identifier
`mercury.execution.graph/v1`. The contract has logical graph nodes, edges,
entry/terminal identities, metadata, and DAG validation. It deliberately has
no model, precision, hardware, worker, or context-placement assignment.

The existing `mercury.graph.models.AIExecutionGraph` remains unchanged. It is
a legacy mutable domain model using UUID identities and `graph_version="0.1"`;
the new contract uses string boundary identities consistent with
`ExecutionPlan`. This preserves certified behavior while adding the missing
versioned wire/boundary contract.

### Artifact manifest

Add a versioned, machine-readable artifact manifest and validator under the
certification package. Every registered artifact records the metadata required
by Master Spec section 19: name, relative path, creator, consumers, schema
version, required/optional status, checksum, version, and readiness status.
Validation rejects duplicate identifiers, paths outside the repository root,
missing required artifacts, and checksum mismatches.

### Complete preflight gate

Extend `mercury.preflight/v1` with the missing mandatory Master Spec items:
scope, dependency lock, and repository structure. Strengthen the artifact
manifest item to require an actual validated manifest. A certification record
will be written only after every required item is supported by fresh evidence.

### Reproducible local environment

The documented command will use the project-local `.venv` explicitly. Before
adding packaging metadata, the implementation will verify whether the existing
environment can build/install a normal `src` package without adding dependency
requirements. If it cannot, the remediation will use the smallest local,
documented import configuration that does not upgrade or add cloud/GPU
dependencies. Tests must prove direct interpreter import behavior rather than
only pytest path injection.

### Local Git baseline

After the first four remediation areas, initialize Git locally only if the
directory remains non-Git. No remote, credentials, push, or publication is
permitted. `.gitignore` must cover the local environment, secrets, caches,
generated artifacts, and remediation scratch state.

## Success Criteria

1. The full Master Spec pre-development gate is represented in the machine
   checklist.
2. `mercury.execution.graph/v1` validates a logical DAG and cannot contain
   physical execution-plan fields.
3. The manifest validates actual paths and checksums.
4. The documented project-local interpreter can run validation reproducibly.
5. All focused tests and the full project suite pass.
6. A certification record is created only when the evaluator reports all
   mandatory gates as PASS.
