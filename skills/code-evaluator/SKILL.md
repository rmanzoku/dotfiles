---
name: code-evaluator
description: Evaluate a repository, package, subsystem, or substantial source tree when explicitly asked for a broad codebase assessment. Produces an artifact-backed Markdown report covering architecture, maintainability, tests, documentation, dependency necessity, license/distribution risk, security, framework idioms, and AI/LLM ergonomics. Use for whole-codebase or subsystem evaluations, architecture assessments, dependency/license audits, broad quality baselines, and broader-than-PR reviews; do not take over ordinary narrow PR/diff review unless the user asks for this evaluator or a broad assessment.
---

# Code Evaluator

Produce an evidence-backed evaluation report. Do not create patches, edit target source files, upgrade dependencies, run autofix commands, or make commits. Improvement guidance should describe the ideal target state, not the smallest human-sized diff.

## Core Rules

- Treat this skill as report-only. Provide findings, risks, scores, and recommended directions; do not implement them.
- Prefer CLI inspection (`rg`, `find`, package manager metadata, test commands) over MCP unless the user explicitly asks for MCP.
- Do not mutate the evaluated source tree. Evaluation artifacts may be written under `.context/code-evaluator/<task>/`.
- Exclude generated/vendor/cache outputs from source-quality review by default: `node_modules/`, `dist/`, `build/`, `.next/`, `coverage/`, generated code, binary artifacts, and previous `.context/` runs.
- In `license-audit` mode, do not ignore vendored/native third-party assets that can enter distributed artifacts. Inventory `vendor/`, `third_party/`, linked native libraries, bundled sample assets, and build-config references without deeply reviewing their source unless needed.
- Still read manifests, lockfiles, license files, notice files, and remediation evidence: `package.json`, lockfiles, `go.mod`, `Cargo.lock`, `LICENSE`, `NOTICE`, `patches/`, `overrides`, `resolutions`, forks, and vendored patch notes.
- Separate general engineering findings from project-specific compliance. If repo docs define local rules, evaluate against them, but do not confuse "matches current policy" with "ideal design".
- Use confidence labels. Do not make whole-repo claims from narrow sampling without marking them provisional.
- When the target is large, create and save a sampling plan before deep dives.

## Mode Selection

Select the narrowest mode that matches the request:

- `whole-codebase-evaluation`: Health check for a repository, package, or subsystem. Use summary-first output with pillar scores, sampling plan, coverage, positive signals, prioritized issues, and ideal-state recommendations.
- `change-review`: Review a diff/PR/patch in a broader evaluator style. Use findings-first output with severity, file/line references, missing tests, and summary last.
- `license-audit`: Focus on dependency licenses, distribution context, prior accepted signals, unknown/no-license blockers, and remediation evidence.
- `framework-best-practice-review`: Focus on idiomatic use of a named framework or library while still checking tests, boundaries, and dependency necessity.

If the user gives no mode, infer it from the target and wording. If a normal PR review is requested without a broad assessment, prefer the environment's normal review workflow instead of this skill.

## Workflow

1. **Set task and artifact directory**
   - Create `.context/code-evaluator/<task>/`.
   - Record the target, mode, assumptions, and requested scope.

2. **Acquire efficient context**
   - Read high-level docs first when present: `AGENTS.md`, `README*`, `docs/`, architecture/rules docs, package readmes.
   - Inventory the source tree while excluding generated/vendor/cache paths for source-quality review.
   - Read manifests, lockfiles, dependency overrides, license/notice files, test/lint/typecheck config, and core source directories.
   - For license audits, also inspect scope-adjacent native/link/bundle config when it can place third-party code or assets into distributed outputs.
   - Save inventory notes to `.context/code-evaluator/<task>/inventory.md`.

3. **Plan sampling for large targets**
   - For large repos/subsystems, choose representative samples across core logic, boundaries, high-risk areas, tests, dependency surfaces, and docs.
   - Save `.context/code-evaluator/<task>/sampling-plan.md`.
   - Report files inspected and important areas not inspected.

4. **Load references as needed**
   - Read `references/evaluation-rubric.md` for general evaluation pillars, scoring, dependency triage, and issue format.
   - Read `references/license-triage.md` for license/distribution/dependency-risk work or whenever dependency manifests are in scope.
   - Read `references/report-template.md` before writing the final report.

5. **Evaluate and record evidence**
   - Save raw notes/findings under `.context/code-evaluator/<task>/raw-findings.md`.
   - Each issue must include evidence, impact, recommended next action, and confidence.
   - Include `What I Would Not Preserve` when existing abstractions or dependencies should not constrain a best-state redesign.

6. **Run non-mutating checks when reasonable**
   - Run tests/lint/typecheck/build only when they are expected to be non-destructive and useful for the requested scope.
   - Do not run install, upgrade, formatter-write, autofix, codegen-write, migration, or dependency-changing commands unless the user explicitly asks.
   - Save commands, exit status, and skipped checks to `.context/code-evaluator/<task>/checks.md`.

7. **Write final report**
   - Save the full report to `.context/code-evaluator/<task>/report.md`.
   - Return a concise chat summary with the report path, top risks, score/confidence, and checks run/not run.

## Required Report Properties

- Include `Executive Summary`, `Overall Score`, `Pillar Scores`, `Evidence Coverage`, `Checks Run`, `Checks Not Run`, `Positive Signals`, `Issues & Risks`, `Dependency Triage`, `License / Distribution Triage` when applicable, `What I Would Not Preserve`, and `Recommended Next Actions`.
- For `whole-codebase-evaluation`, start with summary and scores.
- For `change-review`, start with findings ordered by severity and include file/line references when available.
- Use priority by risk/design importance, not human work phasing: `P0` blocker, `P1` high design/security/license risk, `P2` meaningful maintainability or dependency risk, `P3` optional cleanup.
- Treat recommendations as ideal-state directions. Do not split recommendations into short/medium/long solely because humans would need phased work.
- Add migration cautions only for destructive data changes, public API compatibility, product behavior changes, security boundaries, or license/legal review.

## Boundaries

- This skill provides engineering triage, not legal advice.
- Do not declare a license safe only because a name looks familiar. Consider distribution context, notice/source obligations, prior accepted signals, and remediation evidence.
- Do not declare GPL/LGPL/MPL automatically forbidden. Evaluate use context and whether the license obligations can be met.
- Treat no-license, unclear-license, non-commercial-only, commercial-use-prohibited, and field-of-use-restricted dependencies as blockers or strong needs-confirmation items.
