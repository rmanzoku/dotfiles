---
name: agent-orchestration-evaluator
description: Evaluate and tune AI agent orchestration rules, model resolvers, skill role assignments, slash commands, and prompt harnesses so parent agents stay focused on orchestration while researcher/reviewer/worker roles are delegated to subagents or observable CLI runners. Use when asked to review or extract resolver semantics, Self-Elision, self vs subagent boundaries, multi-agent skill design, Claude/Codex/Gemini/Grok delegation, runner-skill migration, error-bypass remediation policy, or agent workflow evaluator/tuning guidance across projects.
---

# Agent Orchestration Evaluator

Evaluate or tune agent workflow instructions so they separate orchestration from delegated work. The core pattern is: `self` means parent-orchestrator direct execution for orchestration work only; concrete task execution belongs to delegated roles. Aliased AI roles such as researcher, reviewer, creator, worker, or judge should be delegated to a subagent when they resolve to the current provider/model, and to an observable runner or CLI subprocess when they resolve elsewhere.

## Modes

Choose the narrowest mode that matches the user request:

- `audit`: Report issues and recommended changes only. Use by default for "review", "evaluate", "diagnose", or "どう思う".
- `tune`: Edit the target files when the user asks to "切り出す", "反映", "修正", "更新", "skill にする", or otherwise requests implementation.
- `extract-skill`: Create or update a reusable skill from a project-specific resolver or orchestration rule. Use skill-creator rules for new skills; keep the extracted skill model-agnostic, preserve orchestration definitions and completion/verification criteria, and write ADR/docs only for durable architectural decisions rather than one-off examples.

When tuning, keep edits scoped to orchestration instructions, skill text, resolver docs, ADRs, and prompt harnesses. Do not change model IDs, tool permissions, or production code unless the user explicitly asks for that.

## Core Model

Use these terms consistently:

| Term | Meaning |
|---|---|
| Parent orchestrator | The entrypoint agent coordinating the task, artifacts, parallel workers, synthesis, and final response. |
| `self` | An explicit role assignment meaning the parent orchestrator directly performs orchestration work for the phase. Reserve for intent clarification, planning, delegation, artifact checks, synthesis, adjudication, and final output. Do not use for concrete task execution that can be delegated. |
| AI agent role | A delegated role such as researcher, reviewer, creator, worker, judge, analyzer, verifier, or implementation slice owner. |
| Self-Elision | Runtime optimization when a delegated role resolves to the same provider/model as the parent. Skip external CLI, but still delegate to a same-provider/model subagent. |
| Runner skill | A wrapper skill for observable Claude / Codex / Gemini / Grok CLI or API-backed subprocess execution, stream logs, timeouts, expected artifacts, and failure reports. |
| Resolver | Logic that maps role -> alias -> provider/model/config/execution mode. It should not become a raw command cookbook when runner skills exist. |
| Bypass remediation review | A separate review triggered when the parent or a delegated worker bypasses an error in a way that may recur, skip validation, reduce reproducibility, or reveal missing setup, permissions, dependencies, docs, hooks, or skills. |
| Promotion candidate | A repeated orchestration failure or waste pattern that may deserve a durable home such as resolver policy, runner hardening, AGENTS guidance, a skill, a script, a test, or an evaluator backlog item. |

## Invariants

Flag or fix violations of these invariants:

1. `self` and Self-Elision are not equivalent.
2. `self` is the only direct parent execution mode.
3. Parent orchestrators do not own concrete task execution. They clarify, plan, delegate, monitor artifacts, synthesize, adjudicate, and report.
4. Aliased AI agent roles are not performed by the parent orchestrator merely because the model matches.
5. Delegation should prefer subagents whenever the environment supports them, including for same-provider Self-Elision and for wrapping cross-provider runner-skill calls.
6. Self-Elision means "do not spawn an external CLI subprocess; spawn a same-provider subagent instead."
7. Cross-provider roles use a runner skill when available; otherwise use the resolver's CLI command contract. This includes Claude, Codex, Gemini, and Grok runner skills.
8. Runner skills own subprocess mechanics: prompt files, stream logs, timeout defaults, expected artifacts, summary, and failure reports.
9. Resolver docs own role/provider/model/config selection and execution-mode semantics, not wrapper internals.
10. Skills should reference the resolver/registry for concrete provider, model ID, effort, and config. Do not hard-code model names or effort settings in skill text except as examples clearly marked non-authoritative.
11. The rule is entrypoint-independent: Claude Code, Codex, Gemini, or another agent should follow the same logical resolver semantics.
12. Every fallback from subagent delegation must be explicit. Do not silently fall back to parent execution for delegated AI roles.
13. Delegated agents must not perform synthesis, final report editing, or orchestration decisions unless their role explicitly says so.
14. Execution-only roles such as `creator`, `apply_consensus`, formatter, or renderer should default to lightweight model settings such as low effort unless the resolver documents an eval-backed reason for a heavier setting.
15. Review and finding roles should not filter findings by vague importance bars during the discovery phase. Prefer coverage-first finding prompts, then rank, dedupe, or verify in a separate role or phase.
16. Tool-use policy should be explicit enough for required evidence gathering, but should not force fixed tool-call counts or stale progress scaffolds that fight newer model tool-triggering behavior.
17. Long-running delegated work must leave enough artifacts, summaries, and failure reports for the parent orchestrator to recover after context compaction or a runner restart.
18. Error bypasses must not silently become the accepted workflow. If a command, tool, environment, permission, dependency, or validation error is bypassed and recurrence, skipped validation, setup drift, or reproducibility risk remains, the workflow must trigger an explicit bypass remediation review.
19. Bypass remediation review may be delegated to a subagent, reviewer, evaluator, or runner when available, but the parent orchestrator must verify the proposed permanent fix against repository code, configuration, docs, tests, and managed state boundaries before adopting it.
20. Repeated fallback, subline execution, delegated-role confusion, or runner bypass observed in session history or an AI-usage coach report is evidence for an orchestration audit, not proof of an orchestration defect by itself.

## Audit Workflow

1. **Find sources of truth**
   - Inspect agent guidance files such as `AGENTS.md`, `CLAUDE.md`, `.codex/`, `.agents/`, `.claude/skills/**/SKILL.md`, `rules/**`, `docs/adr/**`, `prompts/**`, and slash command definitions.
   - Identify the canonical model registry or resolver if present.
   - Record assumptions in `.context/agent-orchestration-evaluator/<task>/scope.md` for non-trivial audits unless the user explicitly forbids file edits; in no-edit audits, include assumptions in the response instead.

2. **Map role resolution**
   - Build a table: skill/command, phase, role, role type, configured alias/model/provider, execution mode, artifact contract, fallback.
   - Classify each role as `self`, delegated AI agent role, runner invocation, or non-agent tool work.
   - Treat role names like `researcher_*`, `reviewer_*`, `creator`, `worker`, `judge`, `agent`, `subagent`, and `assistant` as likely delegated AI roles unless the local docs clearly define otherwise.
   - Identify execution-only roles that consume an already planned prompt or consensus output, such as `creator`, `apply_consensus`, doc renderer, formatter, or conversion worker.

3. **Check boundaries**
   - Look for wording that says Self-Elision means "current agent directly executes", "execute as self", "親が兼任", or similar.
   - Look for `self` phases that perform concrete task execution instead of orchestration.
   - Look for raw CLI construction inside skills when a runner skill exists.
   - Look for subagent fallbacks that silently become direct parent execution.
   - Look for delegated prompts that allow Phase C/D synthesis, final edits, or reading other workers' outputs without an explicit reason.
   - Look for skills that hard-code concrete model names, provider names, effort settings, timeout defaults, or CLI flags that should come from a resolver/registry or runner skill.
   - Look for code-review prompts that tell finding roles to report only high-severity, important, or certain issues before a separate ranking or verification phase.
   - Look for fixed tool-call quotas, forced progress checkpoints, or stale "always use tools" language that should be replaced by outcome/evidence-based tool guidance.
   - Look for wording that tells agents to "find another way", "work around", "skip", "continue anyway", "ignore", or "use a fallback" after errors without defining when a bypass remediation review is required.
   - Look for workflows where failed tests, missing tools, permission errors, dependency problems, authentication issues, broken hooks, or unavailable subagents/runners can be bypassed without recording the cause, validation gap, permanent-fix candidate, and owner.
   - When a coach report, session audit, or structured usage report identifies repeated fallback or wasted subline execution, trace it back to resolver semantics, runner contracts, prompts, and docs before deciding whether the durable home is orchestration policy, a skill, a script, a test, or no promotion.

