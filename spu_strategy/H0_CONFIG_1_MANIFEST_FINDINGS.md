# H0-CONFIG-1 — SET-N / SET-R manifest reconstruction (findings)

**Disposition: REVISE.** Complete ordered write sequences for two **candidate** manifests were reconstructed from source and preserved evidence, but neither is qualified or ratified, and several properties needed by the future H0 controller are **not provided by the current RTL** (§8). Configuration ratification and implementation: **HOLD**. Read-only investigation: no RTL, SPI, algorithm, VM or ISA change, no RTL simulation, no commit to the shared checkout.
**Source identity:** isolated checkout `~/.local/gate/spu-config1-0f631e3` at `0f631e37caeabb629b81b84a782cee1d881ac0b9` (contains A31-R3). Deliverables: this file, `spu_strategy/h0_config_1/SET_N_CANDIDATE.json`, `SET_R_CANDIDATE.json` (untracked).
**Evidence classes:** *source* = RTL read; *preserved observation* = committed simulation evidence; *oracle* = host arithmetic with `software/lib/a31_field.py` (not RTL); *unverified* = not established. H0-C1-T5 synthetic configuration values were not used.

## 1. Configuration path (source)

| Stage | Behavior | Reference |
|---|---|---|
| SPI frame `0xA5` | command byte, 64-bit HEADER, 64-bit DATA, CRC8 over command‖header‖data. HEADER `[63:56]` must be `0xA5` (else only `crc_error_sticky`); `sel = hdr[50:48]`, `material = hdr[47:44]` (zero-extended to 8), `addr = hdr[43:34]`; **`hdr[55:51]` and `hdr[33:0]` are discarded**. After a valid CRC a one-cycle `rplu_cfg_wr_en` pulse carries `sel/material/addr/data`. No ready input, no backpressure, no per-write response. | `spu_spi_slave.v` (S_RECV_HDR/DATA/CRC, `rplu_cfg_*` assignment) |
| Artix-7 top | `rplu_cfg_*` is the **only** source of the core's `dec_fast_cfg_*`. The top also keeps a count, a rotate-XOR checksum, a sum checksum and the last record of all accepted `0xA5` frames, plus mirror registers for Padé num/den index 0, BTU row 1 and kappa, exposed in `southbridge_telemetry`. | `spu_a7_top.v` (cfg mirror and checksum functions, `southbridge_telemetry`, instance of core) |
| Core decode | `sel` 3 bits. `1` Padé numerator, `2` denominator, `3` BTU row, `6` kappa, `7` torus control, `4` SOM weight (inert unless `ENABLE_CORE_SOM`), `5` audio (only under `DEBUG_VOICE`), `0` unused in H0. `material` is unused by the H0 core. | `spu13_core.v` (config decode, torus/kappa blocks) |
| Padé coefficients | index `addr[2:0]` (valid 0–4; 5–7 silently ignored), half `addr[3]`, `addr[9:4]` ignored. **LOW (`addr[3]=0`) writes only a core-side staging array** (`rplu2_pade_{num,den}_c{0,1}[idx]`). **HIGH writes the engine arrays** `{staged c0,c1 ; data c2,c3}` through `coeff_we`. | `spu13_core.v`, `rplu_thimble_pade.v` |
| BTU rows | row `addr[5:0]`, half `addr[6]`, `addr[9:7]` ignored. **No staging**: LOW writes lanes c0,c1 and HIGH writes c2,c3 of the BRAM row immediately and independently. 64 rows writable; the SOM can select only rows 0–6. | `spu13_btu_core_top.v`, `spu_bram_32x64_array.v` |
| Kappa | `quadray_target_kappa <= data[31:0]`, `quadray_target_valid <= 1`; reset clears both. Feeds only quadray coherence/dissociation, not the result, completion or refusal. | `spu13_core.v` |
| Data layout | LOW `data[31:0]=c0` (rational), `data[63:32]=c1` (√3); HIGH `data[31:0]=c2` (√5), `data[63:32]=c3` (√15). | decode above |

## 2. Staged versus committed (source)

| Write | Acceptance | Staged state | Mathematical-state commitment |
|---|---|---|---|
| Padé LOW | frame CRC-valid, idx ≤ 4 | core staging array for that (num/den, idx) | **none** (engine arrays unchanged) |
| Padé HIGH | same | none | **commits the pair** into the engine array, using the staging array's *current* c0,c1, which are whatever the latest LOW write for that (num/den, idx) left there, or the initial value if none (a HIGH alone commits a stale low half) |
| BTU LOW / HIGH | CRC-valid | none | each half **commits immediately**; a row is complete only after both halves, and between them the row is mixed new/old |
| Kappa | CRC-valid | none | immediate |
| Torus (`sel 7`) | CRC-valid | none | immediate; can enable an autonomous Artery emission (`torus_emit_enable`) |

