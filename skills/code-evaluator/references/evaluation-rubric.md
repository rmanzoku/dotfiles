---
name: evaluation-rubric
description: General codebase evaluation rubric for the code-evaluator skill.
version: "2.1"
updated: 2026-07-18
---

# Evaluation Rubric

Use this rubric to evaluate code quality while keeping the final report evidence-backed and concise.

## Applying the Rubric

- Criteria are separated on purpose: judge each criterion independently and do not average a failed criterion away inside an otherwise good pillar.
- Not every criterion applies to every target. Record non-applicable criteria as `N/A` with a one-line reason instead of scoring them.
- Every finding must cite trace evidence the reader can open: path, line where practical, and the observed fact. No finding without evidence.
- Judge severity by damage depth and reversibility, not by probability alone or by prose volume. A one-way-door risk (money, contracts, data loss, security, PII, legal exposure, public API breakage) outranks a statistically likelier but reversible annoyance. Report length must not scale with repository size.
- In the final report, prefer fewer evidenced findings over many speculative ones; findings the maintainer dismisses as nitpicks erode trust in the whole report. This filter applies when composing the report, not during the finding pass: raw-findings coverage stays complete (see the change-review coverage rule in `SKILL.md`).
- Present structural concerns as conditional smell hypotheses: "acceptable while condition A holds; hurts when condition B becomes true." Confirmed defects outrank hypotheses; style preferences rank last.
- For every P0/P1 issue, include revisit conditions: the concrete observation that would flip or retire the judgment.
- A single evaluator pass is one perspective, not exhaustive coverage. When confidence matters, state which classes of issues this pass is unlikely to catch.
- When materially changing this rubric's pillars or criteria, sanity-check the new version against at least one recent past report before adopting it.

## Pillars

1. **Architecture and boundaries**
   - Separation of concerns, dependency direction, layering, module ownership, circular dependencies, and hidden globals.
   - Pattern fit: avoid both under-structured coupling and unnecessary architecture.
   - Directory and package grain should match ownership and exported responsibility well enough for navigation, without requiring one universal structure.

2. **Implementation quality and maintainability**
   - Readability, simple control flow, robust error handling, observability, validation, security hygiene, performance hygiene, operational readiness signals, and testability.
   - Prefer idiomatic use of language/framework features over custom abstractions without clear benefit.
   - Treat guard clauses, input validation, and error handling as healthy branches; `if` statements are not inherently bad. Treat repeated conditions, `type`/`kind`/`mode`/`status` branching, unclear one-vs-many special cases, and unnamed domain concepts buried in conditions as signals of specification complexity or unextracted concepts.
   - Treat bare default values, magic numbers, Boolean parameters, sentinel values, stringly typed modes, unitless values, implicit fallbacks, and env/config reads from deep layers as observation points for anonymous specification decisions. For domain-significant branches or values, prefer named constants, types, enums, policies, explicit inputs, and boundary validation; comments explain background and tradeoffs, not missing intent.
   - Flag fallback paths that hide the primary path's failure cause, silently switch execution routes, or weaken idempotency. If the alternate path is more reliable, the finding is "promote it to primary," not "keep it as fallback." Explicitly modeled redundant providers (equivalent endpoints, mirrors, replicas) with clear selection rules are not fallback smells.
   - Public component, directory, function, and module names should describe responsibility or ownership, not authoring method, AI involvement, or generator provenance.
   - Semantic UI object names should own the object contract they imply, such as relevant state, variants, accessibility, interaction, layout/composition, and data/source responsibility; leaf text, formatter, wrapper, or selector helpers should use names and placement that reflect their narrower role. If a component named as a UI object only shares a leaf helper while callers duplicate the object grammar, report the abstraction as insufficient rather than successful reuse.

3. **Tests and verification**
   - Critical behavior coverage, edge cases, deterministic tests, test isolation, useful fixtures, checks that can run in CI, and local/CI parity.
   - Tests are evidence of spec conformance only when independent of the implementation they gate: tests derived solely from current code fix current behavior, not intent. Treat weakened or deleted assertions, and spec/test edits that ride along with the implementation change they gate, as first-class findings.
   - Report checks not run and how that affects confidence.
   - Local audit/lint checks should enforce current low-false-positive invariants and avoid broad regex guesses for semantic ownership.
   - Stable test selectors and automation contracts may intentionally keep historical wording; evaluate them separately from internal implementation responsibility names.

