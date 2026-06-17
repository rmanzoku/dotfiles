# Teacher Baseline v0

This baseline is derived from local trusted-log analysis, but it contains only abstract counts and behavior signals. It does not include raw prompts, assistant responses, paths, emails, secrets, or system instructions.

## Extraction Scope

- Window: recent 30 local days at the time of extraction.
- Sessions sampled: 254.
- Sources: 160 Claude sessions and 94 Codex sessions.
- User messages counted: 16,076.
- Assistant messages counted: 30,730.
- Tool calls counted: 16,130.
- Raw excerpts included: no.

## Abstract Signal Counts

| Signal | Count |
|---|---:|
| artifact | 223 |
| verification | 167 |
| delegation | 109 |
| recovery | 87 |
| scope | 74 |
| skill | 54 |
| intent | 51 |
| privacy | 47 |

Interpretation:

- `artifact`, `verification`, `delegation`, and `recovery` are prominent teacher signals.
- The baseline supports the profile that strong AI usage is not just prompt wording; it is artifact-backed, verification-aware, and delegation-conscious.
- `intent`, `scope`, `skill`, and `privacy` appear less often as explicit textual signals. Do not interpret this as unimportant; they may be expressed structurally or implicitly.

## Tool Mix Signals

Top observed tool categories:

| Tool | Count |
|---|---:|
| Bash | 5,491 |
| Edit | 2,943 |
| Read | 2,110 |
| exec_command | 1,772 |
| Write | 986 |
| TaskUpdate | 407 |
| AskUserQuestion | 283 |
| TaskCreate | 216 |
| WebSearch / web_search | 374 |
| Agent | 108 |
| Skill | 92 |

Interpretation:

- The teacher baseline is CLI- and artifact-heavy.
- The presence of `Agent`, `TaskCreate`, `TaskUpdate`, and delegation signals supports an orchestration-first teaching pattern.
- Tool counts are not a target. Do not penalize a user for using fewer tools when their task does not require them.

## How To Use This Baseline

Use for period review only:

- Compare whether a user's recent sessions show any evidence of verification, artifacts, recovery planning, and delegation where the task calls for them.
- Use the baseline to choose teacher moves, not to produce a similarity score.
- State differences as behavior gaps, not personal shortcomings.

Avoid:

- "Teacher uses Bash more, so user should use Bash more."
- "Teacher has more tool calls, so user is better if they have more tool calls."
- "Teacher signal count is the correct target."

Prefer:

- "This period has repeated implementation requests without verification evidence. Teacher move: require success condition and verification command."
- "Long-running sessions lack recoverable artifacts. Teacher move: add an artifact gate."

## Limitations

- Counts are based on keyword and tool-name signals, not full semantic review.
- Some high-quality behavior may not be visible in abstract signal counts.
- Some signals may be inflated by repeated workflow text.
- This baseline should be refreshed after the teacher-pack changes materially.
