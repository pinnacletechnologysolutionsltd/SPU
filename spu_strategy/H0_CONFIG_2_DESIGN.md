# H0-CONFIG-2 (R3) — Configuration commitment, authorization and verification (design and verification plan)

**Disposition: R3 correction of the reset/storage-edge semantics found by the focused review of R2; implementation and production integration HOLD.** R3 changes only the reset wording of the §5 cycle table and E5/E6, the CF-17/CF-18 cases, §10 and the correction matrix; the architecture, the R2 cycle table's other rows, M-C1/CF-15 and everything else are unchanged. The R2 text is preserved unchanged as `spu_strategy/H0_CONFIG_2_DESIGN_R2.md` (SHA-256 `f8d66192aea5c9ec…`), R1 as `H0_CONFIG_2_DESIGN_R1.md`, R0 as `H0_CONFIG_2_DESIGN_R0.md`. Documentation only: no RTL, no SPI encoding change, no simulation or hardware; R8, the CONFIG-1 manifests, T5 files and the R0 self-review are unchanged; nothing staged or committed. RTL statements are source-derived; mathematical values are host arithmetic; nothing is qualified.

## 1. Source and evidence identities

| Input | Identity |
|---|---|
| Source baseline | `dev/next` `0f631e37caeabb629b81b84a782cee1d881ac0b9`; read-only checkout `~/.local/gate/spu-config1-0f631e3` |
| H0-CONFIG-1 findings and manifests (unchanged) | `H0_CONFIG_1_MANIFEST_FINDINGS.md`; `SET_N_CANDIDATE.json` SHA-256 `7b508182…` (entries `6483d9adc453e35e`), `SET_R_CANDIDATE.json` `51c4a011…` (entries `9936607a53517103`) |
| Supplementary candidates (new, §3.3) | `spu_strategy/h0_config_2/SET_N_X1_CANDIDATE.json`, `SET_R_X1_CANDIDATE.json` |
| R8 (governing, unchanged) | `H0_C1_T4_R8_CONTRACT.md` `d72eb154…`, `H0_C1_T4_R8_FROZEN_TRACES.md` `3a3af1d6…` |
| H0-IMAGE-2 findings | `/tmp/spu-h0-image2/spu_strategy/H0_IMAGE_2_EXCLUSION_FINDINGS.md` `ed311c4f…` (HOLD; top lacks an H0 transaction owner; no conflict) |
| T5 scratch | `/tmp/spu-h0-t5-isolated/experiment/h0_c1_t5/`: listed, not relied on |
| R2 design (preserved) | `H0_CONFIG_2_DESIGN_R2.md` `f8d66192aea5c9ec…`; the focused review of R2 is the input to R3 and is not stored here |
| R1 design (preserved) | `H0_CONFIG_2_DESIGN_R1.md` `7c4c6564f5f0426f…`; its independent review (disposition REVISE) is the input to R2 and is not stored here |
| R0 design and R0 review | `H0_CONFIG_2_DESIGN_R0.md` `e8a502e653e448ee…`; `H0_CONFIG_2_DESIGN_REVIEW.md` `d517023032d2fbff…` (author's self-review, not independent) |

## 2. Current limitations (from H0-CONFIG-1)

The `0xA5` path gives a one-cycle pulse with no acknowledgement; Padé LOW writes a core-side staging array and HIGH commits `{staged c0,c1 ; c2,c3}` into the engine; BTU halves commit immediately; staging arrays, engine arrays and BRAM have no reset branch; writes are accepted while an instruction is in flight; the SPI slave discards `hdr[55:51]` and `hdr[33:0]`; there is no readback; selector 7 can enable autonomous Artery emission. R8 leaves configuration while READY, configuration while an instruction is active, and a non-failed submission while a sink operation is pending undefined.

## 3. Authorization, progress and identity (C1, C2)

### 3.1 Three separate accountings (proposed real-H0 adapter convention; R8 is not modified)

| Accounting | Meaning | Range | Advances |
|---|---|---|---|
| **Entry pointer `n`** | manifest entries *accepted in order* in the current attempt (LOW counts when accepted); used for order checking and identity narrowing | 0…34 | at acceptance of an in-order, in-manifest frame |
| **Committed-step count `p`** | architectural steps committed in the current attempt | 0…24 | a Padé LOW/HIGH **pair** is one step, added when its HIGH is COMMITTED (a LOW never advances `p`); each BTU half is one step, added when COMMITTED |
| **Lifecycle and authorization** | `L ∈ {CONFIG, READY}`; authorization `A = (L = READY) ∧ F = 0`; manifest identity `I` (§3.3); sticky fault `F` | | see rules |

Counting rule check: 10 Padé pairs (entries 0–19) + 14 BTU halves (entries 20–33) = **24 steps**. With `c` entries committed (pair-aligned): `p = c/2` for `c ≤ 20`, `p = 10 + (c−20)` for `c > 20`; examples (checked): c = 2→1, 10→5, 20→10, 21→11, 33→23, 34→24. This is R8's own rule (R8's synthetic LOW/HIGH/SINGLE reaches `p = 2`: the pair is one step and the single is one step); only the manifest length differs.

