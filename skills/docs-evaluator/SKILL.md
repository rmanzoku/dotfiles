---
name: docs-evaluator
description: Evaluate a repository's documentation system when asked for a broad docs audit, AI-readability review, source-of-truth review, link/reachability audit, entrypoint conflict review, stale/deprecated document review, freshness governance review, knowledge-base schema review, agent-readable knowledge system review, provenance/confidence/freshness review, typed relationship hygiene review, TODO/deferred work governance review, ADR/history-vs-canonical separation review, instruction-strength drift review, agent-specific guidance separation review, skill contract precedence review, metadata/front matter hygiene review, reference integrity review, or contradiction/gap analysis across README, AGENTS, CLAUDE.md, docs, specs, skills, workbench notes, and other text documentation. Produces an artifact-backed Markdown report and does not edit the target docs.
---

# Docs Evaluator

Produce an evidence-backed evaluation report for a repository's documentation system. Do not create patches, delete docs, rewrite canonical sources, or make commits. Recommendations should describe the ideal target state and identify gaps clearly enough for a later implementation pass.

Use `docs-entrypoint-check` instead when the user only wants a lightweight check for README/docs index/agent entrypoints or bootstrap skeleton suggestions.

## Core Rules

- Treat this skill as report-only. Provide findings, risks, scores, inventories, and recommended directions; do not implement them.
- Prefer CLI inspection (`rg`, `find`, `git`, link extraction commands) over MCP unless the user explicitly asks for MCP.
- Do not mutate the evaluated source tree except for evaluation artifacts written under `.context/docs-evaluator/<task>/`. Treat this artifact directory as the only planned target-local mutation allowed by this skill; ignored cache/output writes from checks must be recorded as observed side effects, not silently assumed harmless.
- Exclude generated/vendor/cache outputs by default: `.git/`, `.context/`, `node_modules/`, `dist/`, `build/`, `.next/`, `coverage/`, generated API docs, vendored docs, package caches, and binary artifacts.
- Exclude gitignored, private, secret, and machine-local files from normal documentation review by default. Do not inspect or quote ignored secret/private content unless the user explicitly asks or a documentation-governance question requires path-level confirmation; even then report only paths, labels, key names, record counts, redacted excerpts, validation status, and risk categories.
- Include repository documentation text broadly: `README*`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `QWEN.md`, `SKILL.md`, `docs/`, `specs/`, `skills/`, workbench/planning docs, and text-like files such as `.md`, `.mdx`, `.txt`, `.rst`, `.adoc`, `.html`, `.htm`, `.yaml`, `.yml`, `.json`, and `.toml` when they function as documentation or policy.
- If the user asks for every text file, include all non-generated, non-ignored text files in the inventory, then mark code/config files that are not documentation as out of scoring scope. Include ignored files only when explicitly requested, and keep private/secret output redacted.
- Separate current canonical instructions from historical records. ADRs, dated workbench notes, `.context/`, and migration notes are evidence/history unless an active entrypoint explicitly promotes them to canonical policy. Keep `.context/` excluded from normal inventory, but sample it when the user asks about temporary-to-canonical gaps, task-memory governance, or an active entrypoint explicitly references it. `.context/` sampling defaults to path-level inventory for relevant task directories plus limited deep reads of the latest or directly related artifacts; broad `.context/` traversal requires an explicit user request.
- Use confidence labels. Do not make whole-repo claims from narrow sampling without marking them provisional.
- For large repositories or any review that will not deep-read all relevant docs, create and save a sampling plan before deep dives. Do not use fixed numeric thresholds as the definition of "large"; explain the scope factors, prioritize entrypoints, canonical docs, and mode-relevant docs, sample remaining classes intentionally, and report unread ranges in `Evidence Coverage` and confidence impact.

## Mode Selection

Select the narrowest mode that matches the request:

- `documentation-system-evaluation`: Health check for a repository's documentation graph. Use summary-first output with pillar scores, inventory coverage, reachability, source-of-truth boundaries, prioritized issues, and ideal-state recommendations.
- `source-of-truth-review`: Focus on canonical vs historical/temporary boundaries, ADR misuse, unreflected decisions, and whether README/docs index/agent guidance identifies current policy correctly.
- `reachability-audit`: Focus on whether all active docs can be reached from README, AGENTS/CLAUDE.md, docs index, skill indexes, or other canonical entrypoints without search.
- `entrypoint-conflict-review`: Focus on competing "read first" claims, multiple active entrypoints, navigation branching, and whether the first-hop path is unambiguous for AI agents.
- `stale-docs-review`: Focus on deprecated docs, obsolete skills, duplicated guidance, contradictory docs, and docs that still look active after replacement.
- `todo-governance-review`: Focus on TODO, Deferred Work, known gaps, follow-up notes, owners, expiry, and whether task memory is stored in the right canonical place.
- `guidance-consistency-review`: Focus on canonical claim conflicts, instruction-strength drift, terminology consistency, and separation between shared guidance and agent-specific guidance.
- `metadata-hygiene-review`: Focus on Markdown front matter, ADR metadata, skill metadata, metadata accidentally embedded in body text, and schema consistency for documentation artifacts.
- `reference-integrity-review`: Focus on external references, documented dependencies, spec/contract traceability, and freshness signals without validating source implementation correctness.

