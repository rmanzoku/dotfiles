# Docs Evaluator Rubric

Use this rubric to score the documentation system as a graph of active guidance, canonical sources, and historical records.

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

### AI Readability

- Documents are necessary and sufficient for an AI agent to complete common tasks without reading excessive unrelated history.
- Reading order is explicit enough to avoid both missed rules and unnecessary deep dives.
- Documents are chunkable: scoped headings, concise sections, stable names, and structured lists where useful.
- The required reading path has a reasonable qualitative burden and does not force agents through irrelevant history.

### Consistency

- Duplicate rules do not conflict.
- Skill descriptions, AGENTS/CLAUDE guidance, README/docs index, and spec docs agree on triggers, responsibilities, and canonical paths.
- Deprecated docs or skills are removed, marked deprecated, or isolated from active navigation.
- Instruction strength is consistent: MUST/SHOULD/MAY and 必須/推奨/任意/禁止/原則禁止 do not drift across docs for the same rule.
- Shared guidance and agent-specific guidance are separated intentionally across AGENTS, CLAUDE.md, GEMINI.md, QWEN.md, Codex guidance, and skill docs.
- Skill docs explain whether they inherit repo rules, override a specific procedure, or provide a narrower contract.
- Terminology for repeated operational concepts is stable enough that agents can match equivalent rules without guessing; do not treat general prose style as a finding.

### Reference Integrity

- External links, external tool references, package or manifest references, and local implementation paths are explicit enough to follow.
- Docs identify the relevant spec, contract, manifest, schema, script, or source path when they depend on one.
- Freshness signals such as deprecation wording, replacement links, accepted ADR status, manifest membership, or git history are considered before declaring stale risk.
- The evaluator does not verify source implementation correctness; it reports missing or unclear documentation traceability.

### Task and Gap Governance

- TODO, Deferred Work, known gaps, and follow-up tasks have an owner, status, destination, or expiry.
- Follow-up notes are not scattered across ADRs, scratchpads, comments, and docs without a canonical tracker.
- Temporary findings that should change canonical docs are tracked until reflected or explicitly rejected.

### Metadata Hygiene

- Markdown metadata lives in front matter where the repo requires it.
- ADRs include required status/date/worked_at/agent_model fields when the repo expects them.
- Skills include valid `name` and `description` front matter and keep UI metadata in `agents/openai.yaml`.
- Body text does not carry stale metadata blocks that should be machine-readable.
- Metadata findings are limited to repo-declared requirements and active documentation contracts.

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
- `temporary-gap`: temporary content has not been reflected, tracked, or expired.
- `contradiction`: docs conflict on active behavior, rules, paths, or responsibilities.
- `instruction-strength-drift`: the same rule changes strength across docs.
- `agent-guidance-separation`: shared and agent-specific guidance are misplaced or only present in one agent file.
- `skill-contract-precedence`: a skill contract does not state how it relates to repo-level rules when conflict is plausible.
- `metadata-hygiene`: front matter, ADR metadata, skill metadata, or body-embedded metadata is invalid or inconsistent.
- `reference-integrity`: external references, local implementation paths, manifests, specs, or contracts are missing, stale, or too ambiguous to follow.
- `freshness-governance`: stale risk lacks replacement, deprecation, status, or update signals.
- `contract-traceability`: docs mention a contract/spec/implementation dependency but do not identify the canonical artifact to inspect.
- `stale-or-deprecated`: obsolete docs or skills remain discoverable as active.
- `todo-governance`: TODO/deferred work is scattered, ownerless, statusless, or expiry-less.
- `ai-readability`: document shape makes agent reading inefficient or error-prone.
- `reference-quality`: anchors, relative paths, named paths, or worktree-crossing references are ambiguous or broken.
- `terminology-drift`: repeated concepts use inconsistent terms that obscure whether rules are equivalent.
- `reading-cost`: required docs path is qualitatively too long or indirect for the task it supports; do not assign pseudo-precise token or minute estimates.

## Confidence

- `high`: directly supported by multiple files or an explicit source-of-truth rule.
- `medium`: directly supported by one source plus repository structure.
- `low`: plausible from naming, age, or absence of links, but needs human confirmation.