### 3.2 Rules

1. **Reset** (physical only) → `CONFIG`, `n=0`, `p=0`, stage register cleared, `I=UNSELECTED`, pending sink work and any replay cancelled, configuration-ack record NONE. Physical coefficient registers, BRAM and the core staging arrays are **not** touched and carry **no authority**.
2. **READY requires**: `n = 34`, `p = 24`, `I = LOCKED(m)`, the 34th entry COMMITTED, no pending work, `F = 0`. A shorter attempt never reaches READY. Because the manifests write every coefficient position and every reachable BTU row, a complete attempt overwrites the whole mathematical state.
3. **A failed submission** (R8 kinds, plus the production extensions `CONFIG_BUSY`, `COMMIT_MISSING`, `COMMIT_MISMATCH`, `UNGRANTED_WRITE`) records a rejection, cancels pending sink work, clears the stage register, sets `n=0, p=0, I=UNSELECTED, L=CONFIG` and requires full replay.
4. **Authorization is revoked at acceptance of the first frame of a new attempt**, not at its commit, so READY never covers a half-rewritten configuration (extension; R8 undefined).
5. **Interlock:** a configuration frame while any instruction is outstanding is rejected as `CONFIG_BUSY`; it has no effect on configuration, authorization or the active instruction (extension; R8 undefined).
6. **Kappa** is not part of any manifest identity; its write is rejected until the decision in §6.

### 3.3 Manifest identity: deterministic prefix-trie matching

**Frozen set** `Φ` of four candidate identities, each exactly 34 ordered entries `(selector, address, value64)` with `material = 0`, in the CONFIG-1 order (numerator coefficients 0–4 LOW/HIGH = entries 0–9, denominator 10–19, BTU rows 0–6 LOW/HIGH = 20–33): **SET-N0, SET-R0** (the preserved CONFIG-1 sequences, regenerated here and verified identical to the preserved JSON entries), **SET-N-X1, SET-R-X1** (§7; sequences in `h0_config_2/`). Uniform sequence hashes over the `(selector,address,value64)` triples: N0 `57ad9e2ef58e065b…`, R0 `6e7792fa23af9953…`, N-X1 `3cd15e7cefb91a57…`, R-X1 `1c160023f198082f…`.

**Checked properties (script, host arithmetic).** All four have length 34 and are pairwise distinct, so **no manifest is a prefix of another**. First divergences: N0 vs R0 at entry 10 (denominator coefficient 0 LOW); N-X1 vs R-X1 at entry 10; {N0, R0} vs {N-X1, R-X1} at entry 2 (numerator coefficient 1 LOW). Entries 0 and 1 are identical in all four.

**Matching.** Let `S(n)` be the manifests whose first `n` entries equal the accepted entries. At acceptance of entry `j`, the frame must equal entry `j` of at least one member of `S`; otherwise it is a failed submission (`WRONG_VALUE` or `WRONG_ORDER`). `S` narrows at acceptance but **identity is not locked at acceptance**:

* `I = UNSELECTED` at reset or after any failure; `I = PROVISIONAL(S)` while `|S| > 1`, **or** while the entry that made `|S| = 1` has not been COMMITTED.
* `I = LOCKED(m)` only when `|S| = 1` **and** that distinguishing entry is COMMITTED. A divergence on a Padé LOW is therefore locked only when its HIGH commits. Lock points for this set: the family (baseline versus X1) after the pair of entries 2–3 commits (`p = 2`); the manifest after the pair 10–11 commits (`p = 6`).
* Once locked, a later frame that does not equal the locked manifest's entry is a failed submission; identity then returns to `UNSELECTED`. Identity cannot change without a failed or new attempt.
* An attempt that stops early (for example after entry 9) stays `PROVISIONAL`, never READY, and is cleared by reset or failure.

The preserved SET-N0 and SET-R0 files are unchanged; the X1 sequences are additional files.

## 4. Paired-write ownership: alternatives and selection (unchanged architecture)