If the user gives no mode, infer it from the target and wording. If the request is only a lightweight entrypoint/bootstrap check, prefer `docs-entrypoint-check`.

Mode decision order:

1. Use an explicitly requested mode when present.
2. If the request is only a lightweight README/docs index/agent-entrypoint check or bootstrap skeleton request, use `docs-entrypoint-check` instead of this skill.
3. If the user asks for a broad docs audit, contradiction/gap analysis across multiple doc types, or multiple narrow concerns at once, use `documentation-system-evaluation`.
4. If multiple narrow modes are primary concerns and no explicit mode is provided, use `documentation-system-evaluation`. Keep a narrow mode only when the request has a clear primary target, and record secondary concerns in `Residual Gaps`.
5. Otherwise choose the narrow mode matching the primary risk: navigation/linking -> `reachability-audit`; competing first-read claims -> `entrypoint-conflict-review`; current truth vs history -> `source-of-truth-review`; stale/deprecated active docs -> `stale-docs-review`; TODO/follow-up governance -> `todo-governance-review`; instruction drift or agent-specific separation -> `guidance-consistency-review`; front matter/schema issues -> `metadata-hygiene-review`; external reference/spec traceability -> `reference-integrity-review`.

## Workflow

1. **Set task and artifact directory**
   - Create `.context/docs-evaluator/<task>/`. Use `<YYYYMMDD>-<target-slug>` when no task name is given; if the directory already exists, append `-2`, `-3`, and so on instead of overwriting prior artifacts.
   - Record target, mode, requested scope, exclusions, assumptions, and whether the user requested all text files or documentation-like files.

2. **Inventory documentation text**
   - Enumerate candidate text documents with `rg --files` or `find`, applying default exclusions and honoring `.gitignore` by default. Use `rg --files -uuu` or equivalent only when the user explicitly asks to include ignored files or a path-level governance question requires it, and keep private/secret output redacted.
   - Classify each relevant file as `entrypoint`, `index`, `canonical`, `policy`, `spec`, `skill`, `historical`, `temporary`, `task-tracking`, `deprecated`, `generated`, or `out-of-scope`.
   - Save `.context/docs-evaluator/<task>/inventory.md`.

3. **Build the navigation and reachability map**
   - Read repository entrypoints first: `README*`, `AGENTS.md`, AI-specific guidance, docs index, and skill indexes when present.
   - Extract local Markdown and HTML links, plus plain-text references where links are missing but paths are named.
   - Mark documents reachable from canonical entrypoints, documents only reachable from historical/temporary notes, orphaned documents, competing first-read paths, broken anchors, and references that leave the worktree.
   - Save `.context/docs-evaluator/<task>/reachability.md`.

4. **Classify source-of-truth boundaries**
   - Identify canonical docs for active rules, specs, architecture, service ownership, operational procedures, and skills.
   - Identify temporary or historical docs: ADRs, workbench notes, migration notes, task scratchpads, and `.context/` artifacts.
   - Check whether temporary or historical content is being used as current policy, whether accepted decisions have not been reflected into canonical docs, and whether multiple docs claim canonical authority for the same topic.
   - Save `.context/docs-evaluator/<task>/source-of-truth.md`.

5. **Evaluate quality and consistency**
   - Read `references/evaluation-rubric.md`.
   - When evaluating knowledge-base directories, durable notes, agent-readable knowledge systems, or reusable context stores, read `references/knowledge-system-patterns.md`.
   - Check reachability, entrypoint conflicts, AI readability, necessity/sufficiency, contradictions, instruction-strength drift, stale/deprecated docs or skills, freshness governance, knowledge-system structure, primary-home/resolver clarity, current-truth-vs-history separation, provenance/confidence/freshness, typed entity and relationship hygiene, raw-source-vs-curated-synthesis boundaries, privacy/data-boundary clarity, TODO/deferred work governance, duplicated policy, agent-specific guidance separation, skill contract precedence, metadata/front matter hygiene, external reference clarity, documented dependency clarity, spec/contract traceability, canonical-vs-temporary separation, unreflected gaps, terminology consistency, and qualitative reading burden.
   - Save raw evidence to `.context/docs-evaluator/<task>/raw-findings.md`.

