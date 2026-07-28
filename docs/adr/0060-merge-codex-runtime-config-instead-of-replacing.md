---
title: "Merge Codex Runtime Config Instead of Replacing It"
date: 2026-07-28
agent: "Claude Opus 5"
---

# ADR 0060: Merge Codex Runtime Config Instead of Replacing It

## Context

`~/.codex/config.toml` and `~/.codex/automations/` had carried unapplied drift
for a long time. Inspection showed why: applying would only have removed things.
Everything the target held that source did not was either written by Codex
Desktop at runtime or granted interactively by the user.

Target-only content, at the time of measurement:

- 11 sections plus one key written by Codex Desktop — two MCP server
  definitions, four plugin entries, two marketplace entries, a desktop section,
  a shell environment policy carrying Desktop-specific variables, and a feature
  flag.
- 5 project trust entries, added as the user granted trust to repositories
  while working.

Source-only content: none. A `chezmoi apply` was therefore a pure deletion, and
the drift persisted because applying it would have broken the Desktop
integration.

Trust levels could not be simplified away either. Codex resolves
`[projects."<path>"]` by exact match and normalized exact match only — the
resolution path performs no ancestor walk — and the config schema models
`projects` as a plain path-to-config map with no glob and no global default.
The setting is absent from the published configuration documentation. Source
already listed two ancestor paths, and individual descendants kept accumulating
anyway, which is the behaviour the implementation predicts.

## Decision

Manage `config.toml` through a `modify_` script that merges rather than
replaces. Source declares the settings it owns; every other key and section
already in the file is preserved. Merging happens per key, not per section, so
a Desktop-written key inside a section that source also declares survives.

Project trust levels are no longer declared in source. Since resolution is
exact-match only, listing ancestor paths neither scales to daily work nor
reduces the number of entries that accumulate. Trust is machine-local state:
the record of what this user approved on this machine, which is what ADR-level
guidance already says to keep out of declarative management.

Move `~/.codex/automations/` out of git entirely and manage it through the
1Password-backed materialization workflow of ADR 0039. Automations mix
general-purpose and project-specific definitions, and deciding per file which
is which is recurring overhead for little benefit. chezmoi still deploys them;
only git tracking changes.

Automation definitions get the same `modify_` treatment, for the same reason:
Codex Desktop writes a resolved project target and created/updated timestamps
into each `automation.toml`, and a plain managed file would delete them. The
prompt, schedule, model, and status stay declarative; the machine-local fields
are preserved from whatever is on disk.

## Consequences

`chezmoi apply` becomes safe to run for Codex config, so drift stops
accumulating. Runtime state written by Desktop and trust granted during work
both survive. Adding a new managed setting means editing the script's declared
block; adding a trusted project means nothing, because Codex records it and the
merge keeps it.

The cost is that `config.toml` is now a script rather than a template, so its
content is one indirection away from the source tree, and a reader has to know
that unmanaged keys in the deployed file are intentional rather than drift.

Automation definitions are no longer visible in git history. Recovering them on
a new machine depends on the 1Password manifest, in the same way as the other
private files under that workflow.
