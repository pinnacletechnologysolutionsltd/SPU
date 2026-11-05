# Focused v0.2 documentation reconciliation

Review snapshot: 2026-11-05, local `dev/next` at `859235e` with pre-existing dirty work. This is a documentation review, not new hardware or regression evidence. Ledger citations below refer to [hardware evidence](hardware_evidence.md); older records remain scoped to their named artifacts and fixtures.

## Silicon-claim review

All 35 original regex hits are listed once below (locations are original audit line numbers). A ledger pointer here identifies relevant evidence; it does not cure an overbroad statement or prove every detail. The quickstart transcript, explicit denials and prohibition text are scanner false positives. The R3/H0 package record is historical and must not be mistaken for the later board package.

| Original finding | Ledger | Disposition |
|---|---|---|
| [docs/CURRENT_STATUS.md:401](CURRENT_STATUS.md) | §3.2e.2 | Wukong PMUL/PINV: bounded sidecar vectors. |
| [docs/IROTC_SPEC.md:98](IROTC_SPEC.md) | §3.2e.2 | PCHIRAL sidecar observation; VM state rule remains spec-only. |
| [docs/LUCAS_QUICKSTART.md:102](LUCAS_QUICKSTART.md) | §3.2e.7 | False positive: transcript is introduced by a ledger citation. |
| [docs/QUADRAY_FOR_PROGRAMMERS.md:86](QUADRAY_FOR_PROGRAMMERS.md) | §3.2g | Bounded 0–5 Tang probe; floor/non-divisible behavior is not established by that board result. |
| [docs/ROTC_KINEMATICS_PAPER.md:511](ROTC_KINEMATICS_PAPER.md) | §3.2g, core architecture | Corrected full-catalog and tagged-core board overstatement. |
| [docs/SERVICE_COMPOSITION_POLICY.md:135](SERVICE_COMPOSITION_POLICY.md) | §3.2g.5–3.2g.6 | Ambiguity bit in tested SOM1 records, not all inputs. |
| [docs/SOM_SIDECAR_QUICKSTART.md:119](SOM_SIDECAR_QUICKSTART.md) | §3.2g.5 | Verify claimed hash against this entry before relying on image identity. |
| [docs/SPIN_CATALOG.md:93](SPIN_CATALOG.md) | §3.2l | Recorded reference-multiplier four-act run; distinct from §3.2l.1 candidate. |
| [docs/SPU13_IDENTITY_AND_BOUNDARIES.md:40](SPU13_IDENTITY_AND_BOUNDARIES.md) | §3.2g.5–3.2g.6 | Iris is bounded; broad feature list needs claim-by-claim mapping. |
| [docs/SPU13_IDENTITY_AND_BOUNDARIES.md:133](SPU13_IDENTITY_AND_BOUNDARIES.md) | §3.2l–3.2l.1 | Bounded guard and rollback fixtures; no active controller. |
| [docs/ZPHI_KARATSUBA_INTEGRATION_PLAN.md:415](ZPHI_KARATSUBA_INTEGRATION_PLAN.md) | §3.2l–3.2l.1 | Conditional historical publication gate; recorded fixture scope applies. |
| [docs/ZPHI_KARATSUBA_INTEGRATION_PLAN.md:444](ZPHI_KARATSUBA_INTEGRATION_PLAN.md) | §3.2l–3.2l.1 | Both recorded halves, limited to fixtures. |
| [docs/ZPHI_KARATSUBA_INTEGRATION_PLAN.md:471](ZPHI_KARATSUBA_INTEGRATION_PLAN.md) | §3.2l–3.2l.1 | Historical rung explicitly fixture-limited; not general qualification. |
| [docs/glossary.md:84](glossary.md) | §3.2l–3.2l.1 | Bounded transactional cases; active controller remains open. |
| [docs/papers/SU3_COPROCESSOR_PAPER.md:13](papers/SU3_COPROCESSOR_PAPER.md) | §3.2e.5–3.2e.6 | Nine recorded dense-matrix checks; not arbitrary matrices. |
| [docs/rotc_robotics_bringup_plan.md:10](rotc_robotics_bringup_plan.md) | §3.2g–3.2h | Tang canonical rotation and six-step probes. |
| [docs/som_bringup_plan.md:22](som_bringup_plan.md) | §3.2g.3 | Recorded sidecar fixture only; later full-domain arithmetic defect remains. |
| [docs/som_temporal_classification.md:13](som_temporal_classification.md) | §3.2g.5–3.2g.6 | Added corpus scope, citation and arithmetic-defect warning. |
| [docs/som_temporal_classification.md:73](som_temporal_classification.md) | §3.2g.5–3.2g.6, §3.2f | SOM bounded corpus and separate RPLU2 probe; 434 clocks is testbench evidence. |
| [docs/spu13_isa_spec.md:365](spu13_isa_spec.md) | §3.2f | RPLU2 Padé fixture, not the proposed adapter composition. |
| [docs/spu13_isa_spec.md:485](spu13_isa_spec.md) | §3.2f | RPLU2 Padé fixture; no general pipeline qualification. |
| [hardware/pcb/bench_adapter/bench_adapter_spec.md:53](../hardware/pcb/bench_adapter/bench_adapter_spec.md) | §3.2b, §3.2e.2 | Prior SPI wiring/firmware observations; all-pin-map assertion needs pin-by-pin trace. |
| [hardware/pcb/bench_adapter/bench_adapter_spec.md:580](../hardware/pcb/bench_adapter/bench_adapter_spec.md) | multiple probe entries | Future measurement plan referring to existing probes; no new power measurement. |
| [knowledge/ARLINGHAUS_SPATIAL_SYNTHESIS.md:235](../knowledge/ARLINGHAUS_SPATIAL_SYNTHESIS.md) | §3.2j | Specific standalone SPU-4 Tang probe. |
| [knowledge/ARLINGHAUS_SPATIAL_SYNTHESIS.md:247](../knowledge/ARLINGHAUS_SPATIAL_SYNTHESIS.md) | §3.2g.3 | Sidecar fixture; proposed sensor end-to-end path remains future work. |
| [knowledge/INTERCONNECT_ARCHITECTURE.md:63](../knowledge/INTERCONNECT_ARCHITECTURE.md) | §3.2b, §3.2e.2 | Prior link observations; board pin assignments need individual mapping. |
| [knowledge/SPU4_ARCHITECTURE.md:3](../knowledge/SPU4_ARCHITECTURE.md) | §3.2j | Standalone Tang program and probe, not complete architecture. |
| [knowledge/SPU4_ARCHITECTURE.md:71](../knowledge/SPU4_ARCHITECTURE.md) | §3.2j | Standalone core/top fixture; testbench listed separately. |
| [knowledge/SYNERGETICS_BEYOND_GEOMETRY.md:40](../knowledge/SYNERGETICS_BEYOND_GEOMETRY.md) | core architecture | Corrected unsupported Davis Ratio silicon claim; correction pulse was simulation-only. |
| [research/h0_uart_1d/INTEGRATION.md:6](../research/h0_uart_1d/INTEGRATION.md) | §3.46 | Negated historical package-scoped assertion; later distinct board image exists. |
| [spu_strategy/contract_gpu_t1d_vertex_ab_2026-10-04.md:258](../spu_strategy/contract_gpu_t1d_vertex_ab_2026-10-04.md) | — | False positive: explicitly denies silicon-verified regression closure. |
| [spu_strategy/contract_graphics_first_priority_2026-09-04.md:156](../spu_strategy/contract_graphics_first_priority_2026-09-04.md) | §3.0 | ROBOTICS board smoke; not all software robotics behavior. |
| [spu_strategy/contract_regen_stageA_2026-08-20.md:203](../spu_strategy/contract_regen_stageA_2026-08-20.md) | — | False positive: prohibits unbacked claims. |
| [spu_strategy/contract_regen_stageC_2026-08-20.md:92](../spu_strategy/contract_regen_stageC_2026-08-20.md) | — | False positive: prohibits unbacked claims. |
| [spu_strategy/contract_tensegrity_active_control_2026-09-04.md:97](../spu_strategy/contract_tensegrity_active_control_2026-09-04.md) | §3.2k–3.2k.1 | IROTC probe is bounded; exact support for this proposed rotation operation needs a specific mapping. |