6. **Run checks with mutation guard**
   - Run link checks, markdown lint/readability checks, or custom inventory scripts only when useful for the requested scope and available without formatters, autofixers, generators, installers, or dependency changes.
   - When the evaluated repository provides `scripts/docs-link-check`, prefer it for local Markdown link and anchor checks, passing the target path for narrow reviews when appropriate. If it is absent, fall back to best-effort CLI extraction and clearly mark the lower confidence.
   - Treat a non-zero `scripts/docs-link-check` exit caused by broken local docs links or anchors as evaluation evidence, not as skill failure.
   - Do not check external URL reachability by default. For `reference-integrity-review`, evaluate whether external references document their purpose, freshness signal, and verification responsibility. Perform web verification only when the user explicitly asks, or when external freshness is the primary review risk and primary-source confirmation is needed; then record `verified_at` and verification scope.
   - If the target is inside a git worktree, record `git status --short` before and after checks in `checks.md`. Treat pre-existing dirtiness as baseline context, not your own change.
   - Do not run commands expected to write tracked docs, configs, generated docs, snapshots, or dependency installation state.
   - If a check writes ignored cache/output files, record the path category and reason in `checks.md`. If a check writes tracked or review-relevant files, stop running further checks and report the mutation; do not clean up or revert it unless the user explicitly asks.
   - Do not run formatters, autofixers, generators, installers, or commands that rewrite docs unless the user explicitly asks.
   - Save commands, exit status, and skipped checks to `.context/docs-evaluator/<task>/checks.md`.

7. **Write final report**
   - Read `references/report-template.md`.
   - Save the full report to `.context/docs-evaluator/<task>/report.md`.
   - Include `Evidence Coverage` in `report.md`. A standalone evidence-coverage artifact is optional, not required.
   - Return a concise chat summary with the report path, top risks, score/confidence, and checks run/not run.

## Required Report Properties

- For `documentation-system-evaluation`, include `Executive Summary`, `Overall Score`, `Pillar Scores`, `Evidence Coverage`, `Inventory Summary`, `Entrypoint Conflicts`, `Reachability`, `Source-of-Truth Boundaries`, `Instruction Strength Drift`, `Agent-Specific Guidance`, `Skill Contract Precedence`, `Metadata / Front Matter Hygiene`, `Reference Integrity`, `AI Readability`, `Positive Signals`, `Contradictions & Drift`, `TODO / Deferred Work`, `Deprecated or Stale Docs`, `Temporary-to-Canonical Gaps`, `Checks Run`, `Checks Not Run`, `Issues & Risks`, and `Recommended Next Actions`. Start with summary and scores.
- For narrower modes, include `Findings`, `Evidence Coverage`, mode-specific sections, `Checks Run / Not Run`, `Residual Gaps`, and `Summary`. Start with findings ordered by severity.
- Include these mode-specific sections when applicable: `Source-of-Truth Boundaries` and `Temporary-to-Canonical Gaps` for `source-of-truth-review`; `Reachability` and `Entrypoint Conflicts` for `reachability-audit` and `entrypoint-conflict-review`; `Deprecated or Stale Docs` and `Freshness Governance` for `stale-docs-review`; `TODO / Deferred Work` for `todo-governance-review`; `Instruction Strength Drift`, `Agent-Specific Guidance`, `Skill Contract Precedence`, and `Contradictions & Drift` for `guidance-consistency-review`; `Metadata / Front Matter Hygiene` for `metadata-hygiene-review`; `Reference Integrity` for `reference-integrity-review`.
- Use priority by documentation-system risk: `P0` blocker, `P1` high risk, `P2` meaningful maintainability or AI-readability risk, `P3` optional cleanup.
- Each issue must include evidence, impact, recommended next action, and confidence.
- Distinguish "missing canonical doc" from "canonical doc exists but is not linked" and from "historical note contains unreflected policy".
- Treat recommendations as ideal-state directions, not a human work breakdown.

## Boundaries

- This skill evaluates documentation systems, not source implementation quality. Use `code-evaluator` for broad codebase health, dependency, security, framework, or license evaluation.
- Do not treat ADRs, workbench files, or `.context/` artifacts as canonical merely because they contain the newest wording.
- Do not declare a document obsolete only because it is old. Look for replacement links, deprecation wording, git history, manifest changes, and whether active entrypoints still route to it.
- Do not require one universal docs structure. Evaluate whether the repo's own canonical entrypoints make the current structure explicit and efficient.
- Do not expand into prose style proofreading, SEO/readability formulas, code example execution, secrets/PII scanning, auto-fixes, pull requests, or document deletion.
- Do not verify whether code implements a documented contract; only evaluate whether docs identify the relevant specs, contracts, manifests, or implementation references clearly enough for a later code review.
- Treat instruction-strength drift, terminology consistency, metadata hygiene, and reading burden as evidence-based docs risks, not style nitpicks or exact quantitative scores.
- For metadata/front matter and other policy hygiene, apply current canonical repo rules. If it is unclear whether a rule applies retroactively to older ADRs or legacy docs, record the uncertainty as residual risk or an open question instead of declaring a violation.
- Do not treat every Markdown file without front matter as a violation by default. Missing front matter is a finding only when the repo declares required metadata for that document type, such as ADRs or `SKILL.md`. For generic README, AGENTS, or docs pages, evaluate misplaced body metadata only when metadata is actually present or explicitly required.

## References

- Read `references/evaluation-rubric.md` before evaluating findings.
- Read `references/knowledge-system-patterns.md` when evaluating knowledge-base directories, durable notes, agent-readable knowledge systems, or documentation intended to preserve reusable context.
- Read `references/report-template.md` before writing the final report.

## Validation

```bash
scripts/skill-quick-validate skills/docs-evaluator
```

Run validation from the publisher source repository root, not from the installed skill directory.
