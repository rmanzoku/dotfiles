---
name: evaluation-rubric
description: Documentation-system evaluation rubric for the docs-evaluator skill.
version: "2.1"
updated: 2026-07-18
---

# Docs Evaluator Rubric

Use this rubric to score the documentation system as a graph of active guidance, canonical sources, and historical records.

## Applying the Rubric

- Criteria are separated on purpose: judge each criterion independently and do not average a failed criterion away inside an otherwise good pillar.
- Not every criterion applies to every repository. Record non-applicable criteria as `N/A` with a one-line reason instead of scoring them.
- Every finding must cite trace evidence the reader can open: path, line or heading, and the observed wording. No finding without evidence.
- Judge severity by impact and damage depth, not by how much prose the finding needs. Long explanations do not make a finding more severe, and report length must not scale with repository size.
- Weight severity by conditioning surface: a defect in a document loaded automatically every session (AGENTS.md, CLAUDE.md, entrypoints) conditions every future agent output and outweighs the same defect in an on-demand or historical document.
- Prefer fewer evidenced findings over many speculative ones; findings the maintainer dismisses as nitpicks erode trust in the whole report.
- Present low/medium-confidence structural concerns as conditional smell hypotheses: "acceptable while condition A holds; hurts when condition B becomes true."
- For every P0/P1 issue, include revisit conditions: the concrete observation that would flip or retire the judgment.
- A single evaluator pass is one perspective, not exhaustive coverage. When confidence matters, state which classes of issues this pass is unlikely to catch.
- When materially changing this rubric's pillars or issue categories, sanity-check the new version against at least one recent past report before adopting it.

## Pillars

### Coverage

- All repository documentation text is inventoried or explicitly excluded.
- The inventory includes README, agent instructions, AI-specific guidance, docs, specs, skills, workbench/planning notes, ADRs, and text-like documentation files.
- Generated/vendor/cache docs are excluded by policy and listed only when relevant to distribution or discoverability.
- External references, documented dependencies, specs, contracts, manifests, and implementation reference paths are inventoried when docs rely on them.

### Reachability

- Canonical entrypoints link to the documents an AI must read.
- No active canonical document is reachable only by guesswork or repository search.
- Orphaned documents are either intentionally deprecated/out-of-scope or linked from the correct index.
- Competing first-read claims are detected separately from ordinary reachability gaps.
- Local anchors, relative paths, and worktree boundaries are clear enough that links do not send agents to dead headings or unrelated source trees.

### Source-of-Truth Boundaries

- Active policy/spec/architecture lives in canonical docs.
- ADRs and historical records explain why decisions happened, but are not the only current source of an active rule.
- Temporary notes, workbench docs, and `.context/` artifacts do not carry unreflected policy.
- Multiple files do not claim canonical authority for the same topic unless the precedence rule is explicit.
- Canonical claims name the current source, not just historical rationale.
- Detailed schemas for skills, gates, artifacts, or workflow contracts have one identifiable canonical owner; summaries and ADRs link to or summarize that owner instead of repeating the full schema.
- Active canonical docs and active skill instructions do not keep deprecated, temporary, fallback, retired, historical, or override vocabulary as current policy options.
- Exceptions granted in active docs carry a reason, scope, and removal condition; an unconditional exception reads as a standard option to future agents and is a finding (`policy-contamination` or `temporary-legitimacy`), not a style note.
- Negative references to retired vocabulary are classified as `allowed-negative-reference`, `migration-map`, `historical-reference`, or `search-only-audit-pattern`; unclassified cases are `QUESTION`, and current-option usage is `current-policy-contamination`.

### AI Readability

Evaluate this pillar as context economy: agent context is a finite resource, and a good documentation system lets an agent assemble the smallest set of high-signal tokens needed for the task at hand.

