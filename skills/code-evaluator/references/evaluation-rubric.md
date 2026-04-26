---
name: evaluation-rubric
description: General codebase evaluation rubric for the code-evaluator skill.
---

# Evaluation Rubric

Use this rubric to evaluate code quality while keeping the final report evidence-backed and concise.

## Pillars

1. **Architecture and boundaries**
   - Separation of concerns, dependency direction, layering, module ownership, circular dependencies, and hidden globals.
   - Pattern fit: avoid both under-structured coupling and unnecessary architecture.

2. **Implementation quality and maintainability**
   - Readability, simple control flow, robust error handling, observability, validation, security hygiene, performance hygiene, operational readiness signals, and testability.
   - Prefer idiomatic use of language/framework features over custom abstractions without clear benefit.

3. **Tests and verification**
   - Critical behavior coverage, edge cases, deterministic tests, test isolation, useful fixtures, checks that can run in CI, and local/CI parity.
   - Report checks not run and how that affects confidence.

4. **Documentation and project knowledge**
   - README, architecture docs, ADRs, API contracts, comments that explain intent, and alignment between docs and code.
   - Separate project-specific compliance from general best practice.

5. **Dependency necessity and ecosystem fit**
   - Whether dependencies are necessary, official, maintained, license-compatible for the use context, and used idiomatically.
   - Prefer standard APIs or small internal code for commodity behavior when safe.

6. **Security and reliability**
   - Secrets handling, input trust boundaries, auth, data validation, logging of sensitive values, graceful degradation, idempotency, supply-chain exposure, deployment reproducibility, runtime configuration, observability, and runbook/on-call posture when visible.
   - Do not declare the system secure. Report visible hygiene failures and label findings `static-review-only` when no scanner, dynamic test, or targeted security tool was run.

7. **AI/LLM ergonomics**
   - Clear structure, chunkable files, explicit interfaces/types, predictable naming, low boilerplate, focused modules, and tests/docs that let future agents reason with limited context.
   - Treat this as supplementary to human readability, domain idiom, and maintainability; do not reward AI convenience at their expense.

## Dependency Triage

Classify important dependencies:

| Class | Meaning | Default treatment |
|---|---|---|
| `platform/core` | React, React Native, Expo, language/runtime/framework core | Usually acceptable; check idiomatic use and version health |
| `official/spec-driven` | Official SDK/client or implementation needed for protocol/spec compliance | Usually acceptable; verify it is official and configured correctly |
| `specialized/hard-to-rebuild` | Crypto, auth, database driver, native bridge, media codec, payment, timezone/runtime complexity | Prefer proven dependencies; scrutinize security and maintenance |
| `community/non-official` | Non-official package from ecosystem | Not automatically bad; issue only when need, maintenance, license, security, distribution, or replaceability risk overlaps |
| `commodity/replaceable` | HTTP wrappers, tiny utilities, formatting helpers, shallow retry/glue code | Yellow sign; consider standard APIs or small internal implementation |
| `duplicative` | Multiple libraries for the same role | Consolidation candidate |
| `license-sensitive` | License or distribution context matters | Apply `license-triage.md` |
| `unknown/unlicensed` | Missing/unclear license or provenance | Blocker or needs-confirmation |

Do not over-rotate into "AI can write it, so always build it." Keep external dependencies for security-critical, spec-heavy, official, or hard-to-rebuild domains.

Treat "zero direct imports found" as a review signal, not removal proof. Peer dependencies, native autolinking, build-time plugins, app config, generated code, and runtime reflection can justify a dependency that a shallow source search does not find.

## Scoring

Use `0-10` scores for the overall assessment and each pillar.

- Mark scores `provisional` when sampling is narrow or checks were not run.
- Attach `confidence: high | medium | low`.
- Cap confidence by evidence coverage: use `low` for narrow sampling or missing core areas, `medium` when representative areas were inspected but important checks or surfaces were skipped, and `high` only when sampling, docs/manifests, high-risk paths, and relevant checks support the claim.
- If evidence cannot support an overall score, report scoped findings instead of forcing a whole-repo score.
- Let prioritized issues and next actions drive decisions; scores are a summary, not the main deliverable.

## Issue Format

Each issue must contain:

```md
### [P1] Short title

Evidence:
- `path/file.ext`: observed fact or short excerpt

Impact:
- Why this matters for correctness, maintainability, security, license, distribution, or AI ergonomics.

Recommended next action:
- Ideal-state direction or investigation target.

Confidence:
- High | Medium | Low
```

Use file/line references when available. Do not invent precision; use path-only evidence when line numbers are not practical.

## Positive Signals

Include a short section for what should likely be preserved:

- Clear boundaries worth keeping.
- Tests or docs that are effective.
- Official/spec-driven dependencies used appropriately.
- Evidence of dependency/license remediation.
- Simple internal code replacing unnecessary commodity dependencies.

## What Not To Preserve

Call out existing structures that should not constrain future improvement:

- Thin wrappers around commodity dependencies.
- Cross-layer imports or abstractions that encode accidental history.
- Duplicate libraries for one purpose.
- Design choices that match current code but conflict with ideal architecture.

This section is design opinion, not a deletion or refactor mandate. Do not apply it to product behavior, public APIs, data migrations, security boundaries, or legal obligations without explicit caution.
