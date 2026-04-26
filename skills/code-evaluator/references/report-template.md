---
name: report-template
description: Report templates for whole-codebase evaluation and change review modes.
---

# Report Template

Use these structures as output contracts. Keep reports concise enough to act on, but include evidence paths and confidence.

## Whole-Codebase Evaluation

```md
# Code Evaluation Report

## Executive Summary

- Overall score: X/10 (`provisional` if applicable)
- Confidence: high | medium | low
- License/distribution verdict: short triage status, not legal advice
- Top 3 risks:

## Scope and Assumptions

- Target:
- Mode:
- Mode trigger:
- Distribution context assumptions:
- Project-specific rules considered:
- Framework/library versions and references consulted, if applicable:

## Sampling Plan

- Core areas:
- Boundary areas:
- High-risk areas:
- Dependency/license surfaces:
- Areas intentionally not inspected:

## Evidence Coverage

- Files/directories inspected:
- Manifests/lockfiles inspected:
- CI/CD, build, and deployment config inspected:
- Docs inspected:
- Commands run:
- Areas not inspected:
- Confidence impact:

## Checks Run

| Command | Result | Notes |
|---|---|---|

## Checks Not Run

| Check | Reason | Confidence impact |
|---|---|---|

## Pillar Scores

| Pillar | Score | Confidence | Notes |
|---|---:|---|---|
| Architecture and boundaries | X/10 | high/medium/low | |
| Implementation quality | X/10 | high/medium/low | |
| Tests and verification | X/10 | high/medium/low | |
| Documentation | X/10 | high/medium/low | |
| Dependency necessity | X/10 | high/medium/low | |
| Security and reliability | X/10 | high/medium/low | |
| AI/LLM ergonomics | X/10 | high/medium/low | |

Confidence must reflect evidence coverage: use `low` for narrow sampling or missing core areas, `medium` for representative but incomplete evidence, and `high` only when inspected evidence and relevant checks support the claim.

## Positive Signals

- ...

## Issues and Risks

### [P0/P1/P2/P3] Title

Evidence:
- ...

Impact:
- ...

Recommended next action:
- ...

Confidence:
- High | Medium | Low

## Dependency Triage

| Dependency | Class | Evidence | Concern | Recommendation | Confidence |
|---|---|---|---|---|---|

## License / Distribution Triage

| Component | Distribution context | License signal | Evidence | Status | Confidence |
|---|---|---|---|---|---|

## Project-Specific Compliance

- ...

## Spec / Policy Conflicts

- ...

## What I Would Not Preserve

Design opinion only; not a deletion/refactor mandate.

- ...

## Recommended Next Actions

Use risk/design priority, not human work phasing.

1. [P0/P1/P2/P3] ...

## Known Limitations

- ...
```

## Change Review Mode

Start with findings:

```md
# Code Evaluation Change Review

## Findings

### [P0/P1/P2/P3] Title

Evidence:
- `path/file.ext:line`

Impact:
- ...

Recommended next action:
- ...

Confidence:
- High | Medium | Low

## Missing Tests

- ...

## Evidence Coverage

- Diff files inspected:
- Directly coupled files inspected:
- Areas intentionally not inspected:
- Confidence impact:

## Open Questions

- ...

## Checks Run / Not Run

- ...

## Summary

- Overall risk:
- Confidence:
```

If there are no findings, state that clearly and still report checks, coverage, and residual risk.
