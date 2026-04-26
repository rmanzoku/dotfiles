# Docs Evaluator Report Template

Use this shape for `.context/docs-evaluator/<task>/report.md`.

```markdown
# Docs Evaluator Report

## Executive Summary

- Overall score:
- Confidence:
- Mode:
- Top risks:

## Pillar Scores

| Pillar | Score | Notes |
| --- | ---: | --- |
| Coverage |  |  |
| Reachability |  |  |
| Source-of-truth boundaries |  |  |
| AI readability |  |  |
| Consistency |  |  |
| Task and gap governance |  |  |
| Metadata hygiene |  |  |
| Reference integrity |  |  |

## Evidence Coverage

- Target:
- Inventory scope:
- Files inventoried:
- Files deeply inspected:
- Exclusions:
- Sampling limits:

## Inventory Summary

| Class | Count | Notes |
| --- | ---: | --- |
| entrypoint |  |  |
| canonical |  |  |
| spec |  |  |
| skill |  |  |
| historical |  |  |
| temporary |  |  |
| task-tracking |  |  |
| deprecated |  |  |
| out-of-scope |  |  |

## Reachability

- Canonical entrypoints:
- Competing first-read claims:
- Reachable active docs:
- Orphaned active docs:
- Historical-only paths:
- Navigation overreach:
- Broken anchors or path references:

## Entrypoint Conflicts

| Entrypoint | Claim | Conflicting Source | Risk | Recommendation |
| --- | --- | --- | --- | --- |

## Source-of-Truth Boundaries

- Canonical sources:
- Historical sources:
- Temporary sources:
- Boundary violations:
- Canonical claim conflicts:

## Instruction Strength Drift

| Topic | Stronger Wording | Weaker Wording | Risk | Recommendation |
| --- | --- | --- | --- | --- |

## Agent-Specific Guidance

| Topic | Shared Source | Agent-Specific Source | Separation Risk | Recommendation |
| --- | --- | --- | --- | --- |

## Skill Contract Precedence

| Skill | Contract Signal | Precedence Gap | Recommendation |
| --- | --- | --- | --- |

## Metadata / Front Matter Hygiene

| Path | Metadata Type | Issue | Recommendation |
| --- | --- | --- | --- |

## Reference Integrity

| Reference | Source Doc | Traceability Issue | Recommendation |
| --- | --- | --- | --- |

## AI Readability

- Necessary docs:
- Excessive or distracting docs:
- Missing reading order:
- Chunking and structure issues:
- Qualitative reading burden:
- Terminology consistency:

## Positive Signals

- 

## Contradictions & Drift

| Priority | Evidence | Impact | Recommendation | Confidence |
| --- | --- | --- | --- | --- |

## TODO / Deferred Work

| Location | Status Signal | Risk | Recommendation |
| --- | --- | --- | --- |

## Deprecated or Stale Docs

| Path | Evidence | Risk | Recommendation |
| --- | --- | --- | --- |

## Freshness Governance

| Path | Freshness Signal | Risk | Recommendation |
| --- | --- | --- | --- |

## Temporary-to-Canonical Gaps

| Temporary Source | Canonical Destination | Gap | Recommendation |
| --- | --- | --- | --- |

## Checks Run

| Command | Exit | Notes |
| --- | ---: | --- |

## Checks Not Run

| Check | Reason |
| --- | --- |

## Issues & Risks

### P1: Title

- Category:
- Evidence:
- Impact:
- Recommended next action:
- Confidence:

## Recommended Next Actions

1. 
2. 
3. 
```
