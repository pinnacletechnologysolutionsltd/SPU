# Engineering Contract: T1r SRAM Reload After Power-Off

**Date:** 2026-10-02  
**Contract ID:** `GPU-T1R-POWER-CYCLE-SRAM-RELOAD-2026-10-02`  
**Status:** COMPLETE — one SRAM load PASS; attempt consumed; UART NOT RUN  
**Owner:** John Curley  
**Spec Author / Implementer / Auditor:** Codex

## 0. Authorization and scope

Record the owner's instruction: "No, it was turned off. So we're ready to flash the new bitstream". Treat this as authorization for one SRAM load of the frozen T1r Q1 artifact, using the prior programming method and 120-second bound. The board power-off invalidated the historical volatile load; halt the host-context UART contract before sender launch.

Load volatile FPGA SRAM only. Preserve the prior attempts and their outcomes. Stop after this programming outcome. UART transmission and operator observation require a later authorization with observation arranged before sender launch. D4 P1b remains deferred.

## 1. Frozen artifact and budget

| Item | Frozen value |
|---|---|
| Bitstream | `build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit` |
| SHA-256 | `5df8ac43e5e6c10dc8a8a6b6a369ee2c44b7e73df9e11149f2b30e9f044523d7` |
| Route evidence | `build/gpu/t1r_palette_pair_20261001/build_seed1/run_01/` |
| Programmer | DirtyJTAG `1209:c0ca`, serial `CB81353DCE678119`, 1 MHz |
| FPGA identity | exactly one Xilinx `xc7a100`, IDCODE `0x03631093`, IR length 6 |
| SRAM attempts / per-attempt timeout / cumulative budget | 1 / 120 seconds / 120 seconds |
| Preflight evidence | `build/gpu/t1r_palette_pair_20261002/power_cycle_reload_01/` |
| Programming evidence | `build/gpu/t1r_palette_pair_20261002/power_cycle_reload_01/program_01/` |

Launching the programming command consumes its slot for every outcome. No retry, rebuild, bitstream substitution, persistent configuration flash write, USB reset/reconnect, wiring change, or limit increase is included.

## 2. Preflight before programming

Create the preflight directory only if absent. Preserve full output and command statuses in `preflight_02.txt`. Run the corrected helper once from the approved host execution context:

```bash
python3 build/gpu/t1r_palette_pair_20261002/power_cycle_reload_01/preflight.py
```

The evidence helper executes these exact checks, stopping on failure:

```bash
sha256sum build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit
git rev-parse HEAD
git status --short
openFPGALoader -V
timeout 20s openFPGALoader --scan-usb
timeout 20s openFPGALoader -c dirtyJtag --freq 1000000 --detect -v
```

Require the exact bitstream hash; exactly one route terminal marker, `COMPLETE`, with `result.json` exit 0; the expected programmer serial; and exactly one matching FPGA. Capture mount namespace, timestamp, programmer version, source revision, and dirty status. A missing/unpowered board or any mismatch halts before loading. Detection does not authorize programming on its own.

The prior functional/repository/Padé gates remain historical evidence under `contract_gpu_t1r_hardware_scaled_visibility_2026-10-01.md`; this contract changes no RTL or sender. Do not infer current SRAM contents from those gates.

The first preflight halted before USB scan or JTAG detection because this installed loader rejects `--version`. Preserve `preflight.txt`, `preflight_01_failed.sha256`, and the original `preflight_01.py`. The minimal correction uses the documented `-V` option and a separate `preflight_02.txt`; no programming slot was consumed. Halt on any failure of the corrected preflight.

Corrected preflight PASS: host mount namespace `4026531832`, `openFPGALoader v1.1.0`, one expected DirtyJTAG adapter, and one matching XC7A100T with IR length 6. Frozen bitstream hash and route evidence matched. `preflight_02.txt` SHA-256: `8b3893e9691aa75b77d994e9646d506d1c29e310bf5fba8c1087a8a7cab344df`.

## 3. One SRAM load after preflight PASS

Launch once from the same approved host context:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1r_palette_pair_20261002/power_cycle_reload_01/program_01 \
  --timeout 120 --unit spu-t1r-power-cycle-reload-20261002-01 --notify-desktop \
  -- openFPGALoader -c dirtyJtag --freq 1000000 \
  build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit
```

Record the reported systemd unit and evidence directory, then end the turn without polling. The detached worker preserves stdout, stderr, command status, provenance, and one terminal marker; it attempts a desktop notification.

## 4. Later interpretation and halt rules

Interpret the result only in a later invocation, after exactly one of `COMPLETE`, `FAILED`, or `TIMEOUT` exists. SRAM PASS requires `COMPLETE`, exit 0, and programmer output confirming `Load SRAM` at 100%, `isc_done 1`, `init 1`, and `done 1`. Record stdout/stderr hashes and cite the exact artifact. No marker means unavailable; timeout is an infrastructure outcome. Any other result stops the contract with the attempt consumed.

Update `docs/hardware_evidence.md` and this contract only from durable programming evidence. No UART bytes are sent under this contract. A successful SRAM load establishes programming of this artifact; FPGA packet acceptance and scaled visibility remain unproven.

## 5. Programming closeout

The single detached programming command completed in 31 seconds, with exactly one terminal marker, `COMPLETE`, and `result.json` exit code 0. Unit: `spu-t1r-power-cycle-reload-20261002-01`. The programmer reached `Load SRAM: 100.00%` and reported `isc_done 1`, `init 1`, and `done 1`; stderr is empty. SRAM programming of the exact §1 bitstream is PASS.

Evidence directory: `build/gpu/t1r_palette_pair_20261002/power_cycle_reload_01/program_01/`. `stdout.log` SHA-256: `da4130eb31e500564a5b017544b128b144754cbc9fef33ce1238c3da42996605`. `stderr.log` SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Desktop notification recorded `DELIVERED`; this is not programming evidence.

The attempt is consumed. No UART transmission or scaled-visibility observation occurred. The new load remains volatile; any subsequent power-off or configuration invalidation requires another load. A later UART contract must obtain power/SRAM continuity confirmation and operator readiness before its sender launches. Evidence ledger: `docs/hardware_evidence.md` §3.30.

After closeout, the operator reported: "Sync is visible but no image." This is an operator observation of the pre-transmission display. The new load has received no scene sequence; A/B/C/return-A visibility remains untested. SRAM PASS is unchanged, and this report does not authorize a sender launch.
