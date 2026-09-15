# MERCURY X Hardware / Cloud Strategy

## Default development path
1. Local CPU for control plane, contracts, compiler, scheduler, telemetry, tests, and small simulations.
2. Optional local/friend GPU only for light validation.
3. Kaggle or Colab for free/low-cost GPU-dependent work where suitable.
4. Paid cloud GPU only when the task cannot be validated adequately using lower-cost options.

## Provider boundary
All execution environments are represented through a provider specification. Core MERCURY logic must not assume CUDA or a local GPU exists.

## Evidence rule
Measured results and simulated results remain explicitly distinct. A simulated hardware profile must never be presented as a measured benchmark.

## Security rule
Remote providers receive only the minimum required workload/context. Credentials are referenced by secret names and are never stored in provider catalog files.

## Cost rule
Paid cloud providers are disabled by default. They must be intentionally enabled for a specific benchmark/research requirement.