4. **Documentation and project knowledge**
   - README, architecture docs, ADRs, API contracts, comments that explain intent, and alignment between docs and code.
   - Separate project-specific compliance from general best practice.
   - When AI-assisted work is part of the workflow, missing or ambiguous entry-gate and artifact contracts are maintainability risks, not only documentation gaps.

5. **Dependency necessity and ecosystem fit**
   - Whether dependencies are necessary, official, maintained, license-compatible for the use context, and used idiomatically.
   - Prefer standard APIs or small internal code for commodity behavior when safe.

6. **Security and reliability**
   - Secrets handling, input trust boundaries, auth, data validation, logging of sensitive values, graceful degradation, idempotency, supply-chain exposure, deployment reproducibility, runtime configuration, observability, and runbook/on-call posture when visible.
   - Do not declare the system secure. Report visible hygiene failures and label findings `static-review-only` when no scanner, dynamic test, or targeted security tool was run.

7. **AI/LLM ergonomics**
   - Clear structure, chunkable files, explicit interfaces/types, predictable naming, low boilerplate, focused modules, and tests/docs that let future agents reason with limited context.
   - Context economy: an agent can load the smallest relevant slice of the codebase for a task — focused modules with clear entrypoints beat sprawling files that force whole-file reads.
   - Feedback loops exist and are agent-usable: validators, tests, and checks that an agent can run, with verbose, self-repair-friendly error messages ("field X not found; available: ...") rather than bare failures.
   - No voodoo constants: configuration values carry their justification; if the right value is unknowable from the code, an agent cannot maintain it either.
   - When the repository contains agent scaffolding (prompts, skills, harness scripts), evaluate whether its instruction specificity matches task fragility: fixed scripts for fragile operations, principles for judgment work; and whether prompts hold a useful altitude instead of hardcoding brittle case logic.
   - Existing code is conditioning input for future AI changes: duplicated implementations, old paths left beside their replacements, and workarounds without an adjacent comment stating reason, scope, and removal condition will be read as precedent and amplified. Weigh such findings by how likely the pattern is to be imitated, not only by local impact.
   - Treat this as supplementary to human readability, domain idiom, and maintainability; do not reward AI convenience at their expense.
   - Future agents should be able to identify source taxonomy, ownership layer, canonical docs, and verification gates before editing.

8. **Future-context fit**
   - Backward compatibility, commonization, staged migration, feature flags, abstraction layers, and fallback paths are not inherently good; each must name the constraint it protects. Where change is cheap and reversible, rebuilding at time of need may beat embedding future support now.
   - Do not present human-era development conventions (effort-based phasing, ceremony-heavy process) as optimal by default when change velocity is high and the change is reversible.
   - When a change replaces a path, removing the superseded path is part of its definition of done; old and new left side by side both remain candidates for the next change. A healthy current state lets a fresh agent resume routine work from current specs, code, and tests alone — routine work that requires chat history or git archaeology signals a deficiency in the current canonical state.
   - This relaxation never applies to high-damage-depth domains: billing, authentication/authorization, audit, migrations, data models, external API contracts, legal/regulatory requirements, security, PII, money movement, and irreversible production data operations are judged by damage depth with explicit specifications, boundary validation, auditability, rollback, and human approval.

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

Revisit conditions:
- (P0/P1 only) The concrete observation that would flip or retire this judgment.

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

## What I Would Not Preserve

Call out existing structures that should not constrain future improvement:

- Thin wrappers around commodity dependencies.
- Cross-layer imports or abstractions that encode accidental history.
- Duplicate libraries for one purpose.
- Design choices that match current code but conflict with ideal architecture.
- Public names that encode authoring method or generator status instead of responsibility.
- Regex gates that appear to enforce semantic ownership but cannot do so with low false positives.

This section is design opinion, not a deletion or refactor mandate. Do not apply it to product behavior, public APIs, data migrations, security boundaries, or legal obligations without explicit caution.
