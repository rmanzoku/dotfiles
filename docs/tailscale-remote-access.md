---
title: "Tailscale Remote Access and VPS Exit Node"
updated_at: 2026-08-12
---

# Tailscale Remote Access and VPS Exit Node

Reproducible procedure for the remote-access setup: Tailscale across personal machines, plus a
Linux VPS acting as a tagged exit node with a stable public IPv4.

Background and rationale are in
[adr/0067-adopt-tailscale-with-vps-exit-node.md](adr/0067-adopt-tailscale-with-vps-exit-node.md).

No addresses, account identifiers or tailnet names appear here. Substitute your own where
placeholders appear.

## Scope

| Component | Role |
|---|---|
| macOS clients | Tailscale Standalone client, installed via `Brewfile` |
| Linux VPS | Tagged exit node, stable public IPv4, tailnet-only SSH |
| Tailnet policy | `tagOwners` entry authorizing the exit-node tag |

## 1. macOS Clients

`Brewfile` carries `cask "tailscale-app"`, so the client installs with the rest of the
toolchain.

```bash
brew install --cask tailscale-app
```

Then, on each machine:

1. Approve the system extension and the VPN configuration profile when macOS prompts.
   Until approved, `systemextensionsctl list` reports `[activated waiting for user]`.
2. Sign in to the tailnet.
3. Enable CLI integration from client settings. This installs `/usr/local/bin/tailscale`.
   Preferred over a shell alias because it requires no dotfile change.

For Screen Sharing to a Mac, enable it on the target under
System Settings → General → Sharing → Screen Sharing, granting access to the intended user
only rather than all users. Connect by MagicDNS FQDN:

```bash
open vnc://<host>.<tailnet>.ts.net
```

## 2. Tailnet Policy

Before the exit node can advertise a tag, the tailnet policy file needs a `tagOwners` entry.
Add it in the admin console's JSON editor:

```json
"tagOwners": {"tag:exit-node": ["autogroup:admin"]},
```

Use `autogroup:admin` rather than a named account so the tag is not bound to one person.

## 3. Exit Node Provisioning

Create the instance with a Linux image the script supports (Ubuntu LTS), a registered SSH key,
and a root password stored in 1Password. **Avoid symbol-heavy root passwords** — the provider's
web console may use a different keyboard layout, and symbols can arrive as different
characters, producing a login failure that looks like a wrong password.

Reach the host, run the provisioning script, then join the tailnet:

```bash
scp scripts/provision-tailscale-exit-node root@<host>:/root/
```

```bash
ssh root@<host> 'chmod 755 /root/provision-tailscale-exit-node && /root/provision-tailscale-exit-node'
```

```bash
ssh root@<host> 'tailscale up --advertise-exit-node --advertise-tags=tag:exit-node'
```

`tailscale up` prints an authentication URL. Open it and approve. Because the node is tagged,
key expiry is disabled automatically.

Finally, approve the route in the admin console:
Machines → filter `property:exit-node` → Edit route settings → **Use as exit node**.

## 4. Closing Public Access

Reaching a freshly built host requires a temporary inbound-SSH security group. This is a normal
part of the procedure. Close it only **after** confirming tailnet SSH works:

```bash
ssh root@<tailnet-ip> 'echo ok'
```

```bash
ssh root@<tailnet-ip> 'ufw --force delete allow OpenSSH'
```

Then detach the inbound-SSH security group in the provider console, leaving only the default
group. Verify both directions:

```bash
nc -z -w 10 -v <public-ip> 22
```

```bash
ssh root@<tailnet-ip> 'echo ok'
```

The first must fail, the second must succeed.

Enable the provider's deletion lock last. It protects the instance — and therefore the IPv4
address registered in any allowlist — from accidental deletion.

## 5. Verification

From a client:

```bash
tailscale status
```

```bash
tailscale ping <exit-node-name>
```

A `via <public-ip>:41641` response means a direct path. A persistent `via DERP` result is worth
investigating rather than accepting.

With the exit node selected, confirm egress and that ordinary traffic still works:

```bash
tailscale set --exit-node=<exit-node-name>
curl -s https://api.ipify.org
```

Clear it again with an empty value:

```bash
tailscale set --exit-node=
```

Measure throughput **both with and without** the exit node. A single figure through the exit
node says nothing without the baseline; in our case the home link, not the exit node, was the
limiting factor.

## 6. Rebuild Procedure

A rebuild wipes all host configuration. The public IPv4, MAC, reverse DNS, security group
assignment and name tag are preserved; nothing inside the OS is.

1. Stop the instance. The rebuild control is disabled while it runs.
2. Rebuild with the same OS and the registered SSH key. Set a fresh root password.
3. Attach the temporary inbound-SSH security group.
4. **Delete the stale node entry in the Tailscale admin console before rejoining.** Otherwise
   the rebuilt host registers under a suffixed name.
5. Run the provisioning script, rejoin with the tag, approve the exit node.
6. Close public access again, per section 4.

Expect a **new tailnet IP**. Only the public IPv4 is stable across this.

## Troubleshooting

**Host unreachable on every port, including ICMP, right after creation.**
The provider's default security group does not permit inbound from the internet. A blank
IP/CIDR column in the rule list means "same security group", not "anywhere". Attach an
inbound-SSH group. Note the fingerprint: a security group **drops** (timeout), while ufw's
default `reject` policy **refuses** (immediate). The difference tells you which layer is
blocking.

**Provisioning fails at the install step with a dpkg lock error.**
`unattended-upgrades` runs at first boot and holds `/var/lib/dpkg/lock-frontend`. The
provisioning script waits for the lock. If you install by hand, wait for it too.

**Exit node looks healthy but clients get no traffic.**
ufw's `DEFAULT_FORWARD_POLICY` defaults to `DROP`, which breaks forwarding silently while
`tailscale status` and the admin console both look correct. The provisioning script sets it to
`ACCEPT`; confirm with `ufw status verbose`, which should report `allow (routed)`.

**`tailscale version` hangs while the system extension is unapproved.**
`tailscale status` still answers in the same state. Do not conclude the CLI is broken from a
hung `version` call alone.

**Tailscale stops when another VPN reconnects on macOS.**
Observed once when reconnecting a WireGuard profile: `tailscale status` reported
`Tailscale is stopped.`. `tailscale up` restores it, after which both VPNs run simultaneously.
Since public SSH to the exit node is closed, a stopped Tailscale on the client leaves the
provider's web console as the only route in.

**Local LAN devices unreachable while using the exit node.**
Expected. All traffic, including LAN-destined traffic, goes to the exit node.
`--exit-node-allow-lan-access=true` changes this, at the cost of trusting the attached network.
Peer-to-peer tailnet traffic is unaffected either way — it takes the more-specific peer route.

## Operational Notes

- The stable identifiers are the **public IPv4** and the **MagicDNS name**. The tailnet `100.x`
  address changes whenever a node is removed and rejoined; never hard-code it.
- Never pin administrative access to another VPN's egress address if that VPN is scheduled for
  retirement.
- A tailnet created against a custom domain is business use and is enrolled in a paid trial;
  the free Personal plan does not apply.