So a LOW Padé write must not advance committed-coefficient progress; only the HIGH write does. There is no readback of the engine arrays, the staging arrays or the BTU rows.

## 3. Candidate SET-N (reconstructed)

Evidence: A31-R3 probe `setup`, `a31r3_core_probe.v` lines 59–66, and preserved results `hardware/tests/spu13/a31_r3/expected/probe_ref.txt`.

* **Writes (evidenced, 18):** numerator coefficient 0: LOW `{c1=0,c0=2}`, HIGH `{c3=0,c2=0}`; denominator coefficient 0: LOW `{0,1}`, HIGH `0`; BTU rows 0–6: LOW `{c1=0,c0=1}`, HIGH `0`. The probe also wrote kappa = 3 (optional, §6). Order observed: numerator, denominator, rows, kappa; the only ordering constraint in the source is LOW before HIGH for the same (selector, index), with no other LOW to that pair in between.
* **Not written by the evidence (16):** coefficients 1–4 of the numerator and denominator rely on the arrays' initial values (zero). They are listed in the manifest as `proposed_completion_unexercised` explicit zero writes, because RTL comments state that Yosys does not synthesise `initial` blocks containing `for` loops, so hardware power-up state of the coefficient arrays and BRAM is **not established by the source**. Mathematically neutral, never exercised.
* **Precondition (not a manifest entry):** `QLDI` lane 3 = (2,0,0,0), then `0x2A` with source lane 3 and result label lane 4.
* **Expected chain:** features → SOM winner node 1 (preserved: NUM-SOM-1/2 `ALIAS_P`/A=2 cases) → BTU row 1 → x = (1,0,0,0) → N(x) = 2, D(x) = 1 → result (2,0,0,0).
* **Expected core behavior (preserved A31-R3 observation):** one `inst_done`, one `rplu2_result_valid`, one `qr_commit_valid`, lane 4, `qr_commit_A = 2`, no refusal, no QR write.
* **Oracle:** `pade_eval` gives (2,0,0,0). The observed value is independent of the row limbs and of coefficients 1–4 (see §7a).

## 4. Candidate SET-R (reconstructed)

Identical to SET-N except denominator coefficient 0: LOW `{c1=0, c0=0x2CEE24B2}`, HIGH `{c3=1, c2=0}` (manifest entries 10 and 11). Same preconditions, same SOM winner and BTU row.

* **Why it is a zero divisor (oracle):** 0x2CEE24B2² ≡ 15 (mod 2³¹−1), so the denominator `x + √15` has norm 0; `a31_tower_inv` returns `flags_v`, `pade_eval` returns refusal.
* **Expected core behavior (preserved A31-R3 observation, R1/R0 transactions):** `pade_done` with `flags_v`, `thimble_refused`, exactly one `rplu2_arith_refused` pulse aligned with `inst_done`, no `rplu2_result_valid`, no `qr_commit_valid`, no QR write, commit telemetry unchanged (historical). Also observed as the first transaction after reset.
* **Scope:** this is the *characterized* zero-norm refusal only. The inverter's norm check is not claimed to catch every zero divisor of A₃₁; `rns_error`, ECC and coherence events are separate and unclassified (H0-C1 D7).

## 5. Manifest representation

Each JSON entry: `index, selector(_name), material, address (+ decode), header_word64, subfield_layout, value64 and limbs, write_class (STAGED | COMMITTED_PAIR | COMMITTED_HALF), destination, pair_with, status, note`. Each manifest has 34 ordered entries (18 evidenced, 16 proposed completion), `entries_sha256` (SET-N `6483d9adc453e35e…`, SET-R `9936607a53517103…`, computed over the canonical entry list) and an optional kappa entry kept **outside** the identity. Entries 10 and 11 are the only difference.

