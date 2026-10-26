# Engineering Contract: VGAFIX configuration CRC delivery diagnostic

**Date:** 2026-10-02  
**Status:** DRAFT — offline preparation PASS; owner hardware authorization pending  
**Roles:** Codex drafts, reviews and prepares; owner reviews the packet and authorizes the hardware budget.

## 1. Prepare the reviewable artifact

```bash
python3 build/gpu/vgafix_crc_delivery_20261002/preparation_01/prepare_crc.py
g++ -std=c++17 -O2 -Wall -Wextra -Werror -I /home/user/toolchains/prjxray/lib/include build/gpu/vgafix_crc_delivery_20261002/preparation_01/crc_reference.cc -o build/gpu/vgafix_crc_delivery_20261002/preparation_01/crc_reference
python3 build/gpu/vgafix_crc_delivery_20261002/preparation_01/check_fixtures.py
python3 build/gpu/vgafix_crc_delivery_20261002/preparation_01/check_hardware_guards.py
python3 build/gpu/vgafix_crc_delivery_20261002/preparation_01/check_prerequisites.py
```

Keep generated helpers, reference binary, derived image, fixtures and logs under
`build/gpu/vgafix_crc_delivery_20261002/`. Do not edit RTL, constraints, archived
inputs, original bitstreams, generated repository catalogs or previous evidence.
Do not run synthesis, repository gates, JTAG, UART or analyzer captures during preparation.
The prior repository PASS remains attached to its frozen snapshot; this offline
preparation is not a new repository closeout.

Freeze the original 3825920-byte `build/spu_a7_100t_VGAFIX.bit` SHA-256
`a80b6d0cde560f71c85dcd4a8896019ae21f9149a5eed6cf26e35b154b69e379`.
Require its 955864-word FDRI digest
`9192c831505e5d6f1629705a81dc4218fc9a2e66de429da0870793f4c66cbdde`.
Replace only the two post-initial CMD/RCRC packets with CRC-register write
packets of equal length; retain the initial RCRC. Preserve every other byte,
including header, frame ECC, payload, startup commands and NOPs. Record exact
offsets, original/replacement words and artifact hashes in `preparation_01.json`.

Use the register-aware 37-bit update with reflected polynomial `0x82f63b78`,
32 data bits followed by five address bits, all least-significant-bit first.
Include all written register words after the initial reset; exclude headers/NOPs.
Supply the accumulator to each CRC write and require the resulting accumulator
zero. Check against the frozen local Project X-Ray C++ function and known vectors.

