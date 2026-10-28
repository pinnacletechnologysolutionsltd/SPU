# H0-CONFIG-2 — Configuration commitment, authorization and verification (design and verification plan)

**Disposition: design complete for independent review; implementation HOLD.** This is a design and verification plan only. No production RTL, SPI encoding, simulation, synthesis or hardware work was done; the existing candidate manifests, R8 documents and T5 files were not modified; nothing was staged or committed. Every claim about RTL is source-derived or taken from preserved evidence; every mathematical value below is host arithmetic, not RTL evidence. Nothing here is labelled qualified.

## 1. Source and evidence identities

| Input | Identity |
|---|---|
| Source baseline | `dev/next` `0f631e37caeabb629b81b84a782cee1d881ac0b9`; read-only isolated checkout `~/.local/gate/spu-config1-0f631e3` |
| H0-CONFIG-1 findings | `spu_strategy/H0_CONFIG_1_MANIFEST_FINDINGS.md` SHA-256 `05a64e64…8bf7dc2` (untracked) |
| Candidate manifests (unchanged) | `SET_N_CANDIDATE.json` `7b508182…da12cb` (entries `6483d9adc453e35e…`), `SET_R_CANDIDATE.json` `51c4a011…59eedb` (entries `9936607a53517103…`) |
| R8 contract / traces | `spu_strategy/H0_C1_T4_R8_CONTRACT.md` `d72eb154…9747666`, `H0_C1_T4_R8_FROZEN_TRACES.md` `3a3af1d6…6955ded` (governing; not modified) |
| H0-IMAGE-2 findings | `/tmp/spu-h0-image2/spu_strategy/H0_IMAGE_2_EXCLUSION_FINDINGS.md` `ed311c4f…a2efd`, disposition HOLD; it concerns chain/audio exclusion and states that the top still lacks an H0 transaction owner and classifier; no conflict with this design. Its repair is not a governing interface. |
| T5 scratch | `/tmp/spu-h0-t5-isolated/experiment/h0_c1_t5/` (`capability_bank.sv`, `fake_units.sv` and their benches, R7 copies). Listed but not read or relied on: preliminary implementation evidence, not an interface. |

## 2. Current limitations (from H0-CONFIG-1, restated)

The `0xA5` path gives a one-cycle pulse with no acknowledgement; Padé LOW writes a core-side staging array and HIGH commits `{staged c0,c1 ; c2,c3}` into the engine; BTU halves commit immediately; staging arrays, engine arrays and BRAM have no reset branch (staged halves survive reset); writes are accepted while an instruction is in flight; the SPI slave discards `hdr[55:51]` and `hdr[33:0]`; there is no readback; selector 7 can enable autonomous Artery emission. R8 leaves three semantics undefined that production must define: configuration while READY, configuration while an instruction is active, and a non-failed submission while a sink operation is pending.

## 3. Authorization model (controller-side, logical)

**State.** Lifecycle `CONFIG` or `READY`; progress `p` = number of manifest entries committed *in the current attempt, in order* (0…34); a controller-owned LOW stage register (one entry, valid bit, identity `(selector, idx)`, 64-bit value); a manifest-lock `{unselected, N, R}`; the R8 records (transaction, rejection, configuration-ack) and sticky fault `F` unchanged.

**Rules.**
1. **Reset** (physical only) → `CONFIG`, `p=0`, stage register cleared, manifest-lock `unselected`, pending sink work cancelled, replay cancelled, configuration-ack record NONE. Physical coefficient registers, BRAM and the core's staging arrays are **not** touched and carry **no authority**.
2. **READY only when `p = 34` and the 34th entry is COMMITTED** with every earlier entry committed in order in this attempt. Because the manifests write every coefficient position (both halves, indices 0–4, both polynomials) and every reachable BTU row (0–6), a complete attempt overwrites the whole mathematical state; no historical physical value can authorize execution.
3. **A failed submission** (R8 kinds `BAD_FRAME`, `WRONG_ORDER`, `WRONG_VALUE`, `WRONG_TARGET`, `DUPLICATE`, plus the new kinds below) records the rejection, cancels pending sink work, clears the stage register, sets `p=0`, returns to `CONFIG` and requires full replay (R8 §3, unchanged).
4. **Authorization is revoked at acceptance of the first frame of a new attempt**, not at its commit: an accepted frame while `READY` and idle moves the lifecycle to `CONFIG` immediately, so there is never a READY state over a half-rewritten configuration. (Extension; R8 leaves "configuration while READY" undefined.)
5. **Interlock:** a configuration frame while any instruction is outstanding is rejected with new kind `CONFIG_BUSY`, has no effect on configuration or on the active instruction, and does not invalidate authorization. A configuration frame while `CONFIG` and no instruction is outstanding follows rules 2–3. (Extension; R8 leaves "configuration while active" undefined.) SPI serializes `0xA5` and `0xB1` frames, so a same-edge collision cannot occur from the host.
6. **Manifest selection (D13a, open):** both frozen manifests are identical up to entry 9. The only selection mechanism compatible with "no SPI encoding change" is prefix matching: entries 0–9 are checked against both, entry 10 (denominator LOW) selects N or R, and entries 11–33 must match the selected manifest. A separate select field would need an SPI encoding change and is not proposed.
7. **Kappa** is not part of either manifest identity. Its write is rejected until the open decision (§6) is made.

