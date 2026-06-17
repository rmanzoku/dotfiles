# Modes

## trusted-local

Use when the user reviews their own raw local logs or transcripts on the same machine.

Requirements:

- Set `shareable: false`.
- Save outputs under `.context/ai-usage-coach/<task>/` unless the user explicitly chooses another private path.
- Raw excerpts must be short and necessary.
- Run `scripts/privacy_scan.py` and report warnings.
- Warn that the report must not be committed, published, or pasted into shared channels.

## shareable

Use when the report may leave the local machine.

Requirements:

- Set `shareable: true`.
- Do not include raw prompt or response excerpts.
- Use behavior-level evidence only.
- Run `scripts/privacy_scan.py --mode shareable`; failure blocks delivery.

## teacher-pack

Use when producing reusable teaching material.

Requirements:

- Raw logs and raw prompt examples are prohibited.
- Use synthetic examples, archetypes, and teacher moves.
- Do not include absolute paths, internal repository names, private URLs, customer names, emails, or secret references unless intentionally public and explicitly allowed.
- Run `scripts/privacy_scan.py --mode teacher-pack`; failure blocks delivery.

## Mode Escalation

If a user asks to share a `trusted-local` report, produce a new `shareable` version instead of editing the local report in place.
