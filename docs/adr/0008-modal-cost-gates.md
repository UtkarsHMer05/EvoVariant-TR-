# ADR 0008 — Modal GPU use and cost gates

- Status: ACCEPTED
- Date: 2026-08-18

## Context

Evo 2 scoring requires GPUs. The legacy system exposed an unauthenticated public
endpoint on H100 containers with no cost control. Full scoring of ~1,024 variants
(×2 orientations ×2 sequences) is a real, bounded expense that must not be triggered
accidentally, from tests, or before scientific prerequisites are met.

## Decision

Use Modal as the GPU runtime under a NEW app identity (`evovariant-tr-v2`, confirmed
at Milestone 52). Enforce staged cost gates: (1) no GPU work until image/model smoke
and official parity pass; (2) small predeclared pilots before scale; (3) resumable
sharded batch submission via Modal-native detached execution; (4) an explicit
full-run approval gate (Milestone 69) that refuses to run without an approval
artifact. The default local test command never launches paid compute; Modal/scientific
tests require explicit markers.

## Alternatives

1. Local/on-prem GPU — not available in this environment; Modal is the approved
   serverless path.
2. Keep the legacy always-on public endpoint — rejected: uncontrolled spend and no
   provenance.
3. Run the full cohort first and optimize later — rejected by the milestone order;
   pilots and cost projection precede the full run.

## Consequences

- Requires cost-control policy (Milestone 19), Modal setup (M52), clean image (M53),
  model cache volume (M54), pilots (M55-60, 67-68), approval gate (M69).
- Every GPU run is registered with projected/actual cost recorded.

## Validation

- `make validate` is CPU/local only (Milestone 20).
- Full-run command exits non-zero without the approval artifact (Milestone 69).