## 4. Paired-write ownership: alternatives and selection

| Option | Mechanism | Assessment |
|---|---|---|
| **A — controller-owned staging with atomic LOW+HIGH replay (selected)** | The controller accepts a LOW frame, validates it against the manifest entry, and holds it in its own stage register; **nothing reaches the core**. When the matching HIGH frame is validated, the controller drives the core with the LOW write and, on the next clock, the HIGH write (a two-pulse replay it cannot interrupt), then compares the observed commit bundle with the manifest entry. | The core's staging array is overwritten with the current-attempt LOW immediately before every HIGH, so stale or earlier content can never be committed; a failed or reset attempt leaves the core untouched; no core RTL change for pairing; matches the R8 sink obligations through an adapter (§9). |
| B — generation/valid bits in the core staging arrays | Add a valid flag and attempt generation per staging entry; HIGH commits only if valid and current. | Hardware-checked pairing, but modifies the mathematical core's configuration logic and adds state and reset behavior inside the mathematical path. Not selected now. |
| C — reset-clear the staging arrays | Add reset branches. | Does not address stale LOW within an attempt or failed attempts; forces flip-flop implementation; rejected. |
| D — host discipline plus aggregate checksum | none | Count and checksum aggregate over frames and cannot prove pairing or destination; rejected. |
| E — A plus array readback | add readback ports | Strongest evidence, largest RTL change; deferred (§5, §9). |

**What option A does not by itself prove.** A valid controller-side pair does not prove the engine received the value. Closing that gap uses the commit bundle (§5) and the discriminating witness (§7).

**Assumptions to verify before implementation (unverified, source reading only).** (i) a LOW pulse at cycle *k* updates the staging array so that a HIGH pulse at cycle *k+1* reads it; (ii) the core accepts one configuration write per cycle; (iii) frames cannot arrive during the two replay cycles (requires the SCK/`clk_fast` relationship, which is unresolved; if a frame can arrive, the controller must treat it as `CONFIG_BUSY` or buffer one frame).

## 5. Commitment acknowledgement

| Event | Owner | Observable (existing or new) |
|---|---|---|
| SPI frame received | `spu_spi_slave` | existing: `rplu_cfg_wr_en` pulse after CRC; raw header bits `[55:51]`, `[33:0]` are lost |
| Request accepted | controller | accepted into the adapter (R8 PENDING); not an acknowledgement |
| Low-half staged | controller stage register | R8 configuration-ack `STAGED` (progress unchanged) |
| Mathematical state committed | core | **new evidence needed:** the commit bundle observed at the engine/BRAM write inputs matches the manifest entry |
| Configuration acknowledgement published | controller | R8 configuration-ack record `COMMITTED` (progress +1); unread/overrun/capability rules unchanged |
| Complete manifest authorized | controller | `p=34` → `READY` |

**Commit bundle (minimum new core outputs; the signals already exist as internal wires):** Padé `{we, is_den, idx[2:0], c0, c1, c2, c3}` (`rplu2_pade_coeff_*` in `spu13_core.v`) and BTU `{we, addr[5:0], pair, data[63:0]}` (`rplu2_btu_cfg_*`). A Padé HIGH is COMMITTED only when the bundle shows `we` with the expected `is_den`, `idx` and all four limbs equal to the manifest entry: this observes what the engine actually receives, including `c0,c1` read from the staging array. A BTU half is COMMITTED when the bundle shows `we` with the expected `addr`, `pair` and `data`. The array and BRAM storage bodies are plain writes (`rplu_thimble_pade.v`, `spu_bram_32x64_array.v`) so the bundle is the strongest evidence short of readback; it is not a readback.