- Documents are necessary and sufficient for an AI agent to complete common tasks without reading excessive unrelated history, and they do not re-explain what a competent agent already knows.
- Reading order is explicit enough to avoid both missed rules and unnecessary deep dives.
- Entrypoints work as pointer sets (path plus one-line purpose) that support just-in-time retrieval: an agent can decide which file to load next without loading everything.
- Entrypoint hub files hold only invariants and pointers. Procedures that belong in skills, decision rationale that belongs in ADRs, and executable expectations that belong in tests or specs parked in a hub file are placement findings, not neutral convenience.
- The docs system maps to a three-layer shape: index/table-of-contents entrypoints, focused per-topic documents, and deep reference material loaded only on demand.
- Structure signals are checkable: entry documents stay concise, documents are reachable within the layers the entrypoints declare (index to topic to reference) rather than through undeclared nested reference chains, and long reference documents open with a table of contents or an equivalent scannable heading structure.
- Critical rules sit where agents will see them — near the beginning or end of a document — not buried mid-file.
- Guidance documents hold a useful instruction altitude: concrete enough to steer behavior, without hardcoding brittle case-by-case logic that belongs in scripts or validators.
- Documents are chunkable: scoped headings, concise sections, stable names, and structured lists where useful.
- The required reading path has a reasonable qualitative burden and does not force agents through irrelevant history.
- Gate or phase artifacts expose machine-checkable status fields when docs say work cannot proceed on `FAIL` or `QUESTION`; prose-only completion claims are a risk when downstream agents or validators need stable state.
- Docs separate low-false-positive static checks from semantic human/agent review instead of asking scripts to infer task-local intent or ownership without context.

### Consistency

- Duplicate rules do not conflict.
- Skill descriptions, AGENTS/CLAUDE guidance, README/docs index, and spec docs agree on triggers, responsibilities, and canonical paths.
- Deprecated docs or skills are removed, marked deprecated, or isolated from active navigation.
- Instruction strength is consistent: MUST/SHOULD/MAY and 必須/推奨/任意/禁止/原則禁止 do not drift across docs for the same rule.
- Shared guidance and agent-specific guidance are separated intentionally across AGENTS, CLAUDE.md, GEMINI.md, QWEN.md, Codex guidance, and skill docs.
- Skill docs explain whether they inherit repo rules, override a specific procedure, or provide a narrower contract.
- Terminology for repeated operational concepts is stable enough that agents can match equivalent rules without guessing; do not treat general prose style as a finding.
- Naming taxonomy docs distinguish responsibility/ownership names from authoring-method labels and generated-artifact labels.
- Stable external selectors, test IDs, public automation contracts, and implementation responsibility names are documented as separate concerns when renaming one would break the other.

### Reference Integrity

- External links, external tool references, package or manifest references, and local implementation paths are explicit enough to follow.
- Docs identify the relevant spec, contract, manifest, schema, script, or source path when they depend on one.
- Freshness signals such as deprecation wording, replacement links, accepted ADR status, manifest membership, or git history are considered before declaring stale risk.
- The evaluator does not verify source implementation correctness; it reports missing or unclear documentation traceability.

### Task and Gap Governance

- TODO, Deferred Work, known gaps, and follow-up tasks have an owner, status, destination, or expiry.
- Follow-up notes are not scattered across ADRs, scratchpads, comments, and docs without a canonical tracker.
- Temporary findings that should change canonical docs are tracked until reflected or explicitly rejected.
- Gate artifacts use explicit fields such as status, blocking failures, and open questions when the workflow needs deterministic continuation rules.

### Metadata Hygiene

- Markdown metadata lives in front matter where the repo requires it.
- ADRs include required status/date/worked_at/agent_model fields when the repo expects them.
- Skills include valid `name` and `description` front matter and keep UI metadata in `agents/openai.yaml`.
- Body text does not carry stale metadata blocks that should be machine-readable.
- Metadata findings are limited to repo-declared requirements and active documentation contracts.
- Legacy or older documents are only violations when current canonical policy clearly applies to them. Otherwise, report uncertainty or grandfathering risk.
- Absence of front matter is only a finding for document types with declared required metadata, such as ADRs or `SKILL.md`. Generic README, AGENTS, or docs pages do not need front matter unless the repo explicitly requires it.

## Scoring

- `90-100`: Strong documentation graph. Entry points, canonical sources, and history are clearly separated with only minor cleanup.
- `75-89`: Good structure with a few reachable-or-canonicality gaps.
- `60-74`: Usable but risky. AI agents can complete tasks, but must search or infer too often.
- `40-59`: Fragile. Important docs are missing, orphaned, stale, contradictory, or only present in historical notes.
- `0-39`: Unreliable. No trustworthy path exists from entrypoints to current policy/specs.