Predicted existing Artix-top telemetry after exactly these 34 frames since reset (bit model of the top's checksum functions; host arithmetic, not RTL-observed): SET-N count 34, rotate-XOR checksum `0x10FF8B92`, sum checksum `0xEA480992`; SET-R count 34, `0x4929FC80`, `0x17362E44`. These are aggregates over all `0xA5` frames since reset, so they are meaningful only if no other frame was sent.

The future controller must compare the **ordered entries** (selector, material, address, full value) against a stored manifest in hardware, not a host-supplied hash. Entries are `(selector, material, address, subfield, value)` as in the JSON; progress must advance on the HIGH write of a Padé pair (and on each BTU half), never on a Padé LOW write.

## 6. Allowlist classification (candidate)

| Target | Class | Reason |
|---|---|---|
| `sel 1` idx 0–4, LOW and HIGH | **required** | numerator coefficients |
| `sel 2` idx 0–4, LOW and HIGH | **required** | denominator coefficients |
| `sel 3` rows 0–6, LOW and HIGH | **required** | rows reachable by the 7 SOM nodes |
| `sel 6` kappa | **unresolved** | only coherence/dissociation telemetry; bench copied kappa = 3; its necessity for H0 is undecided |
| `sel 1/2` idx 5–7 | prohibited | silently ignored by the core; reject instead |
| `sel 3` rows 7–63 | prohibited / unresolved | writable but unreachable from the SOM; unnecessary mutation surface |
| `sel 7` torus | **prohibited** | enables autonomous Artery emission, not guarded by `ENABLE_TORUS` |
| `sel 4` SOM weight | prohibited | inert in the H0 pipeline configuration (training port tied off), live if `ENABLE_CORE_SOM` |
| `sel 0`, `sel 5` | prohibited | no H0 function |
| nonzero `material`; address bits above the used field (`addr[9:4]` for Padé, `addr[9:7]` for BTU, all of `addr` for kappa/torus) | prohibited | ignored by the decoder, so non-canonical frames alias valid writes; the controller must reject them |

## 7. Separation of claims and gaps

| Item | Exact math | Bit-accurate RTL model | Preserved RTL observation | Unverified |
|---|---|---|---|---|
| SET-N result (2,0,0,0) | oracle | — | A31-R3 `S1` | with non-trivial row limbs and coefficients 1–4 |
| SET-R refusal | oracle `flags_v` | — | A31-R3 `R1`/`R0` | other zero divisors |
| SOM winner node 1 | — | NUM-SOM models | NUM-SOM-1/2 (A=2 → node 1) | with the exact H0 image |
| Checksums/counts | — | host bit model of top functions | — | on the board |
| Hardware power-up of arrays/BRAM | — | — | simulation `initial` only | on FPGA |

**(a) Discrimination gap.** Both evidenced manifests use only constant polynomial terms (numerator 2, denominator 1 or the witness), so the observed result does not depend on the BTU row content or coefficients 1–4. A successful or refused completion therefore does **not** prove that rows and higher coefficients were committed. A discriminating, **unexercised** oracle vector (not part of the manifests and not evidence): numerator `[2, 1]`, denominator `[1]`, row-1 x = (3,0,0,0) gives (5,0,0,0); with x = (0,1,0,0) it gives (2,1,0,0). Choosing a vector is a ratification decision.
**(b) Initial state.** `initial` blocks seed num/den coefficient 0 = 1, all else 0 and BRAM = 0; none of the three arrays has a reset branch, so previous configuration, **including staged LOW halves**, survives a reset. A reset therefore does not discard staged halves and does not return the Padé/BTU state to defaults.
**(c) Stale low half.** A HIGH write commits whichever low half is staged; nothing detects a missing or earlier LOW.
**(d) Configuration while busy.** The core accepts configuration writes at any time, including during a Padé evaluation (no busy gating); the engine and BRAM are live.
**(e) Dropped header bits.** `hdr[55:51]` and `hdr[33:0]` never leave the SPI slave, so a core-boundary controller cannot verify them; strict verification needs the SPI slave or a pre-slave tap.
**(f) No acknowledgement or readback.** There is no per-write response, no staged/committed indication, no readback of the staging arrays, engine arrays or BTU rows. The top's count/checksum/last-record and the mirrors for num/den index 0, row 1 and kappa are partial aggregate evidence only.
**(g) Kappa.** Written as 3 by the A31-R3 bench (copied from the historical Artix consume bench, which also expects 149 flash-loaded records); no mathematical role in SET-N/SET-R.

## 8. Lifecycle implications and hardware requirements for the controller

* Progress counters must advance only on a HIGH Padé write (when the low half staged by that same pair is the one committed) and per BTU half; a LOW write is STAGED, not COMMITTED.
* A new LOW to the same (selector, index) before its HIGH, a rejected HIGH, or a reset must discard the staged half; the current RTL cannot discard it (§7b), so reset recovery either rewrites every entry (the complete 34-entry manifests do) or needs a hardware change.
* Configuration must be rejected while an instruction is in flight (§7d).
* The controller needs per-write attributable acknowledgement carrying the entry index and class, which the current SPI path does not provide.
* A manifest-identity check must cover the complete ordered entry stream and must reject any non-allowlisted frame without staging it.

## 9. Open items

Ratify (or change) the SET-N vector so that it discriminates rows and higher coefficients; decide kappa; decide whether hardware power-up state needs a fresh evidence run; define acknowledgement and staging-discard hardware; assess whether header bits must be checked before the SPI slave; physical qualification. None is established here, and **neither manifest is labelled qualified**.
