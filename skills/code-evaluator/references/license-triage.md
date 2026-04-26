---
name: license-triage
description: License, distribution context, and dependency remediation guidance for code-evaluator.
---

# License Triage

This is engineering triage, not legal advice or compliance clearance. Evaluate whether the observed dependency use appears compatible with the stated commercial/service context and whether follow-up is needed.

## Core Approach

Do not use a blanket "GPL is forbidden" rule. License risk depends on distribution context, license obligations, whether source/notice obligations can be met, and whether remediation evidence exists.

Treat these as strong blockers or needs-confirmation:

- No license or unclear license.
- Commercial use prohibited.
- Non-commercial-only.
- Field-of-use restriction.
- Unknown provenance or vendored code with no clear license.

## Distribution Context

Classify each relevant component before judging risk:

| Context | Examples | Default scrutiny |
|---|---|---|
| `client-distributed` | frontend bundle, mobile app, CSS/assets shipped to users | High |
| `server-side-only` | backend service code not distributed to customers | Lower, except AGPL/SaaS/network clauses and deployment artifacts |
| `dev-only-tooling` | test/lint/build tools not shipped | Lower, but still check policy and license clarity |
| `distributed-cli-sdk-image` | CLI, SDK, Docker image, binary, embedded code sent to customers | High |
| `unknown` | Cannot infer | Conservative; mark needs-confirmation |

For this repository's typical shape, `frontend/` is usually distributed and `backend/` is usually server-side only. In a generic repo, infer this from paths, manifests, build config, and docs; record evidence and confidence.

In license-audit mode, include scope-adjacent vendored/native assets when they can enter distributed artifacts even if they are not package-manager dependencies. Check `vendor/`, `third_party/`, native project files, linker flags, bundled media/sample assets, plugin configs, and generated resource references. Do not perform a full source-quality review of those directories unless the license/provenance question requires it.

## Previously Accepted License Signals

These license strings were previously accepted in the user's commercial-service context. Treat exact matches as `accepted-signal`, not unconditional approval. Still verify distribution context, notices, source/modification obligations, dual-license selection, and remediation evidence.

This list is an internal heuristic, not policy of record. If the repository or user supplies organization-specific license policy, use that policy as the authority and cite the accepted-signal list only as supporting evidence.

- `(AFL-2.1 OR BSD-3-Clause) License`
- `(Apache-2.0 AND MIT) License`
- `(BSD-3-Clause OR GPL-2.0) License`
- `(MIT AND BSD-3-Clause) License`
- `(MIT AND Zlib) License`
- `(MIT OR Apache-2.0) License`
- `(MIT OR CC0-1.0) License`
- `(MIT OR GPL-3.0) License`
- `0BSD License`
- `Apache-2.0 License`
- `BSD License`
- `BSD-2-Clause License`
- `BSD-3-Clause License`
- `CC-BY-3.0 License`
- `CC-BY-4.0 License`
- `CC0-1.0 License`
- `ISC License`
- `LGPL-3.0-only License`
- `MIT AND BSD-3-Clause License`
- `MIT License`
- `MPL-2.0 License`
- `MPLv2 License`
- `Public Domain License`
- `Python-2.0 License`
- `Unlicence License`
- `Unlicense License`
- `WAGMIT License`
- `WTFPL License`
- `Zlib License`

If a license is not on this list, do not automatically fail it. Mark it `unknown-to-this-policy` and investigate terms, provenance, and use context.

## Copyleft and Share-Alike Families

GPL/LGPL/MPL and similar licenses can be acceptable when used in a license-compliant way. Evaluate:

- Whether the code is distributed to customers/users.
- Whether the component is server-side only.
- Whether AGPL/network-use obligations apply.
- Whether the required source, modifications, notices, and attribution can be provided.
- Whether dual licensing allows selecting a permissive option.
- Whether a client-side use can be moved server-side if needed.

Flag a high-risk issue when obligations cannot be met, use context is unknown, or evidence is missing.

## Remediation Evidence

When a potentially problematic dependency appears, look for evidence that the project already made it acceptable:

- `overrides`, `resolutions`, `pnpm.overrides`, dependency aliasing.
- `patch-package`, `patches/`, forked dependencies, vendored patch notes.
- Transitive dependencies removed or replaced.
- Server-side isolation of problematic functionality.
- Client-side removal or relocation of implementation to backend.
- License notices, source disclosure bundles, attribution files.

Use statuses:

- `accepted-signal`: license string is on the prior accepted list; no obvious conflict found.
- `accepted-with-remediation-evidence`: risk exists but evidence shows the project patched, isolated, replaced, or complied.
- `needs-confirmation`: risk or unknown remains; more evidence/legal review needed.
- `blocker`: no/unclear license, commercial restriction, field-of-use restriction, or incompatible use with no viable evidence.

## Output Matrix

Include a license/distribution matrix when dependencies are in scope:

| Component | Distribution context | License signal | Evidence | Status | Confidence |
|---|---|---|---|---|---|
| package A | client-distributed | MIT License | `package-lock.json`, package metadata | accepted-signal | high |
| package B | server-side-only | GPL-3.0 | backend manifest only | needs-confirmation | medium |
| package C | client-distributed | no license | package metadata missing | blocker | high |

Prioritize unknown/no-license and commercial-use restrictions above ordinary copyleft notices.
