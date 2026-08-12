---
title: "Adopt Tailscale for Remote Access With a VPS Exit Node"
date: 2026-08-12
agent_model: "Claude Opus 5"
status: "accepted"
---

# ADR 0067: Adopt Tailscale for Remote Access With a VPS Exit Node

## Context

Remote access ran on WireGuard with two hand-maintained VPN profiles. Two needs drove a
reassessment:

1. macOS Screen Sharing from the laptop to the home desktop, from inside and outside the home
   network.
2. Internet egress from a stable, publicly routable IPv4 address, so that address can be
   registered in third-party allowlists.

WireGuard covered neither well. Every peer pair needs explicit configuration, and the egress
address belongs to the VPN provider rather than to us.

## Decision

Adopt Tailscale, and stand up a Linux VPS as a tagged exit node.

### Client distribution

Install the macOS **Standalone** client through Homebrew (`cask "tailscale-app"` in
`Brewfile`), not the App Store build and not a CLI-only install. The cask resolves to the
vendor's own package server and self-updates. CLI integration is enabled from client settings,
which installs a launcher at `/usr/local/bin/tailscale` — chosen over a shell alias
specifically so no dotfile change is required.

### Exit node host: ConoHa VPS

Compared against Akamai Cloud (Linode), さくらのVPS, KAGOYA CLOUD VPS and Xserver VPS. The
decisive factors, in order:

- **Documented fixed IPv4.** ConoHa states 「固定のIPアドレスなので変更はできません」. Among the
  providers examined it was the only one that says so in as many words; さくら only documents
  that no mechanism exists to change it, and KAGOYA does not document the standard IP's
  behavior at all.
- **Unmetered transfer.** ConoHa charges nothing for data transfer. Linode's cheapest tier caps
  at 1 TB/month with per-GB overage, which adds a monitoring obligation for a host whose whole
  job is to carry traffic.
- **Domestic billing.** JPY, tax-inclusive pricing and a domestic invoice, which matters
  because the account may later need to move to company ownership.

Rejected: Linode, whose reserved IP is the only true AWS-Elastic-IP equivalent found, because
that property was not required and it carries the transfer cap. KAGOYA, initially preferred on
corporate-billing documentation, was dropped once fixed IP became a hard requirement.

### Exit node identity: tagged, not user-owned

The node joins with `--advertise-tags=tag:exit-node`, backed by a `tagOwners` entry in the
tailnet policy file granting `autogroup:admin`.

Tagged devices have key expiry disabled automatically. A user-owned device expires on the
tailnet default and the exit node would silently drop off months later. Tagging also detaches
the host from an individual account's lifecycle, so a later move to a team tailnet is a
re-authentication rather than a rebuild.

`autogroup:admin` rather than a named account, for the same reason: naming one person would
reintroduce the coupling the tag exists to remove.

### Access model: tailnet-only SSH

Administrative access to the VPS is over the tailnet exclusively, enforced in two independent
layers:

- ConoHa security group: `default` only. No group permitting inbound from the internet.
- ufw: `allow in on tailscale0` and `41641/udp`, with no public 22 rule.

Emergency access is the provider's web console, which attaches to a getty and is therefore
unaffected by sshd configuration. **The root password stays the emergency credential** and must
remain retrievable from 1Password.

SSH password authentication is disabled through an explicit
`/etc/ssh/sshd_config.d/10-hardening.conf`, with `PermitRootLogin prohibit-password`. The image
already disabled it via a cloud-init drop-in, but the base `sshd_config` still carries
`PasswordAuthentication yes`; a regenerated cloud-init drop-in would silently restore it. The
`10-` prefix sorts ahead of cloud-init's `50-` and sshd takes the first value it obtains.

Temporarily attaching the vendor's SSH security group to reach a freshly rebuilt host is a
**sanctioned procedure**, not an exception — a rebuilt host has no Tailscale state, so the
tailnet route does not exist yet. The requirement is that tailnet access is confirmed before
the public route is closed again.

### Exit node is opt-in

The exit node is not selected by default. Normal traffic goes direct; the exit node is chosen
manually when an allowlisted egress address is needed. Hourly billing was chosen over a
discounted long-term ticket while account ownership remains unsettled.

### WireGuard runs in parallel

WireGuard is retained until the external integrations that depend on it move. It is scheduled
for retirement, not retired. Administrative access must therefore never be pinned to the
WireGuard egress address — doing so would lock us out the moment WireGuard is switched off,
which is a planned event.

## Consequences

Verified during implementation:

- The **public IPv4 survives both a reboot and a full rebuild** (OS reinstall), along with the
  MAC address, gateway, DNS servers, reverse DNS record, security group assignment and instance
  UUID. The address is safe to register in an allowlist.
- The **tailnet IP does not survive re-registration**. Removing the node and rejoining assigns a
  new `100.x` address. The stable identifier is the public IPv4 and the MagicDNS name, never the
  tailnet IP.
- All host configuration is wiped by a rebuild, so provisioning must be reproducible. See
  `scripts/provision-tailscale-exit-node`.
- Exit node throughput cost is roughly 15% over a direct path in our measurement. The VPS
  interface cap was not the limiting factor.
- Peer-to-peer traffic is not hairpinned through the exit node even while it is selected; the
  more-specific peer route wins.

Accepted costs:

- A tailnet created against a custom domain is treated as business use and enrolled in a paid
  trial. The free Personal plan does not apply to such a tailnet.
- Using an exit node blocks access to the local LAN by default. `--exit-node-allow-lan-access`
  exists but is deliberately left off, because enabling it means trusting whatever network the
  laptop is attached to — which contradicts the reason for using an exit node on untrusted
  Wi-Fi.

## Notes

Operating procedure lives in [../tailscale-remote-access.md](../tailscale-remote-access.md).
This ADR records why the shape was chosen; the runbook records how to reproduce it.