4. **Evaluate model and effort policy**
   - Check whether skills only name logical roles and resolver paths, not concrete model IDs.
   - Check whether the resolver assigns lightweight settings to execution-only roles that mainly follow an existing plan.
   - Require a documented reason, eval result, or risk argument before `creator`-like roles use high/xhigh/deep reasoning by default.
   - For review, researcher, and judge roles, check whether effort escalation is tied to task risk, evidence needs, or eval results rather than prompt magic words.
   - Keep model allocation changes in the resolver/registry, not scattered across skill text.

5. **Evaluate execution contracts**
   - Delegated work should have an outcome-first prompt, source prompt file when large, expected artifacts, success criteria, allowed side effects, evidence rules, timeout/budget guard, and blocked-state reporting.
   - CLI runner calls should preserve observability: stream logs, stderr, summary, failure artifact, elapsed time, and expected artifact checks.
   - Check Claude, Codex, Gemini, and Grok roles for available runner skills before accepting raw `claude`, `codex`, `gemini`, `grok`, direct API, or ad hoc wrapper calls inside skill text.
   - Same-provider subagents should have a bounded responsibility and a clear return artifact or final report shape.
   - Long-running roles should write summaries, blocked-state reports, and expected artifacts in stable paths so compaction does not make the work unrecoverable.
   - Bypass remediation reviews should classify the error cause, temporary bypass, permanent-remediation options, repo-managed changes, machine-local state, and verification plan.
   - If the bypass review is delegated, check that the subagent or runner prompt forbids direct adoption of its proposal and requires the parent to verify against source-of-truth files.
   - Treat promotion candidates as review inputs. Require recurrence, friction, risk, portability, and future-value evidence before recommending a reusable orchestration rule or skill.

6. **Report or tune**
   - In `audit` mode, produce findings first with path references and recommended wording.
   - In `tune` mode, patch the canonical resolver first, then dependent skills/prompts, then ADR or durable rationale if the change is architectural.

## Tuning Patterns

### Replace Direct Self-Elision

Bad:

```text
If resolved provider/model matches current agent, execute as self and skip command construction.
```

Good:

```text
If resolved provider/model matches current agent, skip external CLI subprocess construction and delegate the role to a same-provider/model subagent. The parent orchestrator must not perform aliased AI agent roles directly.
```

### Separate `self` From Delegated Roles

Use `self` for orchestration phases. These phases may decide and synthesize, but should not perform concrete worker tasks when delegation is available:

```yaml
roles:
  understand: self
  synthesize: self
  adjudicate: self
```

Use aliases for delegated work:

```yaml
roles:
  researcher_1: { alias: claude_researcher }
  researcher_2: { alias: codex_researcher }
  reviewer_1: { alias: claude_reviewer }
```

### Keep Skills Model-Agnostic

Skills should point to the resolver or registry path:

```markdown
**Model resolution**: `rules/model_registry.yaml` -> `skills.<skill>.roles.<role>`
```

Avoid authoritative model details in skills:

```markdown
Bad: `researcher_2` uses `gpt-5.5` with `medium`.
Good: `researcher_2` resolves through `skills.research.roles.researcher_2`; concrete model and effort live in the resolver/registry.
```

If a skill includes an example command or model for illustration, mark it non-authoritative and verify it cannot drift from the resolver.

### Prefer Lightweight Execution Models

For roles that execute an already planned prompt, apply accepted changes, render artifacts, format output, or perform a bounded conversion, check that the resolver defaults to a lightweight setting such as low effort. Escalate only when there is evidence that the role must make novel design judgments, handle ambiguous requirements, or resolve conflicts.

Typical policy:

| Role type | Default expectation |
|---|---|
| `creator`, `apply_consensus`, renderer, formatter | Lightweight / low effort unless evals justify more. |
| `researcher`, `reviewer`, `judge`, architecture analyzer | Medium or higher depending on risk and evidence needs. |
| Parent `self` orchestration | No concrete model allocation inside the skill; uses the entrypoint agent. |

### Define Provider-Specific Same-Provider Delegation

Keep this as execution guidance, not model allocation:

| Current provider | Same-provider delegation |
|---|---|
| `claude_code` | Claude Code subagent / Agent tool, with the skill's artifact contract. |
| `codex` | `spawn_agent`, with explicit ownership and expected artifacts. |
| `gemini` | Gemini subagent mechanism if available; otherwise use the skill's explicit fallback. |
| Other | Define explicitly before relying on Self-Elision. |