AMD's sample sequence checks CRC after FDRI and again before DESYNC. A detected
configuration CRC mismatch aborts configuration. CRC checks test delivery,
not display logic or live SRAM readback. [UG470, configuration sequence and CRC](https://docs.amd.com/api/khub/documents/FOs3lXmlcWxBhTIFxVKyGA/content).
No deliberately invalid image may be programmed; corruption fixtures are offline only.

## 2. Halt-and-flag review

```bash
cat build/gpu/vgafix_crc_delivery_20261002/preparation_01/preparation_01.json
cat build/gpu/vgafix_crc_delivery_20261002/preparation_01/fixture_results_01.json
cat build/gpu/vgafix_crc_delivery_20261002/preparation_01/implementation_review_packet.md
```

HALT on any missing reference input, identity mismatch, packet truncation,
unexpected command sequence, frame change, extra changed byte, nonzero reference
exit, or accepted negative fixture. Freeze helper, reference and image identities
before authorization. Hardware instructions and budget below are proposals until
that review passes and the owner authorizes this new campaign.

## 3. Proposed hardware campaign

Reserve one new `hardware_01` campaign, one preflight (60 s), one SRAM load
(120 s), one detached launcher invocation (45 s), one STAT query (20 s) and one
observation (30 s). Allow two seconds of forced-termination grace for preflight
and query, and the runner's ten-second grace for the SRAM command. Maximum
cumulative tool/observation budget: 300 s, including launch and termination grace;
human readiness waits are outside that budget
and authorize no operation. Launch consumes the relevant slot, including failures
and timeouts. No retries, longer timeouts, fallback images, deliberate CRC failure,
flash operation, extra reset, UART, synthesis or wiring change.

Before preflight record owner authorization and current observer readiness,
same Wukong/J10/monitor/DirtyJTAG association, unchanged harness/settings and
whether power has remained continuous. Do not infer current readiness from older
answers. Match the original adapter serial `CB81353DCE678119`, USB `1209:c0ca`,
one XC7A100 IDCODE `0x03631093`, IR length 6, host mount namespace
`mnt:[4026531832]`, loader v1.1.0 and 1 MHz JTAG. Recheck frozen helper/image hashes.

Create `hardware_01` once after authorization, with no inherited outputs or
symlink; record `operator_preflight.json` containing `authorized_contract`
equal to this filename, `owner_authorized`, `same_wukong_j10_monitor`,
`configuration_unchanged`, `ready_for_load` all true, Boolean `power_continuous`,
the exact owner `authorization_quote` and current UTC `readiness_utc`.

Run these commands in the host namespace, sequentially, stopping on every nonzero
exit. Check the frozen manifest digest specified in §5 before using its entries.

```bash
sha256sum -c build/gpu/vgafix_crc_delivery_20261002/preparation_01/frozen_inputs.sha256
timeout --signal=TERM --kill-after=2s 60s python3 build/gpu/vgafix_crc_delivery_20261002/preparation_01/campaign.py preflight
```

Require `preflight.result.json` PASS, then recheck the same manifest and launch once:

```bash
sha256sum -c build/gpu/vgafix_crc_delivery_20261002/preparation_01/frozen_inputs.sha256
python3 build/gpu/vgafix_crc_delivery_20261002/preparation_01/campaign.py launch
```

The launch helper invokes the frozen detached runner with 120-second timeout,
unit `spu-vgafix-crc-delivery-20261002-01`, desktop notification and evidence
`build/gpu/vgafix_crc_delivery_20261002/hardware_01/program_01`. Its worker
rechecks frozen inputs before the exact SRAM command:

```bash
/opt/oss-cad-suite/bin/openFPGALoader -c dirtyJtag --freq 1000000 /home/user/Projects/hardware/SPU/build/gpu/vgafix_crc_delivery_20261002/preparation_01/spu_a7_100t_VGAFIX_CRC.bit
```

Record unit/evidence and end the launch turn; Linux owns execution.
On a later invocation require exactly one
terminal marker, COMPLETE, exit 0, 100% SRAM transfer and INIT/DONE/ISC_DONE all 1.
Only then recheck the manifest and run the single STAT query:

```bash
sha256sum -c build/gpu/vgafix_crc_delivery_20261002/preparation_01/frozen_inputs.sha256
timeout --signal=TERM --kill-after=2s 20s python3 build/gpu/vgafix_crc_delivery_20261002/preparation_01/campaign.py query
```

The query helper runs exactly `/opt/oss-cad-suite/bin/openFPGALoader -c dirtyJtag
--freq 1000000 --read-register STAT` with an 18-second process limit, inside the
20-second stage limit. Require CRC/ID/DEC errors absent and
INIT Complete/EOS/GWE/Release Done/Done all 1. HALT on any failure or unavailable
result; do not recover or replace the image.

After startup PASS require a live observer, then capture one full-display photo
and ten-second video within the single 30-second observation. VGAFIX expects
eight vertical color bars and a moving red marker. Missing evidence leaves visual
classification INCONCLUSIVE. Corrupted display leaves visual HOLD. Clean display
is a clean observation for this artifact only; a reload and checksum addition are
coupled in this single experiment, so it cannot attribute improvement to CRC.
Record transfer/startup and visual outcomes independently in the hardware ledger.
Record observer readiness, start/end UTC, power/setup continuity and any change
in `observation_01.json`. Use one 30-second foreground timer; absent original
post-load photo/video remains pending evidence for the earlier campaign.

```bash
python3 -c 'from datetime import datetime, timezone; import time; print("OBSERVATION_START", datetime.now(timezone.utc).isoformat(), flush=True); time.sleep(30); print("OBSERVATION_END", datetime.now(timezone.utc).isoformat(), flush=True)'
```

Announce the capture interval before launching this timer. The observation slot
is consumed at timer launch even if evidence is missed. Classify absence as
INCONCLUSIVE; do not repeat the interval without a newly authorized budget.

## 4. Closeout limits

No additional repository rerun is indicated for preparing this diagnostic, as
the owner has specified. Do not claim a new engineering/repository closeout,
netlist equivalence, SRAM readback, reset/pixel-clock measurement or silicon PASS
from offline checksum validation. Retain VGAFIX visual HOLD until new observations.
The old VGAFIX and recovery budgets are consumed and cannot fund this campaign.

## 5. Frozen preparation and execution guards

Before every hardware-stage invocation, run this manifest-identity check and
HALT on nonzero exit, then the §3 input checks. Never import a modified helper.

```bash
printf '%s  %s\n' '09a5ddb0b73fb5974519fe07d95eb774d34595840053f58f4531979f6abd321c' 'build/gpu/vgafix_crc_delivery_20261002/preparation_01/frozen_inputs.sha256' | sha256sum -c -
```

The frozen manifest records 21 inputs including helpers, original/candidate,
reference CRC header/tests/binary, fixture evidence, detached runner/worker and
loader wrapper/binary. The CRC header is an immutable external verification
input at `/home/user/toolchains/prjxray/lib/include/prjxray/xilinx/xc7series/crc.h`,
SHA-256 `ebc3f2c1f824829ae5f3a5223b6213d7e5a6539202b249aff3104c1ad241e726`.
Its bytes and the known-vector source are included in the review ZIP for review;
the active commands retain the declared frozen external path.

Derived image: 3825920 bytes, SHA-256
`534e88759e10aa66330fbeb10856635f93d7c5306c277de841a09587ccde49f9`.
The replacements are at absolute byte offsets 3823824 and 3824296, with CRC
values `0x0b4dc570` and `0xe3ad7ea5`. There are two CRC-register writes and one
retained initial RCRC. Every byte outside those two eight-byte packets matches
the original, and the full frame payload digest is unchanged.

Preparation evidence: 34 checksum/image checks, 30 pure startup/identity guard
checks and 19 frozen-input/authorization prerequisite checks, all PASS. The
independent C++ reference accepts the candidate and rejects the original's
missing checks, both wrong-checksum fixtures, altered frame/register data and
a checksum-erasing RCRC fixture. No malformed fixture was programmed.
Python syntax checks PASS. Hardware campaign, startup and visual observation
remain NOT RUN for the derived image. No new repository gate was run.
