# Hardware / Cloud Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Define a validated, CPU-first hardware-provider strategy that keeps remote GPU execution modular.

**Architecture:** Provider metadata is configuration-driven and separate from measured hardware profiles. The control plane can reason about provider trust, cost, GPU/CPU support, remote execution, and evidence type without implementing worker execution yet.

**Tech Stack:** Python 3.13, Pydantic v2, pytest, JSON.

**Spec:** `docs/MERCURY_X_MASTER_SPEC.md`

## Global Constraints
- Local development must not require a discrete GPU.
- Simulated and measured evidence must remain distinct.
- Paid cloud must remain disabled by default.
- Secrets must not be stored in committed provider configs.

### Task 1: Provider specification and catalog
Create provider schema and loader, then validate the baseline provider catalog.

### Task 2: Strategy tests
Verify local CPU availability, GPU-provider shape, remote execution flags, paid-cloud default state, duplicate IDs, and invalid configurations.