## Issue Categories

- `inventory-gap`: relevant text documents were not inventoried or are hard to classify.
- `reachability-gap`: a necessary document is not linked from canonical entrypoints.
- `entrypoint-conflict`: multiple active documents compete as the first-read or routing authority.
- `overreach`: navigation forces agents through unnecessary or low-value docs.
- `source-of-truth-gap`: active guidance exists only in ADR/history/temporary notes.
- `canonical-claim-conflict`: multiple docs claim canonical authority for the same topic without precedence.
- `schema-drift`: detailed schemas are copied across skills, rules, ADRs, or other docs without a single canonical owner.
- `artifact-contract`: workflow, phase, or gate artifacts lack explicit fields needed for deterministic continuation or validation.
- `machine-check-boundary`: docs blur what scripts can safely check with regex/static rules and what requires semantic review.
- `temporary-gap`: temporary content has not been reflected, tracked, or expired.
- `contradiction`: docs conflict on active behavior, rules, paths, or responsibilities.
- `instruction-strength-drift`: the same rule changes strength across docs.
- `agent-guidance-separation`: shared and agent-specific guidance are misplaced or only present in one agent file.
- `skill-contract-precedence`: a skill contract does not state how it relates to repo-level rules when conflict is plausible.
- `metadata-hygiene`: front matter, ADR metadata, skill metadata, or body-embedded metadata is invalid or inconsistent.
- `reference-integrity`: external references, local implementation paths, manifests, specs, or contracts are missing, stale, or too ambiguous to follow.
- `freshness-governance`: stale risk lacks replacement, deprecation, status, or update signals.
- `knowledge-structure`: durable knowledge lacks primary-home rules, resolver/index entrypoints, clear raw-vs-curated boundaries, or maintainable retrieval granularity.
- `provenance-gap`: important knowledge claims lack source, observation date, confidence, or enough context to distinguish direct, inferred, synthesized, and external claims.
- `relationship-graph-hygiene`: links, backlinks, aliases, or entity relationships are missing, duplicated, untyped, or too vague for agent traversal.
- `current-history-blur`: current truth, accepted policy, timeline evidence, historical notes, and temporary task context are mixed without a clear boundary.
- `policy-contamination`: active canonical docs or active skill instructions contain deprecated, temporary, fallback, retired, historical, or override wording as a current implementation, QA, release, or authoring option.
- `negative-reference-ambiguity`: active docs mention retired or deprecated vocabulary but do not make clear whether the occurrence is a prohibited term, migration map, historical reference, search-only audit pattern, or current option.
- `temporary-legitimacy`: temporary/fallback/workaround wording is treated as valid because it is documented, even though the repository's source-boundary rule requires current policy in docs, reasons in ADR, and local exceptions in source comments.
- `privacy-boundary`: public, internal, private, confidential, or machine-local knowledge boundaries are unclear to agents that may quote, index, commit, or expose content.
- `contract-traceability`: docs mention a contract/spec/implementation dependency but do not identify the canonical artifact to inspect.
- `stale-or-deprecated`: obsolete docs or skills remain discoverable as active.
- `todo-governance`: TODO/deferred work is scattered, ownerless, statusless, or expiry-less.
- `ai-readability`: document shape makes agent reading inefficient or error-prone.
- `reference-quality`: anchors, relative paths, named paths, or worktree-crossing references are ambiguous or broken.
- `terminology-drift`: repeated concepts use inconsistent terms that obscure whether rules are equivalent.
- `naming-taxonomy`: docs blur responsibility names, authoring-method labels, generated-artifact labels, or stable external selectors.
- `reading-cost`: required docs path is qualitatively too long or indirect for the task it supports; do not assign pseudo-precise token or minute estimates.

## Confidence

- `high`: directly supported by multiple files or an explicit source-of-truth rule.
- `medium`: directly supported by one source plus repository structure.
- `low`: plausible from naming, age, or absence of links, but needs human confirmation.
