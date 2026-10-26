# Vivado environment readiness before C1 elaboration

Date: 2026-10-19. Status: read-only readiness check; no installation or tool run.
The owner selected [C1 as the prospective source identity](VIVADO_SOURCE_RECONCILIATION_2026-10-19.md).
Historical H0 remains separate evidence. Source selection authorizes no routing.

Owner direction: preserve the established CachyOS development installation.
Prefer native supported Ubuntu on a separate SSD or machine for vendor tools;
do not replace CachyOS to run Vivado. Worker selection/provisioning and licence
setup remain separate decisions. No purchase or disk/OS change is authorized.

## Owner decision — installation deferred

The owner plans to install Ubuntu personally on the existing separate NTFS
SSD, then revisit Vivado installation. Read-only inspection identified an
Intel SSDSC2CT180A4, 180,045,766,656 bytes (180 GB), serial
`<disk-serial-redacted>`, currently `/dev/sda`; this corrects the earlier 256 GB
description. The owner reports only Steam and games on it. The current
CachyOS/SPU disk is the other Intel SSD, serial `<disk-serial-redacted>`, currently
`/dev/sdb`. Device names are observations, not stable installation identities.

For now, record the decision and leave the environment unchanged. No disk
formatting, partition changes, bootloader changes, installation preparation,
downloads or tool execution are requested. Vivado installation and C1 execution
remain future separately authorized work. No disk contents were independently
audited or backed up, and no installation-space sufficiency is established.

## Observed local environment

| Item | Observed state |
|---|---|
| Host | CachyOS, Arch-derived rolling Linux, x86-64 |
| Vivado in PATH | Absent |
| Docker/Podman in PATH | Neither found |
| Root filesystem free | Approximately 68 GiB at inspection |
| Physical RAM | Approximately 15 GiB total, 10 GiB available at inspection |
| Swap | Approximately 15 GiB; not equivalent to physical RAM |
| /tmp | Approximately 7.8 GiB tmpfs; not an installer staging disk |

Inspected `/etc/os-release`, architecture, disk/memory and executable paths.
These are point-in-time observations, not reservations or installation success.
No licence file content or credentials were accessed.

## Supported-platform boundary

AMD's [installer/OS support matrix](https://www.amd.com/en/support/adaptive-socs-and-fpgas/installer-info-general.html)
lists Ubuntu 24.04.3 LTS for Vivado 2026.1; it does not list CachyOS/Arch.
Checked 2026-10-19. The linked version-specific UG973 operating-system page
could not be retrieved during this check, so record that limitation rather
than claiming a separate release-note verification.
Before installation, pin the exact Vivado build and reconfirm its released
OS/package requirements. A successful generic Linux launch would not itself
make this host an AMD-supported environment.

The proposed supported worker is an AMD-listed x86-64 Ubuntu 24.04.3 environment
with sufficient persistent storage and memory, provisioned separately from the
current host. Do not assume that merely adding Ubuntu userspace in a container
qualifies the kernel/platform; VM/container support needs its own verification.
No OS replacement, VM, container, service or package installation is authorized
or performed by this document.

A VM on this host would compete for its limited physical-memory headroom.
An Ubuntu container or native CachyOS installation may be useful experimental
options, but neither has established vendor-support status here. They are not
the selected reference environment. Swap is not a reason to allocate a 16 GiB
Vivado working set on the observed host.

Use the Linux web installer with only the required Vivado/7-series components
after the environment decision. Confirm actual component disk requirements
before download; 68 GiB free is not a verified installation-space guarantee.
Obtain the free annual BASIC licence through the owner-controlled AMD account;
keep licence files/credentials out of source and build evidence. The
[BASIC licensing requirement](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/licensing-faq.html)
is product eligibility, not proof that this machine has a valid licence.

## Stage the next decision as elaboration, not routing

After separately authorized environment/licence setup, verify the executable
version and device availability, then prepare an elaboration-only C1 invocation.
Use the immutable 35-file C1 packet with both required include directories,
top `spu_a7_surd_cpu_bench_top`, ENABLE_SURD_CPU=1 and the full part
`xc7a100tfgg676-1`. Preserve the 40 ns clock and source guard. Refuse any
source fallback outside the captured tree; report missing modules, macros,
initialization dependencies or unsupported constructs without editing RTL.

Stop after RTL elaboration and hierarchy/black-box inspection. Logic mapping,
optimization, placement, routing, bitstream generation and board programming
are not part of that stage. Freeze an exact tool-supported Tcl invocation,
resource limits and durable logs before authorizing it; no runnable vendor
command is supplied while the executable and environment are absent.

The earlier proposed four-thread, 16 GiB, 3,600-second implementation campaign
remains unapproved and is not the next action. Its cap exceeds the observed
physical RAM and must not be mistaken for available reserved capacity. Review
actual headroom and future worker capacity before approving either elaboration
or implementation. Routed timing and mapping-policy comparisons remain later,
separately reviewed evidence claims.