Further citation and scope cleanup remains in the individual documents. In particular, feature-wide SOM claims must carry the full-domain defect, the board pin-map statements need pin-by-pin provenance, and the active-control rotation statement needs an operation-level mapping. These are not newly validated by this review.

## Suite totals

- `research/bq0/README.md`: 75/0 is the 2026-10-25 filtered C++/Python run; `result.json`, `COMPLETE`, `exit_status` and `summary.txt` preserve the result. Verilog was filtered out.
- `research/icos0/README.md`: 76/0 is a separate filtered run; its corresponding result and summary preserve the result. Neither is a full-suite total.
- `contract_d4_equal_norm_direction_p2_2026-10-11.md`: 243/0 is explicitly a historical decoder campaign, not a current count. Its cited `build/` stdout and terminal marker are unavailable in this checkout, so the report cannot independently recheck the original log. No count was replaced with the unrelated 238 baseline. The 238/0 record in the T1R recovery contract belongs to an earlier frozen snapshot, not today’s tree.

## Broken-link triage

The audit reported 269 link occurrences. The following groups are classified by target shape, not a claim that every missing artifact should be restored or every historical reference deleted:

- **209 unavailable relative `build/` paths:** these resolve to missing local artifacts. They are real broken links here; many are historical or generated evidence references, and the audit cannot tell whether an artifact exists in an archive elsewhere. The handoff records unresolved off-machine H0 bundle verification. Do not infer missing evidence from the link alone.
- **22 targets involving `research/`:** missing files or packages (including baseline/SG0/SSM links); some may be preserved outside this checkout. The two `research/surd_lorentz...` paths in a `docs/` file also warrant checking their relative base. They are broken here; replacement locations need provenance.
- **18 code fragments:** regex false positives: two C++ signatures and 16 `Path.cwd(` fragments inside Python code. These are not Markdown links.
- **2 `/home/user/...` paths:** machine-specific artifact references; not portable in this checkout. Find the named manifests before replacing them.
- **18 other missing or misrelative targets:** include absent handoffs, review files, a PDF, and four archive-document links whose intended files appear to exist under `docs/` but resolve relative to `docs/archive/bench_sessions/`. These are genuine navigation defects in this checkout; historical relocation and intended target identity need checking before edits.

The machine-readable original inventory can be reproduced with `python3 tools/doc_audit.py --check links --json`; it reports occurrences, not unique files. No archive was altered or artifact reconstructed.

A case-insensitive basename check where the target's parent directory exists
found no case-only filename matches; missing parent directories were not
resolved by that check. The only two root-absolute targets are the local
`/home/user/...` paths above. This review did not verify rendering on GitHub,
so it does not claim that any broken local target works there.

## Remaining evidence boundaries

The H0 board result is one session on one image, with two programs and a reset; it does not qualify UART, CPU, or measured timing margins. The handoff does not establish the off-machine bundle location or verified backup. CPU physical observations, tool reports and simulation remain separate. No full regression, synthesis or board test was run for this documentation review.

For the bounded pre-commit review, the accessible `/home/john/spu-transfer`
research-baseline checkout, the 2026-10-25 development Git bundle's tree,
the H0 preservation source archive and the local repository tarball were checked
for HEX-SOM-named records. None contained an identifiable original report.
The transfer checkout's Ubuntu handover describes `hex_som` files as untracked;
Git bundles alone therefore cannot establish whether a separate backup contains
them. No result was reconstructed and no experiment was rerun.
