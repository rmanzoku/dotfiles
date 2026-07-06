---
name: report-template
description: Report templates for code-evaluator modes.
version: "2.0"
updated: 2026-07-05
---

# Report Template

Use these structures as output contracts. Keep reports concise enough to act on, but include evidence paths and confidence.

Every artifact under `.context/code-evaluator/<task>/` starts with front matter
containing `task`, `phase_or_step` (the artifact filename stem), and
`created_at`; `report.md` adds `mode`, as shown below.

## Whole-Codebase Evaluation

```md
---
task: <task-slug>
phase_or_step: report
created_at: <ISO-8601 timestamp>
mode: whole-codebase-evaluation
---

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
| Future-context fit | X/10 | high/medium/low | |

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

Revisit conditions:
- (P0/P1 only) ...

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
---
task: <task-slug>
phase_or_step: report
created_at: <ISO-8601 timestamp>
mode: change-review
---

# Code Evaluation Change Review

## Findings

### [P0/P1/P2/P3] Title

Evidence:
- `path/file.ext:line`

Impact:
- ...

Recommended next action:
- ...

Revisit conditions:
- (P0/P1 only) ...

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

## License Audit Mode

```md
---
task: <task-slug>
phase_or_step: report
created_at: <ISO-8601 timestamp>
mode: license-audit
---

# Code Evaluation License Audit

## Executive Summary

- Verdict: accepted-signal | accepted-with-remediation-evidence | needs-confirmation | blocker
- Confidence: high | medium | low
- Distribution context:
- Top blockers or needs-confirmation items:

## Scope and Assumptions

- Target:
- Mode trigger:
- Distribution context assumptions:
- Project-specific license policy considered:
- Areas intentionally not inspected:

## Evidence Coverage

- Manifests/lockfiles inspected:
- License/notice files inspected:
- Vendored/native/bundled assets inspected:
- Build/link/bundle config inspected:
- Remediation evidence inspected:
- Confidence impact:

## Checks Run / Not Run

- ...

## Dependency Triage

| Dependency | Class | Evidence | Concern | Recommendation | Confidence |
|---|---|---|---|---|---|

## License / Distribution Triage

| Component | Distribution context | License signal | Evidence | Status | Confidence |
|---|---|---|---|---|---|

## Remediation Evidence

- ...

## Blockers and Needs-Confirmation Items

### [P0/P1/P2/P3] Title

Evidence:
- ...

Impact:
- ...

Recommended next action:
- ...

Revisit conditions:
- (P0/P1 only) ...

Confidence:
- High | Medium | Low

## Recommended Next Actions

1. [P0/P1/P2/P3] ...

## Known Limitations

- This is engineering triage, not legal advice.
```

## Framework Best-Practice Review Mode

```md
---
task: <task-slug>
phase_or_step: report
created_at: <ISO-8601 timestamp>
mode: framework-best-practice-review
---

# Code Evaluation Framework Best-Practice Review

## Executive Summary

- Framework/library:
- Detected version:
- Reviewer confidence for idiom claims: high | medium | low
- Overall risk:
- Top risks:

## Scope and Assumptions

- Target:
- Mode trigger:
- Primary references consulted:
- Project-specific rules considered:
- Areas intentionally not inspected:

## Evidence Coverage

- Framework entrypoints inspected:
- Core usage patterns inspected:
- Tests/checks inspected:
- Dependency surfaces inspected:
- Commands run:
- Confidence impact:

## Checks Run / Not Run

- ...

## Findings

### [P0/P1/P2/P3] Title

Evidence:
- `path/file.ext:line`

Impact:
- ...

Recommended next action:
- ...

Revisit conditions:
- (P0/P1 only) ...

Confidence:
- High | Medium | Low

## Dependency Necessity

| Dependency | Role | Evidence | Concern | Recommendation | Confidence |
|---|---|---|---|---|---|

## Positive Signals

- ...

## Recommended Next Actions

1. [P0/P1/P2/P3] ...

## Known Limitations

- ...
```
