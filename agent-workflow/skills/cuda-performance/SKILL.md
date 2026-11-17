---
name: cuda-performance
description: Use when reviewing, optimizing, or debugging CUDA performance, especially LHCb Allen trigger software or GPU-resident reconstruction code.
---

# CUDA Performance Skill

Measure before optimizing. A useful change is localized, validated, and compatible with the execution model.

## Required Context

Identify GPU model, driver/CUDA, build, exact benchmark command, input dataset/event count, baseline throughput or latency, target kernel/algorithm, memory layout, stream behavior, correctness tolerance, and profiling evidence.

For Allen, also identify sequence, algorithm, build directory, HLT1 throughput impact, Allen-managed buffers, stream ownership, and whether the change adds allocations, synchronization, or external libraries.

## Constraints

- Do not accidentally use the default stream.
- Do not add `cudaDeviceSynchronize()` or device allocation in hot paths.
- Do not introduce unmanaged memory ownership or deployment-conflicting dependencies.
- For Allen, preserve SoA conventions and existing event/block assumptions.
- Do not change physics semantics to gain speed.

## Checklist

Check indexing, bounds, coalescing, shared memory, register pressure, occupancy, warp divergence, atomics, host-device transfers, launch count, hidden synchronization, temporary allocations, data layout conversions, and numerical precision changes.

## Procedure

1. Record baseline.
2. Identify the dominant compute, memory, launch, transfer, or synchronization cost.
3. Make one meaningful change.
4. Validate against reference behavior with stated tolerances.
5. Re-measure with the same command and input.
6. Report delta and remaining bottleneck.

## Output

```markdown
Diagnosis:

- ...

Likely bottleneck:

- ...

Recommended change:

- ...

Framework constraints (when relevant):

- ...

Correctness validation:

- ...

Benchmark:

- GPU:
- Command:
- Input:
- Baseline:
- New result:
- Delta:

Risks:

- ...
```
