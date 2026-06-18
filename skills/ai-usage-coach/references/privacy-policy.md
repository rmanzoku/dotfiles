# Privacy Policy

This skill may inspect sensitive AI usage logs in `trusted-local` mode. Treat raw data as local-only.

## Never Include In Shareable Output

- Prompt bodies.
- Full assistant responses.
- System-level instruction fields.
- Emails.
- Absolute local filesystem paths.
- Secrets, access tokens, API keys, cookies, session IDs, or private URLs.
- `op://` secret references.
- Long raw JSON records.
- Customer names, customer-specific business details, contracts, production incident details, or field artifacts unless they are intentionally public and explicitly allowed.

## Raw Excerpts In Trusted-Local Mode

Raw excerpts are allowed only when all are true:

1. The mode is `trusted-local`.
2. The excerpt is necessary for coaching.
3. The excerpt is short.
4. Privacy scan has no blocking finding for that excerpt.
5. The report is marked `shareable: false`.

## Concrete Evidence In Trusted-Local Mode

Trusted-local reports should not become generic dashboards. Prefer concrete local-only examples that are useful but controlled:

- repo or workflow labels,
- command classes rather than full shell histories,
- failure shapes such as "verification command discovered after implementation",
- short paraphrases of prompt intent,
- short redacted excerpts only when paraphrase loses the coaching point.

In `trusted-local`, concrete repo or workflow labels are allowed when they are already present in the reviewed evidence and are not customer-identifying field details. Do not replace useful repo labels with vague categories such as "wallet app 系" solely for privacy.

Do not include full prompt bodies, long assistant responses, absolute paths, emails, secrets, tokens, cookies, private URLs, customer-identifying field details, contracts, or raw JSON records.

## Preferred Evidence

Prefer this:

> The user gave an implementation task but did not name a verification command.

Prefer this in trusted-local when concrete detail matters:

> In the `repo-a` verification workflow, the test command was discovered after implementation instead of being pinned before edits.

Avoid this in shareable output:

> Raw quoted prompt text.

## Failure Handling

If privacy scan fails in `shareable` or `teacher-pack` mode, stop and produce only:

- failure summary,
- blocked reason,
- path to the private report if one exists,
- required redaction action.
