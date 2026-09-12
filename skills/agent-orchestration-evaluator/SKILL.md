---
name: agent-orchestration-evaluator
description: "Evaluate and tune AI agent orchestration assets: model resolvers, Self-Elision, skill role assignments, delegation boundaries, and prompt harnesses. Use when reviewing resolver semantics, multi-agent skill design, runner-skill migration, or agent workflow tuning."
---

# Agent Orchestration Evaluator

Evaluate or tune agent workflow instructions so delegation is used where it improves parallelism, context isolation, specialty coverage, or required independence. Existing-contract work that remains within one owner may be performed directly by the parent. A matching provider or model does not decide that choice; cross-provider delegated work uses an observable runner or CLI subprocess when available.

## Modes

Choose the narrowest mode that matches the user request:

- `audit`: Report issues and recommended changes only. Use by default for "review", "evaluate", "diagnose", or "どう思う". Read [references/audit-checklist.md](references/audit-checklist.md).
- `tune`: Edit the target files when the user asks to "切り出す", "反映", "修正", "更新", "skill にする", or otherwise requests implementation. Read [references/tuning-patterns.md](references/tuning-patterns.md).
- `extract-skill`: Create or update a reusable skill from a project-specific resolver or orchestration rule. Use the existing `skill-creator` skill for its extract/update workflow, then read [references/tuning-patterns.md](references/tuning-patterns.md) for applicable orchestration patterns. Keep the extracted skill model-agnostic, preserve orchestration definitions and completion/verification criteria, and write ADR/docs only for durable architectural decisions rather than one-off examples.

When tuning, keep edits scoped to orchestration instructions, skill text, resolver docs, ADRs, and prompt harnesses. Do not change model IDs, tool permissions, or production code unless the user explicitly asks for that.

## Core Model

Use these terms consistently:

| Term | Meaning |
|---|---|
| Parent orchestrator | The entrypoint agent coordinating the task, direct owner-local work when appropriate, handoffs, parallel workers, synthesis, and final response. |
| `self` | An explicit role assignment meaning the parent handles the work directly. It may cover orchestration or existing-contract work that remains within one owner when delegation is not warranted. |
| AI agent role | A delegated role such as researcher, reviewer, creator, worker, judge, analyzer, verifier, or implementation slice owner. |
| Self-Elision | Runtime optimization when a delegated role resolves to the same provider/model as the parent. Skip external CLI and choose direct execution or a same-provider subagent under the same delegation criteria. |
| Runner skill | A wrapper skill for observable Claude / Codex / Gemini / Grok / Copilot CLI or API-backed subprocess execution, stream logs, timeouts, expected artifacts, and failure reports. |
| Resolver | Logic that maps role -> alias -> provider/model/config/execution mode. It should not become a raw command cookbook when runner skills exist. |
| Executor / billing source | The CLI, subagent surface, or service that actually serves a resolved model, plus how that execution is billed (provider subscription, metered API budget, or credit pool). The same model can be servable by more than one executor; the runner contract and budget rules follow the executor, not the model vendor. |
| Bypass remediation review | A separate review triggered when the parent or a delegated worker bypasses an error in a way that may recur, skip validation, reduce reproducibility, or reveal missing setup, permissions, dependencies, docs, hooks, or skills. |
| Promotion candidate | A repeated orchestration failure or waste pattern that may deserve a durable home such as resolver policy, runner hardening, AGENTS guidance, a skill, a script, a test, or an evaluator backlog item. |

## Invariants

Flag or fix violations of these invariants:

1. `self` and Self-Elision are not equivalent.
2. Parent direct execution is valid for existing-contract work within one owner when parallelism, context isolation, specialty coverage, and independent review do not justify delegation.
3. Phase names, role names, and a matching model do not by themselves require delegation or prohibit direct execution.
4. Delegated work has a bounded owner and an explicit reason for the delegation.
5. Self-Elision means "do not spawn an external CLI subprocess"; it does not determine whether the parent works directly or delegates to a same-provider subagent.
6. Cross-provider delegated work uses a runner skill when available; otherwise use the resolver's CLI command contract. This includes Claude, Codex, Gemini, Grok, and Copilot runner skills.
7. Runner skills own subprocess mechanics: prompt files, stream logs, timeout defaults, expected artifacts, summary, and failure reports.
8. Resolver docs own role/provider/model/config selection and execution-mode semantics, not wrapper internals.
9. Skills should reference the resolver/registry for concrete provider, model ID, effort, and config. Do not hard-code model names or effort settings in skill text except as examples clearly marked non-authoritative.
10. The rule is entrypoint-independent: Claude Code, Codex, Gemini, or another agent should follow the same logical resolver semantics.
11. A fallback from delegation must be explicit. Reconsidering direct parent execution is allowed only when it meets the same owner, scope, and delegation criteria.
12. Delegated agents must not perform synthesis, final report editing, or orchestration decisions unless their role explicitly says so.
13. Execution-only roles such as `creator`, `apply_consensus`, formatter, or renderer should default to lightweight model settings such as low effort unless the resolver documents an eval-backed reason for a heavier setting.
14. Review and finding roles should not filter findings by vague importance bars during the discovery phase. Prefer coverage-first finding prompts, then rank, dedupe, or verify in a separate role or phase.
15. Tool-use policy should be explicit enough for required evidence gathering, but should not force fixed tool-call counts or stale progress scaffolds that fight newer model tool-triggering behavior.
16. Long-running delegated work leaves enough handoff evidence, summaries, and failure reports for recovery after context compaction or a runner restart. Artifacts carry references to canonical sources when an artifact is needed; a summary must not replace the source it summarizes.
17. Error bypasses must not silently become the accepted workflow. If a command, tool, environment, permission, dependency, or validation error is bypassed and recurrence, skipped validation, setup drift, or reproducibility risk remains, the workflow must trigger an explicit bypass remediation review.
18. Bypass remediation review may be delegated to a subagent, reviewer, evaluator, or runner when available, but the parent orchestrator must verify the proposed permanent fix against repository code, configuration, docs, tests, and managed state boundaries before adopting it.
19. Repeated fallback, subline execution, delegated-role confusion, or runner bypass observed in session history or an AI-usage coach report is evidence for an orchestration audit, not proof of an orchestration defect by itself.
20. Roles that generate changes must not weaken or rewrite their own acceptance criteria — tests, specs, or completion definitions — without a separate gate or role.
21. Scaling generation throughput (fan-out, parallel workers, autonomous loops) must be paired with matching verification and cleanup capacity, and goal contracts must include stop conditions and cleanup of superseded artifacts.
22. Model-generation behavior compensation — delegation encouragement or suppression, mandatory self-check passes, forced progress scaffolds — belongs in the resolver, model adapters, or runner prompt profiles, not in role prompts or skill text; a newer model generation can invert the bias the compensation was written for.
23. Role resolution covers model, executor, and billing source as separate dimensions. When a model is served through another provider's CLI or surface, the runner contract, budget guard, and usage reporting follow the executor, not the model vendor.
24. Subscription-covered standard models are the routine default; metered or credit-billed execution paths — API budgets, credit pools, premium tiers with special retention or pricing — require an explicit per-run budget contract and never become silent defaults or fallbacks. Concrete standard-model and executor choices live in the resolver/registry/ADR, not in skill text, and per-project executor overrides are declared in that project's resolver.
25. Runner data is model-neutral: selection covers in-scope repo/docs; retention is not reapproval. Exclude secrets/credentials/sessions.

## Runner Mapping

Expected runner mapping:

| Provider / backend | Preferred runner |
|---|---|
| Claude Code CLI | `claude-cli-runner` |
| Codex CLI | Use `codex-cli-runner` when available; do not inline `codex exec` details in dependent skills. If unavailable, keep only an explicit resolver fallback contract. |
| Grok CLI or API-backed handoff | `grok-cli-runner` |
| Copilot CLI | `copilot-cli-runner` |
| Gemini backend (Antigravity CLI) | `agy-cli-runner` |

The runner follows the executor, not the model vendor: a Claude model routed through the Copilot CLI uses `copilot-cli-runner` and its credit contract, not `claude-cli-runner`.

## Output Format

For `audit`, report findings, evidence, limitations, recommendations, and a verification plan. Include a Role Map when roles or commands are in scope. Do not edit target/source files. Create run-evidence artifacts under `.context/agent-orchestration-evaluator/<task>/` only for a handoff, user-requested audit trail, identity, or recovery need. If the user forbids all file writes, keep assumptions and evidence in the response instead.

For `tune` and `extract-skill`, report the requested change, applicable existing invariants, files changed, verified edits, required durable decision documentation, and validation run. Do not require unrelated repository-wide defects to be fixed.

## Completion Rules

### `audit`

Complete when the report covers the inspected scope with findings or an explicit no-finding result, supporting evidence, limitations, recommendations, and a verification plan. Source defects may remain because this mode does not edit them.

### `tune`

Complete when the requested edits satisfy the applicable existing invariants, in-scope dependent skills/prompts do not contradict the canonical resolver or equivalent guidance, edits are verified, and durable architectural decisions are recorded in ADRs or equivalent long-lived documentation when the target repository requires them. Apply the user's acceptance criteria and existing invariants in the requested scope, including explicit fallback reassessment, runner ownership, recovery evidence when needed, separate acceptance gates, and bypass remediation review.

### `extract-skill`

Complete when the reusable skill is created or updated through `skill-creator`, preserves applicable orchestration definitions and completion/verification criteria, is model-agnostic, and has verified edits plus any required durable decision documentation. Apply the existing invariants and user's acceptance criteria only to the requested extraction scope.
