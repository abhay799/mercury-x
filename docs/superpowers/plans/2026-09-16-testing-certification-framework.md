# Testing & Certification Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make MERCURY X preflight/phase certification explicit, machine-checkable, and fail-closed.

**Architecture:** A versioned checklist defines required certification evidence. An evaluator converts item statuses into a single result without hiding missing checks.

**Tech Stack:** Python 3.13, Pydantic v2, pytest, JSON.

**Spec:** `docs/MERCURY_X_MASTER_SPEC.md`

## Global Constraints
- Missing required evidence must fail closed.
- Unit-test success alone must not imply phase certification.
- Simulated and measured evidence remain distinct.
- Certification must be reproducible from explicit statuses and artifacts.

### Task 1: Certification models and evaluator
Implement checklist/result types and fail-closed evaluation.

### Task 2: Preflight configuration
Define the required pre-development checklist.

### Task 3: Framework tests and documentation
Verify complete pass, missing evidence, explicit failure, and duplicate-ID rejection.

## Current Verification

- [x] The checklist now represents all 21 mandatory Master Spec pre-development gates.
- [x] The artifact manifest validates required paths, readiness, and SHA-256 checksums.
- [x] `configs/certification/preflight-record.json` exists only because every
  required gate evaluated PASS with evidence.
- [x] The complete project-local regression suite reported 61 passed.