### Preserve Runner Ownership

When a role resolves to a different provider and a runner skill exists, say:

```text
The resolver determines role/provider/model/config. The runner skill performs the subprocess execution and owns prompt-file handling, timeout, stream logs, expected artifact checks, summary, and failure reporting.
```

Avoid duplicating wrapper command lines in every skill unless no runner exists.

Expected runner mapping:

| Provider / backend | Preferred runner |
|---|---|
| Claude Code CLI | `claude-cli-runner` |
| Codex CLI | Use `codex-cli-runner` when available; do not inline `codex exec` details in dependent skills. If unavailable, keep only an explicit resolver fallback contract. |
| Gemini CLI | `gemini-cli-runner` |
| Grok CLI or API-backed handoff | `grok-cli-runner` |

Prefer runners that provide prompt-file handoff, timeout control, expected artifact checks, summary, and failure reporting. Keep the skill text at the level of "use the runner skill"; do not inline runner command details.

### Separate Finding From Filtering

For review harnesses and bug-finding roles, check whether the prompt separates broad discovery from downstream ranking:

```text
Finding role: report every plausible issue with confidence and estimated severity.
Verifier/ranker role: dedupe, rank, and decide what meets the final reporting bar.
```

Avoid vague discovery-phase filters such as "only important issues" or "be conservative" unless the role is explicitly a final reporting filter.

### Use Outcome-Based Tool Guidance

Tool guidance should describe the evidence or state required, not a fixed number of calls:

```text
Use repository search before claiming a symbol is unused. Use web fetch only for cited current external docs.
```

Avoid stale scaffolds such as mandatory progress updates every N tool calls or unconditional tool use when the task can be completed directly.

### Detect Silent Error Bypasses

Flag workflow text that lets an agent bypass errors without a durable review path:

```text
Bad: If the command fails, use another method and continue.
Good: If the command fails, use a temporary bypass only when it preserves validation. Trigger bypass remediation review when the failure may recur, skips validation, reveals missing setup, or lowers reproducibility.
```

Recommended remediation review contract:

- Error cause and observed command/tool output summary.
- Temporary bypass used and what validation it preserves or loses.
- Permanent-fix candidates across repo-managed config/docs/hooks/skills and machine-local state.
- Whether a subagent, reviewer, evaluator, or runner should investigate the permanent fix.
- Verification required before adopting the fix.

### Delegated Prompt Contract

Subagent or runner prompts should include:

- Role and scope.
- Working directory.
- Source prompt path for multi-line instructions.
- Expected artifact paths.
- Success criteria and blocked-state reporting.
- Allowed side effects.
- Evidence rules.
- Compaction/restart recovery expectations for long-running work.
- Prohibition on orchestration, synthesis, final response editing, and reading sibling worker outputs unless explicitly allowed.

## Output Format

For audits, return:

```markdown
## Findings

- [P1] <short title> — <path:line>
  <why it breaks orchestration boundaries and what to change>

## Role Map

| Skill/Command | Role | Current mode | Expected mode | Notes |
|---|---|---|---|---|

## Recommended Changes

- <canonical resolver change>
- <dependent skill/prompt changes>

## Verification

- <lint/validation/searches run>
- <remaining risks>
```

For tuning, also list files changed and validation commands run.

## Completion Rules

Stop only when:

- The canonical resolver or equivalent guidance clearly distinguishes `self` from Self-Elision.
- Delegated AI roles have an explicit subagent or runner path.
- Parent `self` phases are limited to orchestration responsibilities, not concrete task execution.
- Skills reference resolver/registry paths instead of hard-coding concrete model names, effort, or provider config.
- Claude, Codex, Gemini, and Grok cross-provider invocations use available runner skills instead of raw command or ad hoc API calls.
- Execution-only roles such as `creator` use lightweight defaults unless a documented reason says otherwise.
- Fallbacks are explicit and do not silently assign worker roles to the parent orchestrator.
- Dependent skills/prompts no longer contradict the canonical resolver.
- Review/finding roles preserve discovery coverage before final filtering.
- Long-running runner or subagent roles leave recoverable artifacts for compaction or restart.
- Error bypasses that may recur, skip validation, or reduce reproducibility trigger an explicit bypass remediation review with cause, temporary bypass, permanent-fix candidates, ownership boundary, and verification plan.
- Durable architectural changes are recorded in the target repo's ADR or equivalent long-lived documentation when the repo requires it.
