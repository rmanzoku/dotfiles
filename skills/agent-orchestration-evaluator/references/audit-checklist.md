# Audit Checklist

Read this reference only in `audit` mode.

## Workflow

1. **Find sources of truth.** Inspect applicable agent guidance, resolver/registry, skills, prompts, ADRs, and command definitions. Follow `SKILL.md`'s Output Format for conditional run-evidence artifacts; audit mode alone does not require one. If the user forbids all file writes, keep assumptions and evidence in the response.
2. **Map role resolution.** Build a table for each in-scope skill or command: phase, role, role type, configured alias/model/provider, executor and billing source, execution mode, artifact contract, and fallback. Classify each role as `self`, delegated AI agent role, runner invocation, or non-agent tool work. Treat names such as `researcher_*`, `reviewer_*`, `creator`, `worker`, `judge`, `agent`, `subagent`, and `assistant` as likely delegated roles unless local guidance defines them otherwise. Identify execution-only roles that consume an existing plan or consensus.
3. **Check boundaries.** Evaluate the applicable Core Model and Invariants, especially delegation benefit and ownership (1–5, 11–12, 21), resolver and runner ownership (6–10, 23–25), execution-role effort (13), finding and tool guidance (14–15, 20, 22), and recovery and bypass handling (16–19). Review/researcher/judge effort escalation must follow task risk, evidence needs, or eval results rather than prompt magic words. Trace coach or session observations back to source-of-truth files before treating them as defects.
4. **Evaluate execution contracts.** Check outcome-first prompts, source prompt files when large, bounded responsibility, allowed side effects, evidence, timeout/budget guard, blocked-state reporting, runner observability, and recovery artifacts only where needed. Check runner availability before accepting raw CLI/API calls. For bypass remediation, classify cause, temporary bypass, permanent candidates, managed-state boundary, owner, and verification plan.
5. **Report without editing sources.** Give findings first with path references and recommended wording, then the role map when applicable, limitations, recommendations, and verification plan. Read [tuning-patterns.md](tuning-patterns.md) only when concrete recommended wording needs its examples. Treat promotion candidates as review inputs; require recurrence, friction, risk, portability, and future-value evidence before recommending a reusable rule or skill.

## Audit Acceptance Criteria

- Cover the user-requested scope and cite the inspected source for each finding.
- Distinguish observations from recommendations and unresolved limitations.
- Do not claim that source defects are fixed or edit target/source files. Run-evidence artifacts follow the conditional permission in `SKILL.md`'s Output Format.
