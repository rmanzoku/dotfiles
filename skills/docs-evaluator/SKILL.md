---
name: docs-evaluator
description: Evaluate a repository's documentation system when asked for a broad docs audit, AI-readability review, source-of-truth review, link/reachability audit, entrypoint conflict review, stale/deprecated document review, freshness governance review, TODO/deferred work governance review, ADR/history-vs-canonical separation review, instruction-strength drift review, agent-specific guidance separation review, skill contract precedence review, metadata/front matter hygiene review, reference integrity review, or contradiction/gap analysis across README, AGENTS, CLAUDE.md, docs, specs, skills, workbench notes, and other text documentation. Produces an artifact-backed Markdown report and does not edit the target docs.
---

# Docs Evaluator

Produce an evidence-backed evaluation report for a repository's documentation system. Do not create patches, delete docs, rewrite canonical sources, or make commits. Recommendations should describe the ideal target state and identify gaps clearly enough for a later implementation pass.

Use `docs-entrypoint-check` instead when the user only wants a lightweight check for README/docs index/agent entrypoints or bootstrap skeleton suggestions.

## Core Rules

- Treat this skill as report-only. Provide findings, risks, scores, inventories, and recommended directions; do not implement them.
- Prefer CLI inspection (`rg`, `find`, `git`, link extraction commands) over MCP unless the user explicitly asks for MCP.
- Do not mutate the evaluated source tree. Evaluation artifacts may be written under `.context/docs-evaluator/<task>/`.
- Exclude generated/vendor/cache outputs by default: `.git/`, `.context/`, `node_modules/`, `dist/`, `build/`, `.next/`, `coverage/`, generated API docs, vendored docs, package caches, and binary artifacts.
- Include repository documentation text broadly: `README*`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `QWEN.md`, `SKILL.md`, `docs/`, `specs/`, `skills/`, workbench/planning docs, and text-like files such as `.md`, `.mdx`, `.txt`, `.rst`, `.adoc`, `.html`, `.htm`, `.yaml`, `.yml`, `.json`, and `.toml` when they function as documentation or policy.
- If the user asks for every text file, include all non-generated text files in the inventory, then mark code/config files that are not documentation as out of scoring scope.
- Separate current canonical instructions from historical records. ADRs, dated workbench notes, `.context/`, and migration notes are evidence/history unless an active entrypoint explicitly promotes them to canonical policy.
- Use confidence labels. Do not make whole-repo claims from narrow sampling without marking them provisional.
- For large repositories, create and save a sampling plan before deep dives.

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

## Workflow

1. **Set task and artifact directory**
   - Create `.context/docs-evaluator/<task>/`.
   - Record target, mode, requested scope, exclusions, assumptions, and whether the user requested all text files or documentation-like files.

2. **Inventory documentation text**
   - Enumerate candidate text documents with `find` or `rg --files`, applying default exclusions.
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
   - Check reachability, entrypoint conflicts, AI readability, necessity/sufficiency, contradictions, instruction-strength drift, stale/deprecated docs or skills, freshness governance, TODO/deferred work governance, duplicated policy, agent-specific guidance separation, skill contract precedence, metadata/front matter hygiene, external reference clarity, documented dependency clarity, spec/contract traceability, canonical-vs-temporary separation, unreflected gaps, terminology consistency, and qualitative reading burden.
   - Save raw evidence to `.context/docs-evaluator/<task>/raw-findings.md`.

6. **Run non-mutating checks when reasonable**
   - Run link checks, markdown lint/readability checks, or custom inventory scripts only when they are available and non-mutating.
   - Do not run formatters, autofixers, generators, installers, or commands that rewrite docs unless the user explicitly asks.
   - Save commands, exit status, and skipped checks to `.context/docs-evaluator/<task>/checks.md`.

7. **Write final report**
   - Read `references/report-template.md`.
   - Save the full report to `.context/docs-evaluator/<task>/report.md`.
   - Return a concise chat summary with the report path, top risks, score/confidence, and checks run/not run.

## Required Report Properties

- Include `Executive Summary`, `Overall Score`, `Pillar Scores`, `Evidence Coverage`, `Inventory Summary`, `Entrypoint Conflicts`, `Reachability`, `Source-of-Truth Boundaries`, `Instruction Strength Drift`, `Agent-Specific Guidance`, `Skill Contract Precedence`, `Metadata / Front Matter Hygiene`, `Reference Integrity`, `AI Readability`, `Positive Signals`, `Contradictions & Drift`, `TODO / Deferred Work`, `Deprecated or Stale Docs`, `Temporary-to-Canonical Gaps`, `Checks Run`, `Checks Not Run`, `Issues & Risks`, and `Recommended Next Actions`.
- For `documentation-system-evaluation`, start with summary and scores.
- For narrower modes, start with findings ordered by severity, then include mode-specific coverage and residual gaps.
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

## References

- Read `references/evaluation-rubric.md` before evaluating findings.
- Read `references/report-template.md` before writing the final report.

## Validation

```bash
scripts/skill-quick-validate skills/docs-evaluator
```