| Option | Assessment |
|---|---|
| **A — controller-owned staging, atomic LOW+HIGH replay (selected)** | The controller holds a validated LOW in its own stage register and sends **nothing** to the core until the matching HIGH is validated; it then drives the core with the LOW write and, on the next clock, the HIGH write (an uninterruptible replay) and checks the commit bundle (§5). The core's staging array is overwritten with the current-attempt LOW immediately before every HIGH, so stale content cannot be committed; failed or reset attempts leave the core untouched. |
| B — generation/valid bits in the core staging arrays | hardware-checked pairing; modifies the mathematical core's configuration logic; not selected now |
| C — reset-clear the staging arrays | does not address stale LOW in an attempt or failed attempts; rejected |
| D — host discipline plus aggregate checksum | cannot prove pairing or destination; rejected |
| E — A plus array readback | strongest evidence, largest RTL change; deferred |

**Staging versus commitment.** The replayed LOW mutates only the core staging array (not read by the evaluator); the architectural commitment is the HIGH write into the engine array. **Replay timing (source-derived).** The SPI slave and core are both on `clk_fast`; `sck_rise` is a `01` pattern in a 3-stage SCK history, so detected rises are at least two cycles apart, and a configuration pulse follows a full frame of 144 rises (8 + 64 + 64 + 8), so consecutive configuration pulses are at least **288 `clk_fast` cycles** apart whatever the SCK frequency, **conditional on the slave implementation as written** (source-derived; it does not replace the replay interlock and fault of CF-16). A replay of a few cycles therefore cannot overlap a following frame and no frame buffering is needed. The core decodes configuration combinationally and accepts one write per cycle (the write sits in the final `else` of a sequential block whose earlier branches are reset and the boot-time `prime_we`, tied to 0 in the Artix top); a LOW pulse at cycle *k* is visible to the HIGH decode at *k+1* (unsimulated assumption).

## 5. Commitment acknowledgement and commit-evidence failure semantics (C3)

| Event | Owner | Observable |
|---|---|---|
| SPI frame received | `spu_spi_slave` | existing `rplu_cfg_wr_en` pulse after CRC (raw header bits `[55:51]`, `[33:0]` are lost) |
| Request accepted | controller | PENDING in the adapter; not an acknowledgement |
| Low-half staged | controller stage register | R8 configuration-ack `STAGED`; `p` unchanged |
| Mathematical state committed | core | **commit bundle** matches (below) |
| Configuration acknowledgement published | controller | R8 configuration-ack record `COMMITTED`; `p += 1` |
| Complete manifest authorized | controller | §3.2 rule 2 → READY |

**Commit bundle (minimum new core outputs; existing internal wires):** Padé `{we, is_den, idx[2:0], c0, c1, c2, c3}` (`rplu2_pade_coeff_*`) and BTU `{we, addr[5:0], pair, data[63:0]}` (`rplu2_btu_cfg_*`). **Padé verification is of the pair:** the bundle's `is_den`, `idx` and all four limbs must equal `{stage register ‖ HIGH entry}`; the LOW replay pulse must produce **no** Padé `we`. A BTU half's bundle must equal its entry. The bundle observes the write-input pins, **not** array or BRAM contents: it is not readback, and it does not detect memory or synthesis misbehaviour.

**Bundle cycle table (R2).** Let the controller drive a core configuration pulse during cycle *k* (its pulse-driving flops changed at the edge that began *k*). The bundle is a combinational function of the driven pulse, and the configuration state elements (core staging arrays, engine coefficient arrays, BTU BRAM) are plain clocked writes enabled by that same decode, so the **sample edge and the storage edge coincide**. The tap type is an integration parameter `TAP ∈ {COMB, REG}` fixed at design time:

