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

## Raw Excerpts In Trusted-Local Mode

Raw excerpts are allowed only when all are true:

1. The mode is `trusted-local`.
2. The excerpt is necessary for coaching.
3. The excerpt is short.
4. Privacy scan has no blocking finding for that excerpt.
5. The report is marked `shareable: false`.

## Preferred Evidence

Prefer this:

> The user gave an implementation task but did not name a verification command.

Avoid this in shareable output:

> Raw quoted prompt text.

## Failure Handling

If privacy scan fails in `shareable` or `teacher-pack` mode, stop and produce only:

- failure summary,
- blocked reason,
- path to the private report if one exists,
- required redaction action.