**Not claimed.** The existing count/checksum/last-record telemetry and the mirrors for coefficient index 0, row 1 and kappa remain debug aggregates and are not per-write commitment. No SPI command is invented; host observation of configuration acknowledgements is through the H0-C1 record interface, which is R8's, not this document's.

## 6. Minimum allowlist

| Target | Class |
|---|---|
| selector 1, idx 0–4, LOW and HIGH (numerator) | required |
| selector 2, idx 0–4, LOW and HIGH (denominator) | required |
| selector 3, rows 0–6, LOW and HIGH | required |
| selector 6 (kappa) | **unresolved; rejected until decided.** Written as 3 only because the A31-R3 and A31-R2 benches copied the historical Artix consume bench; it feeds only quadray coherence/dissociation telemetry, never result, completion or refusal. If H0 wants the coherence telemetry, kappa needs its own manifest entry and its authorization effect must be stated. |
| selector 7, 4, 5, 0 | prohibited (torus/Artery autonomous emission; SOM weight; audio; none) |
| selectors 1/2 idx 5–7; selector 3 rows 7–63 | prohibited |
| nonzero `material`; address bits outside the used field; non-allowlisted `(selector, address)` | prohibited |
| header bits `[55:51]`, `[33:0]` | cannot be checked at the core boundary; requires an SPI-slave tap (§9) or a narrower claim |

## 7. Independent discriminating witness (supplementary; baseline witnesses unchanged)

The existing constant-term manifests stay as baseline witnesses **SET-N0** and **SET-R0**. The supplementary witnesses reuse the same 34-entry structure with the values below. Source operand precondition is unchanged (lane 3 = (2,0,0,0), expected SOM winner node 1, BTU row 1).

**SET-N-X1 values.** Numerator: n0 = (2,0,0,0); n1 = (1,2,3,4) (LOW c0,c1 = 1,2; HIGH c2,c3 = 3,4); n2 = (7,0,0,9); n3 = n4 = 0. Denominator: d0 = (1,0,0,0); d1 = (0,1,0,2); d2 = d3 = d4 = 0. BTU rows: row k = (k+20, k+30, k+40, k+50) for k ≠ 1, and **row 1 = (3,5,7,11)**.

**Derivation.** With x = row 1 = (3,5,7,11): N(x) = n0 + x·(n1 + x·n2) = (34168, 22656, 24346, 20300); D(x) = d0 + x·d1 = (346, 73, 63, 13), invertible (`flags_v` false). Result N/D = **(1802234782, 506891096, 1918494961, 831706698)** = limbs `0x6B6BEB9E, 0x1E368B58, 0x7259E8F1, 0x3192D64A`. Two independent computations agree: `software/lib/a31_field.py::pade_eval`, and a separate exact calculation written for this task (explicit multiplication table on the basis [1,√3,√5,√15], Horner evaluation, and inversion by Gaussian elimination mod p instead of the tower; it also confirms the SET-R0 denominator is singular).

**It distinguishes plausible incomplete configurations** (oracle results; all differ from the intended result). Omitted destinations are assumed to retain the SET-N0 baseline state (zero coefficients 1–4, row 1 = (1,0,0,0)); a different prior state changes the numbers, so each variant must be re-evaluated against the oracle for the prior state actually used:

| Variant | Result limbs |
|---|---|
| V1 n1 HIGH omitted (n1 stays 0 after baseline) | (1096513973, 1662572458, 1125221986, 591723925) |
| V2 n1 HIGH commits a stale LOW (0,0,3,4) | (292335249, 312055228, 14290060, 847758925) |
| V3 n1 halves swapped (3,4,1,2) | (916671964, 1838346323, 1185795586, 516456347) |
| V4 n1 limb c3 corrupted 4→5 | (379733549, 2135499832, 1517584753, 995943000) |
| V5 n2 omitted | (755095218, 591345678, 1677424112, 1508574447) |
| V6 coefficients written one index too high | (214053049, 1144216999, 991699133, 697782832) |
| V7 d1 omitted | (34168, 22656, 24346, 20300) |
| V8 d1 HIGH omitted | (1581790451, 1303427078, 326528094, 1792916970) |
| V9 row 1 HIGH omitted | (1348954217, 98242819, 811938142, 1976270817) |
| V10 row 1 halves swapped | (1100451632, 352039690, 1259526963, 1532523133) |
| V11 row 1 LOW omitted (row 1 keeps SET-N0's LOW (1,0)) | (1894260082, 19361544, 566142575, 2141293916) |
| V12 wrong row selected (row 0) | (1108734640, 579629885, 1612772892, 1169175214) |
| V13 wrong row selected (row 2) | (1372737050, 2038718457, 1511753896, 780843173) |
| V14 numerator and denominator swapped | (211996569, 505328679, 1130297362, 2005280376) |

**SET-R-X1 (refusal that depends on the nonconstant configuration).** Same numerator and rows as SET-N-X1; denominator d1 = (1,0,0,0) and d0 = W − x = (`0x2CEE24AF`, `0x7FFFFFFA`, `0x7FFFFFF8`, `0x7FFFFFF5`), so D(x) = W = (0x2CEE24B2,0,0,1), the characterized zero divisor, **only if** d0, d1 and row 1 are all committed correctly. Oracle: intended = refusal (`flags_v`). Omitting d1 gives (1799765541, 1064189451, 199771714, 1607659094); corrupting d1 to (1,0,0,1) gives (1607282987, …); d0 HIGH omitted gives (1608304621, …); wrong row 0 gives (682094954, …); row 1 HIGH omitted gives (1029892468, …): each is a successful completion instead of the refusal.

These are oracle predictions for supplementary witnesses, not RTL observations; the finite-width interpretation is exact A₃₁ arithmetic over M31 (no truncation). The numerical-domain guard applies only to the source operand, not to coefficients. The witness is not RTL-qualified; it must be exercised in a later authorized simulation.

## 8. Directed verification plan (not executed; no harness created)

Observables: R8 state (lifecycle, `p`, `s`, records, `F`, counters including `sw`), plus **commit-bundle counters** (Padé `nc`, BTU `bc`: number of bundle pulses and the last observed bundle), plus core completion and result telemetry for execution checks.

| ID | Stimulus | Expected transition | Assertion |
|---|---|---|---|
| CF-01 | full SET-N0 (34 frames), then `0x2A` | CONFIG→READY at `p=34`; one STAGED ack per LOW, COMMITTED per HIGH/BTU half; success result (2,0,0,0) | `p` advances only on COMMITTED; bundle matches every entry; result equals oracle |
| CF-02 | full SET-R0, then `0x2A` | READY; arithmetic refusal | one refusal pulse aligned with `inst_done`, no result-valid, no commit |
| CF-03 | reset between a LOW and its HIGH; then HIGH | CONFIG, stage cleared, `p=0`; HIGH rejected (`WRONG_ORDER`) | `nc` unchanged; core staging array still holds the earlier LOW but is not committed |
| CF-04 | failed frame (bad value) between LOW and HIGH; then valid HIGH | invalidated; `p=0`; HIGH rejected | stage register empty; `nc` unchanged |
| CF-05 | HIGH with no current-attempt LOW, while the core staging array holds a previous-attempt LOW | rejected `WRONG_ORDER`; nothing reaches the core | no bundle pulse; engine array unchanged (observed through the witness after later install) |
| CF-06 | duplicate LOW; HIGH before LOW; entries out of order | `DUPLICATE` / `WRONG_ORDER`; replay required | `p=0`, no commit |
| CF-07 | configuration frame while an instruction is outstanding | `CONFIG_BUSY`; authorization and instruction unaffected | instruction completes with the expected result; no bundle pulse |
| CF-08 | reset after committed Padé HIGH, mid-manifest; then `0x2A` | CONFIG; `NOT_READY` rejection | physical values retained (shown later by CF-09/CF-13), but no execution |
| CF-09 | reinstall full manifest after reset | READY; result as CF-01 | all 34 bundles observed again in this attempt |
| CF-10 | selectors 7/4/5/0; idx 5–7; rows ≥ 7; nonzero material; address high bits; kappa | rejection records; no authorization | no bundle pulse; no `torus_emit_enable`; `p` unchanged |
| CF-11 | SET-N-X1 install then `0x2A` | READY; result = (1802234782, 506891096, 1918494961, 831706698) | equals oracle |
| CF-12 | SET-R-X1 install then `0x2A` | READY; arithmetic refusal | refusal, not success |
| CF-13 | variants V1–V14 and SET-R-X1 variants installed through a test-only path that bypasses the controller | result differs from intended | each variant's result equals its oracle value and not the intended result |
| CF-14 | failure after a BTU LOW half committed | `p=0`; partial row never authorizes; replay completes it | after replay, witness result equals CF-11 |
| CF-15 | observe the replayed LOW+HIGH pulses | consecutive cycles, nothing between | no other configuration write between the two pulses; HIGH bundle `c0,c1` equals the stage register value |
| CF-16 | frame arrival during the two replay cycles (if the SCK ratio allows it) | `CONFIG_BUSY` or buffered per the decision | no interleaving into the replay |

**Negative controls (each must fail its named assertion, not time out):** M-C1 LOW forwarded directly to the core (no replay) → CF-05 commits a stale LOW; M-C2 HIGH accepted without a current LOW → CF-03/05; M-C3 reset leaves the stage register or `p` → CF-03/08; M-C4 STAGED counted as progress → CF-01; M-C5 READY at `p=33` → CF-01; M-C6 configuration accepted while an instruction is outstanding → CF-07; M-C7 acknowledgement without comparing the bundle (forwarded value corrupted by one limb) → CF-13/15; M-C8 selector 7 or idx 5 accepted → CF-10; M-C9 authorization kept on a failed attempt → CF-04; M-C10 replay interleavable → CF-15/16; M-C11 supplementary witness with n2 or row 1 HIGH omitted → CF-11. Plus the standing runner controls: a PASS-looking transcript followed by a nonzero exit must be rejected, and every assertion hit count must be nonzero.

## 9. Relationship to R8/T5 and required production integration points

**Mapping to R8's fake sink (the production adapter).** The adapter presents R8's sink interface to the controller: accept → PENDING identity; LOW commit = write into the adapter's stage register (R8 STAGED); HIGH commit = the atomic replay plus bundle match (R8 pair COMMITTED); BTU halves and any single writes = one pulse plus bundle match; cancellation drops a pending request before replay starts. R8's request ownership, capability banks, record freshness and result publication are unchanged.

**Conflicts or gaps to report, not changes to R8.** (a) R8's sink mutation is atomic with the controller grant; here the grant starts a two-cycle indivisible replay and the commit is recognized when the bundle is observed — the adapter must make the replay non-cancellable and treat a reset during it as "physical storage possibly partially changed, never authorizing". (b) R8 leaves undefined configuration while READY, while an instruction is active, and a non-failed submission while a sink operation is pending; §3 proposes definitions as an extension. (c) R8's synthetic manifest has three entries and 8-bit tags; real manifests have 34 entries, so production widths (≥ 6-bit progress) are a separate decision. (d) New rejection kind `CONFIG_BUSY`.

**Production RTL integration points (none implemented):** (1) `spu_spi_slave.v`: an optional tap of the raw 64-bit header (or in-slave canonical-bit rejection) with the configuration pulse, so reserved header bits can be checked. (2) `spu_a7_top.v`: place the configuration adapter between `rplu_cfg_*` and the core's `dec_fast_cfg_*` (the only existing source), and give it the transaction controller's outstanding-instruction state. (3) `spu13_core.v`: export the commit bundle as outputs (existing internal wires). (4) No change to the Padé engine, BRAM or staging arrays for the selected option. (5) Optional later: staging valid/generation bits or readback ports (options B/E).

## 10. Unresolved dependencies

SCK/`clk_fast` relationship and whether a frame can arrive during replay; D13a manifest selection (prefix matching proposed); kappa; whether the SPI-slave header tap is accepted or the claim is narrowed to the visible fields; hardware power-up values of the arrays and BRAM (the 34-entry replay removes dependence on them for manifest-covered state, but not for kappa, torus or rows 7–63, which are prohibited or unreachable); production widths and manifest storage; exact commit-bundle timing against the BRAM write; simulation of assumptions (i)–(iii) in §4; whether the supplementary witnesses are adopted.

## 11. Recommendation

**PASS for the design as a basis for independent review. HOLD for implementation.** Subsequent implementation should wait for: independent review of §3–§5; resolution of the SPI timing relationship, D13a and kappa; an explicit decision to expose the commit bundle; and a separately authorized unit-level simulation of assumptions (i)–(iii), the verification matrix and the supplementary witnesses. The narrower assurance claim for early bring-up is: ordered, allowlisted, individually acknowledged writes plus the baseline and supplementary mathematical witnesses; it is not complete configuration-state verification, because the engine arrays and BRAM have no readback.