| Step | `TAP=COMB` | `TAP=REG` (bundle registered at E_k) |
|---|---|---|
| Controller drives pulse | cycle *k* | cycle *k* |
| Bundle valid at the tap | cycle *k* | cycle *k* (combinational), captured at E_k |
| Controller samples/compares | at E_k (end of *k*) | during *k+1* (at E_{k+1}) |
| Storage edge (staging, engine array or BRAM write) | E_k, the same edge as the sample | E_k |
| COMMITTED recorded, `p` +1, config-ack unread set | visible in cycle *k+1* | visible in cycle *k+2* |
| Compare window | cycle *k* only | cycle *k+1* only (absence at its end = E1) |
| Reset asserted early (the controller's pulse drivers are cleared before E_k) | no pulse at E_k, so no write to any storage; no fault | same |
| Reset **sampled active at E_k** | **core staging array** (LOW writes): suppressed, because the write sits in the `else` of the core's `if (!rst_n)` branch (source-derived from the RTL, not measured). **Engine coefficient array and BTU BRAM**: no reset term in their write logic, so the write at E_k happens unless the pulse driver was already cleared; that depends on the controller's reset style and timing and is **not defined by the RTL**, so "may have landed". Never counted; no fault; authorization cleared | same, for the storage edge E_k |
| Reset **after E_k** (sampled inactive at E_k) | the write has happened and reset cannot undo it; reset only cancels the observation and acknowledgement (E6) | the write happened at E_k; a reset in cycle *k+1* cancels the observation/acknowledgement only and does **not** imply the write was prevented |

For a Padé pair, *k* is the HIGH pulse cycle and the LOW pulse is cycle *k−1*; the LOW storage edge E_{k−1} is the edge at which the staging array takes the LOW value that the HIGH decode reads in cycle *k*. "HIGH issued" means cycle *k*, "bundle observed" means the tap time in the table, and "write committed" means E_k; the controller must not infer any of them from another. The unresolved tap latency (`TAP`) is an acceptance criterion of the isolated experiment: every CF/M-C case that names a window must be run for both values or the unused value must be declared out of scope.

| ID | Event | Outcome |
|---|---|---|
| E1 | expected bundle **missing** at window end | attempt fails (`COMMIT_MISSING`): `n=0, p=0, I=UNSELECTED, L=CONFIG`, READY blocked, **F=1** (controller/core inconsistency, integrity class) |
| E2 | bundle present with **wrong selector, index, address, pair or data** | attempt fails (`COMMIT_MISMATCH`), same consequences as E1, F=1 |
| E3 | **unexpected bundle**: a second `we` for one grant, a Padé `we` during the LOW replay pulse, or a bundle of a kind other than the granted write | F=1; any active attempt fails; if `L=READY`, authorization is revoked (`L=CONFIG`) |
| E4 | **bundle without controller authorization** (no grant outstanding, e.g. a path that bypasses the controller) | record `UNGRANTED_WRITE`, F=1, authorization revoked; never ignored |
| E5 | **reset between the two replay pulses** (after the LOW pulse cycle *k−1*, before the HIGH pulse cycle *k*) | reset-edge priority: replay cancelled, no fault; `n, p, I` cleared. If reset was sampled active at E_{k−1}, the LOW write to the staging array is suppressed (source-derived); otherwise the staging array holds the LOW. No engine `we` has occurred in either case. Not authorizing |
| E6 | **reset at or after HIGH issuance, before the observation completes** | reset-edge events cancelled without fault; `n, p, I` cleared. Reset sampled active at E_k: the engine/BRAM write is not suppressed by the RTL and "may have landed" (staging not involved); reset after E_k: the write has happened. In both cases the entry is not counted and the next attempt rewrites everything |

F is the R8 sticky fault (blocks new requests, freezes existing work, cleared only by reset). The classification of integrity events remains H0-C1 D7; the kinds above are proposed production extensions. The existing count/checksum/last-record telemetry and the mirrors for coefficient 0, row 1 and kappa remain debug aggregates, not per-write commitment, and are not sufficient proof of configuration. No SPI command is invented.

## 6. Minimum allowlist

| Target | Class |
|---|---|
| selector 1, idx 0–4, LOW/HIGH (numerator) | required |
| selector 2, idx 0–4, LOW/HIGH (denominator) | required |
| selector 3, rows 0–6, LOW/HIGH | required |
| selector 6 (kappa) | **unresolved; rejected until decided.** It was written as 3 by the A31-R2/R3 benches because they copied the historical Artix consume bench; it feeds only quadray coherence/dissociation telemetry, never result, completion or refusal. If H0 wants that telemetry it needs its own manifest entry and a stated authorization effect. |
| selectors 7, 4, 5, 0 | prohibited (torus/Artery autonomous emission; SOM weight; audio; none) |
| selectors 1/2 idx 5–7; selector 3 rows 7–63 | prohibited |
| nonzero `material`; address bits outside the used field; non-allowlisted pairs | prohibited |
| header bits `[55:51]`, `[33:0]` | not checkable at the core boundary; needs an SPI-slave tap (§9) or a narrower claim |

## 7. Independent discriminating witness (supplementary; baseline witnesses unchanged)

SET-N0 and SET-R0 remain the baseline witnesses. The X1 witnesses reuse the same 34-entry structure; source operand lane 3 = (2,0,0,0), expected SOM winner node 1, BTU row 1.

**SET-N-X1.** Numerator n0 = (2,0,0,0), n1 = (1,2,3,4), n2 = (7,0,0,9), n3 = n4 = 0; denominator d0 = (1,0,0,0), d1 = (0,1,0,2), d2–d4 = 0; BTU row k = (k+20, k+30, k+40, k+50) for k ≠ 1, **row 1 = (3,5,7,11)**. With x = (3,5,7,11): N(x) = (34168, 22656, 24346, 20300), D(x) = (346, 73, 63, 13) (invertible); result **(1802234782, 506891096, 1918494961, 831706698)** = limbs `0x6B6BEB9E, 0x1E368B58, 0x7259E8F1, 0x3192D64A`. Two independent computations agree (`a31_field.py::pade_eval`; a separate multiplication-table evaluation with Gaussian-elimination inversion). All coefficients and row limbs are canonical, so no finite-width effect arises.

| Variant (omitted destinations keep SET-N0 values: zero coefficients 1–4, row 1 = (1,0,0,0)) | Result limbs |
|---|---|
| V1 n1 HIGH omitted | (1096513973, 1662572458, 1125221986, 591723925) |
| V2 n1 HIGH commits a stale LOW (0,0,3,4) | (292335249, 312055228, 14290060, 847758925) |
| V3 n1 halves swapped | (916671964, 1838346323, 1185795586, 516456347) |
| V4 n1 limb c3 corrupted 4→5 | (379733549, 2135499832, 1517584753, 995943000) |
| V5 n2 omitted | (755095218, 591345678, 1677424112, 1508574447) |
| V6 coefficients written one index too high | (214053049, 1144216999, 991699133, 697782832) |
| V7 d1 omitted | (34168, 22656, 24346, 20300) |
| V8 d1 HIGH omitted | (1581790451, 1303427078, 326528094, 1792916970) |
| V9 row 1 HIGH omitted | (1348954217, 98242819, 811938142, 1976270817) |
| V10 row 1 halves swapped | (1100451632, 352039690, 1259526963, 1532523133) |
| V11 row 1 LOW omitted (keeps (1,0)) | (1894260082, 19361544, 566142575, 2141293916) |
| V12 wrong row selected (row 0) | (1108734640, 579629885, 1612772892, 1169175214) |
| V13 wrong row selected (row 2) | (1372737050, 2038718457, 1511753896, 780843173) |
| V14 numerator and denominator swapped | (211996569, 505328679, 1130297362, 2005280376) |

A different prior state changes these numbers, so each variant must be re-evaluated against the oracle for the prior state actually used; CF-22 requires that the witness is run after a different prior manifest.

**SET-R-X1.** Same numerator and rows; d1 = (1,0,0,0), d0 = W − x = (`0x2CEE24AF`, `0x7FFFFFFA`, `0x7FFFFFF8`, `0x7FFFFFF5`), so D(x) = W = (0x2CEE24B2,0,0,1), the characterized zero divisor, only if d0, d1 and row 1 are all committed correctly. Oracle: refusal (`flags_v`). Omitting d1 gives (1799765541, …), corrupting d1 to (1,0,0,1) gives (1607282987, …), d0 HIGH omitted gives (1608304621, …), wrong row 0 gives (682094954, …), row 1 HIGH omitted gives (1029892468, …): each is a successful completion. Oracle predictions only, not RTL observations; the numerical-domain guard applies to the source operand only.

## 8. Directed verification plan (not executed; no harness created)

Observables: R8 state (`L, n, p, I, s, F`, records, counters including `sw`), commit-bundle counters (Padé `nc`, BTU `bc`) and the last bundle, a **harness-owned independent bundle monitor** (compares every core configuration write with the frozen manifest copy in the harness, independent of the controller), and core completion/result telemetry.

**Verification interface (R2).** The experiment exposes the controller-internal state that several assertions need, as verification taps (not architectural observables): `L, n, p, I, s, F`, the candidate set `S`, the stage register and its valid bit, the replay FSM state, and two separate event signals: `host_low_accept` (the adapter accepted a LOW frame from the host) and `host_high_validated` (a HIGH frame matching the staged LOW was validated and replay is granted), distinct from `core_cfg_pulse` (the adapter's driver output to the core, with its selector, address, half and data). The independent monitor samples **the same bundle window as the controller** (the cycle named by `TAP` in §5), so a window skew cannot mask a mismatch.

| ID | Stimulus | Expected transition | Assertion (named point) |
|---|---|---|---|
| CF-01 | install SET-N0 then `0x2A` | READY at `n=34, p=24`; success (2,0,0,0) | `p` unchanged at each LOW STAGED edge, +1 at each COMMITTED edge; `L=CONFIG` at the 33rd-entry edge, READY at the 34th |
| CF-02 | install SET-R0 then `0x2A` | READY; arithmetic refusal | one refusal pulse aligned with `inst_done`; no result-valid, no commit |
| CF-03 | reset between a LOW and its HIGH *frames*; then HIGH | CONFIG, stage cleared, all counters 0; HIGH rejected `WRONG_ORDER` | `nc` unchanged at the HIGH edge |
| CF-04 | failed frame between LOW and HIGH; then valid HIGH | `L=CONFIG`, `n=p=0`; HIGH rejected | stage empty at the failure edge+1 |
| CF-05 | HIGH with no current LOW while the core staging array holds a previous-attempt LOW | `WRONG_ORDER`; nothing reaches the core | zero core configuration pulses and zero bundle at the HIGH acceptance edge |
| CF-06 | duplicate LOW; HIGH before LOW; out-of-order entries | `DUPLICATE` / `WRONG_ORDER`; replay required | `n=p=0` after the failing edge |
| CF-07 | configuration frame while an instruction is outstanding | `CONFIG_BUSY`; authorization and instruction unaffected | instruction completes as expected; zero bundle during it |
| CF-08 | reset after a committed Padé HIGH mid-manifest; then `0x2A` | CONFIG; `NOT_READY` | `L=CONFIG` and `p=0` at reset edge+1; no execution |
| CF-09 | reinstall SET-N0 after reset | READY; result as CF-01 | all 34 bundles observed again in this attempt |
| CF-10 | selectors 7/4/5/0; idx 5–7; rows ≥ 7; nonzero material; address high bits; kappa | rejection kinds; no authorization | zero core pulses and zero bundle at each acceptance edge; `torus_emit_enable` stays 0 |
| CF-11 | install SET-N-X1 then `0x2A` | READY; result (1802234782, 506891096, 1918494961, 831706698) | equals oracle |
| CF-12 | install SET-R-X1 then `0x2A` | READY; arithmetic refusal | refusal, not success |
| CF-13 | variants V1–V14 and the SET-R-X1 variants, installed through a test-only path that bypasses the controller (core-level) | result differs from intended | each result equals its oracle value and not the intended one |
| CF-14 | failure after a BTU LOW half committed; then replay | `n=p=0`; partial row never authorizes; replay completes it | after replay, witness result equals CF-11 |
| CF-15 | replay structure, for each Padé pair | (a) **from `host_low_accept` until `host_high_validated`, the adapter produces zero `core_cfg_pulse` and zero bundle**; at replay it produces exactly two pulses on consecutive cycles, the first with half = LOW and the data of the stage register, the second with half = HIGH; (b) nothing else between them; (c) the HIGH bundle `c0,c1` equals the stage register | (a) pulse count 0 over the interval `[host_low_accept, host_high_validated)`; exactly 2 pulses over the replay interval, with half(first)=LOW and half(second)=HIGH; (b) no other core configuration pulse between the two; (c) independent monitor equality in the `TAP` window |
| CF-16 | structural enforcement of the no-overlap assumption | the 288-cycle spacing holds for legal SPI streams; an illegal pulse during replay is a fault | assumption monitor: spacing between `cfg_wr_en` pulses ≥ 288 cycles under the legal-SPI model; negative test: an injected pulse during replay sets F=1 |
| CF-17 | **reset between the two replay pulses**, both cases: (a) reset sampled active at E_{k−1}; (b) reset after E_{k−1} and before the HIGH pulse | E5: replay cancelled, no fault, counters 0 | no engine `we` ever occurs; `F=0`; the staging-array state is *recorded* for (a) and (b) and expected to be unchanged in (a), written in (b); `L=CONFIG`, `p=0` at reset edge+1 |
| CF-18 | **reset around HIGH issuance**, three cases per `TAP`: (a) reset asserted early enough that the pulse drivers are cleared before E_k; (b) reset **sampled active at E_k**; (c) reset **after E_k** (for `TAP=REG` this includes cycle *k+1*) | E6: no fault, not counted | `p` and config-ack record NONE and `L=CONFIG` at reset edge+1 in all cases; (a) engine entry unchanged and no bundle; (b) the engine/BRAM write outcome is **recorded, not asserted** (not defined by the RTL), and the staging array, where involved, is expected unchanged (source-derived); (c) the write is observed as having happened (the experiment checks the stub sink) and the acknowledgement is cancelled |
| CF-19 | **reset on the final configuration entry** (entry 33) before READY | READY never asserted; after reset NOT_READY; reinstall reaches READY | `L=CONFIG` at the reset edge+1 |
| CF-20 | commit-evidence failures via a stub core: (a) missing bundle, (b) wrong selector, index, address or data, (c) unexpected second or LOW-time Padé `we`, (d) ungranted write while idle and while READY | E1–E4 | (a)/(b) `COMMIT_MISSING`/`COMMIT_MISMATCH`, `n=p=0`, `F=1`, no READY; (c)/(d) `F=1`, authorization revoked, `UNGRANTED_WRITE` for (d) |
| CF-21 | **manifest-selection branches**: (a) baseline versus X1 family lock after entries 2–3 commit; (b) N versus R lock after entries 10–11 commit, in each family; (c) wrong value after lock; (d) stop before lock then reset; (e) divergent LOW accepted but its pair fails; (f) a 20-entry or 33-entry attempt; (g) mixed manifest (X1 prefix then a baseline value) | (a)(b) `I` becomes LOCKED only at the pair commit; (c)(e)(g) failure, `I=UNSELECTED`; (d)(f) never READY | `I` and `L` at each named edge; no READY at `n<34` or `p<24` |
| CF-22 | **reinstall after a different previously committed manifest**: N0→X1, R0→X1, X1→N0, R-X1→N0 | READY each time; witness result equals the oracle for the installed manifest | a stale value from the prior manifest would change the result (V-table) |

**Mutation controls (each must fail the named assertion at the named point; a timeout or an unrelated earlier failure is not detection):**

| ID | Defective variant | Case and detection point |
|---|---|---|
| M-C1 | LOW forwarded to the core at host-LOW acceptance (instead of being held for replay) | CF-15(a): any `core_cfg_pulse` with half = LOW inside `[host_low_accept, host_high_validated)`; the permitted replay LOW pulse occurs only after `host_high_validated` and is not a detection |
| M-C2 | HIGH accepted without a current LOW | CF-03/CF-05: no `WRONG_ORDER`; bundle appears at the HIGH edge |
| M-C3 | reset leaves stage, `n`, `p` or `I` | CF-03/08/19: state ≠ 0 at reset edge+1 |
| M-C4 | LOW counted as a committed step | CF-01: `p ≠ 0` at the first LOW STAGED edge |
| M-C5 | READY at `p=23` or `n=33` | CF-01/CF-19: `L=READY` at the 33rd-entry edge |
| M-C6 | configuration accepted while an instruction is outstanding | CF-07: no `CONFIG_BUSY`; bundle during the instruction |
| M-C7 | acknowledgement without comparing the bundle, with a limb corrupted in forwarding | CF-15(c)/CF-20(b): the **independent monitor**, sampling the same `TAP` window, reports a mismatch at the HIGH pulse while the controller acknowledges COMMITTED |
| M-C8 | forbidden selector or index accepted | CF-10: nonzero core pulse at the acceptance edge |
| M-C9 | authorization kept after a failed attempt | CF-04: `L=READY` or `p≠0` at failure edge+1 |
| M-C10 | replay interleavable, or an illegal pulse during replay ignored | CF-15(b)/CF-16: foreign write between pulses; F stays 0 |
| M-C12 | reset during replay marks COMMITTED or READY | CF-17/18/19: `p≠0` or ack record ≠ NONE at reset edge+1 |
| M-C13 | bundle mismatch ignored | CF-20(b): attempt continues instead of `COMMIT_MISMATCH` |
| M-C14 | missing bundle treated as committed | CF-20(a): COMMITTED at window end |
| M-C15 | unexpected or ungranted bundle ignored | CF-20(c)/(d): F stays 0, READY not revoked |
| M-C16 | identity locked at acceptance instead of commit | CF-21(e): `I=LOCKED` after a failed divergent pair |
| M-C17 | a shorter prefix accepted as complete | CF-21(f): `L=READY` at `n<34` |
| M-C18 | replay skips entries equal to the prior manifest | CF-22: stale-value witness result after N0→X1 |

Standing runner controls: a transcript that matches but ends with a nonzero exit must be rejected; every assertion must have a nonzero hit count. The suite contains no redundant permutations beyond the named branches.

## 9. Relationship to R8/T5 and production integration points

**Adapter mapping to R8's sink interface.** accept → PENDING identity; LOW commit = write to the adapter stage register (R8 STAGED); HIGH commit = uninterruptible replay plus pair-bundle match (R8 pair COMMITTED); BTU half or single = one pulse plus bundle match; cancellation drops a request before replay starts. R8's request ownership, capability banks, record freshness and result publication are unchanged.

**Additional adapter state not in R8's fakes:** the stage register (64-bit value plus selector/index), a replay FSM (idle / LOW / HIGH / compare), the compare window, a 4-bit candidate set `S` and the identity state, the ordered manifest store (4 × 34 entries), `n` (6 bits), `p` (5 bits) and a sticky integrity fault path. (A verification-only independent monitor is outside the design.)

**Experiment interface requirements (R2).** The isolated experiment provides (1) the verification taps and the two host-side event signals of §8; (2) a stub core (or the real core inputs) exposing both bundle types, with `TAP` selectable as COMB or REG; (3) an independent monitor driven by the harness's own copy of the frozen manifests.

**Conflicts or gaps reported, not changes to R8.** (a) R8's sink mutation is atomic with the grant; here the grant starts an uninterruptible two-cycle replay and the commit is recognized when the bundle is observed; a reset during it leaves physical storage possibly changed but never authorizing (E5/E6). (b) R8 leaves configuration while READY, while active, and a non-failed submission while pending undefined; §3.2 defines them as production extensions. (c) R8's three-entry synthetic manifest and 8-bit tags versus 34 real entries; production widths are a separate decision. (d) New kinds `CONFIG_BUSY`, `COMMIT_MISSING`, `COMMIT_MISMATCH`, `UNGRANTED_WRITE` are production extensions.

**Production RTL integration points (none implemented):** (1) `spu_spi_slave.v`: optional tap of the raw 64-bit header with the configuration pulse (or in-slave canonical rejection). (2) `spu_a7_top.v`: configuration adapter between `rplu_cfg_*` and the core's `dec_fast_cfg_*` (the only existing source), with the transaction controller's outstanding-instruction state. (3) `spu13_core.v`: export the commit bundles (existing internal wires). (4) No change to the Padé engine, BRAM or staging arrays for the selected option.

## 10. Remaining assumptions and limitations

Unsimulated: the two-pulse replay and one-write-per-cycle behaviour; the 288-cycle bound rests on the 3-stage synchronizer as written; the tap latency (`TAP=COMB` or `REG`, §5) is open and is an experiment acceptance criterion; the 288-cycle bound is conditional on the slave implementation as written; hardware power-up values of the arrays and BRAM are unknown (the 34-entry replay removes the dependence only for manifest-covered state); kappa unresolved; production widths and manifest storage undecided; the SPI-slave header tap undecided; the bundle is an input-pin observation, not readback; the X1 witnesses and variant values are oracle predictions, not RTL observations, and the end-to-end path through SOM, BTU and configuration is not yet evidenced (the standalone engine testbench exercises nonconstant polynomials in isolation). Reset behaviour at the storage edge is established by RTL reading only (staging suppressed when reset is sampled active; engine array and BRAM have no reset term); no evidence beyond that description exists, and the experiment records the actual outcome for CF-17/CF-18.

## 11. Recommendation

**PASS for R2 as the acceptance specification of a separately scoped isolated experiment; HOLD for implementation and production integration.** The experiment covers the adapter, a stub core exposing both bundle types with selectable tap latency, an independent monitor and the verification taps, and the testbench for CF-01 to CF-22 and M-C1 to M-C18 under both `TAP` values. Because the author also wrote the R0 self-review, the R2 changes should be checked by the same independent reviewer. The narrower early-bring-up assurance claim stays: ordered, allowlisted, individually acknowledged writes with bundle evidence plus the baseline and supplementary mathematical witnesses; it is not complete configuration-state verification.

## 12. Correction matrices

| Item | Correction | Where |
|---|---|---|
| C1 progress | entry pointer `n` (34), committed steps `p` (24), lifecycle/authorization separated; pair = one step, BTU half = one step; READY needs all; documented as a proposed adapter convention matching R8's counting rule | §3.1–3.2 |
| C2 identity | four identities; deterministic prefix trie; no manifest a prefix of another (checked); identity locked only at commit of the distinguishing entry; reset/failure invalidates identity and progress; N0/R0 unchanged | §3.3 |
| C3 evidence failure | E1–E6 outcomes; pair verification; ungranted write is a fault; no readback claim | §5 |
| C4 verification | CF-15(a) (LOW generates no core write), CF-16 structural, CF-17–CF-22, independent monitor for M-C7, every mutation with a named detection point | §8 |

### R1 → R2 (independent review amendments)

| Item | Amendment | Where |
|---|---|---|
| Bundle observation timing | single cycle table (drive, valid, sample, storage edge, acknowledgement, window, reset priority) for `TAP=COMB` and `TAP=REG`; sample and storage edges coincide; E5/E6 restated against it | §5 |
| CF-15(a) / M-C1 | separated `host_low_accept`, `host_high_validated` and `core_cfg_pulse`; expected pulse sequence stated; M-C1 detected only by a LOW-half core pulse inside the acceptance-to-validation interval, not by the replay LOW | §8 |
| Verification taps | controller-internal state exposed as verification taps for the experiment | §8, §9 |
| M-C7 monitor | independent monitor samples the same `TAP` window | §8 |
| Tap latency and 288-cycle bound | tap latency is an experiment acceptance criterion; the 288-cycle argument is labelled conditional on the slave implementation | §4, §5, §10 |

### R2 → R3 (focused review of R2)

| Item | Correction | Where |
|---|---|---|
| Reset timing wording | "before/coincident with/after E_k" replaced by when reset is *sampled active* at the storage edge; early reset (drivers cleared), reset sampled active at E_k, and reset after E_k are separate cases | §5 |
| Reset-before-write priority | stated as source-derived for the core staging array only; engine array and BRAM have no reset term, so a write at E_k is not suppressed by the RTL (depends on controller reset style/timing) | §5, E5/E6 |
| TAP=REG | write at E_k, observation at E_{k+1}; reset in cycle *k+1* cancels the acknowledgement only | §5 |
| CF-17/CF-18 | both edge cases tested explicitly; storage outcomes recorded where the RTL does not define them | §8 |
