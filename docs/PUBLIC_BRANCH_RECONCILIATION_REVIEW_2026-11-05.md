# Public branch reconciliation: review inventory

Snapshot checked 2026-11-05: public `master` = `4e0d5b908e5bb1e0e86ba979b87affb83bd2a372`; local `main` and `dev/next` = `9fe2ceeb6f1113b7323a541d80316784d6cc526f`. A read-only live `ls-remote --symref` confirmed public `master` is the default and all fetched public heads match. The comparison uses committed trees, not local uncommitted README or other work. No Git merge base exists; `b063280` is the parentless RC2 snapshot at the root of the development line.

## Candidate approach

Use local `main` as a candidate development baseline, subject to the owner’s selection after review. Preserve public `master`, all historical refs, and the archive. Do not force a merge or overwrite `master`. Any publication, default-branch change, branch deletion or reconciliation is a separate decision. The [handoff](ARCH_RECONCILIATION_HANDOFF_2026-11-04.md) remains authoritative.

Tree comparison: 1399 shared paths have identical blob IDs; 114 shared paths differ; 31 paths occur only in public `master`; 1684 occur only in local `main`. These counts do not prove semantic equivalence, release readiness, license clearance or test coverage. Both trees contain substantial work; differences require review rather than an assumed direction of superiority.

## Findings and decisions

- **Public-only material:** 22 archived session handover paths, seven historical strategy/publication documents, one INA226 session handoff, and one checked-in VM binary. They remain in `master`; their absence from the candidate snapshot does not establish that they should be republished. Review provenance, intended exclusions and confidentiality before any restoration. The exact list is below.
- **Licensing and release:** root, hardware, software and docs license files and the Iris dataset/provenance/map files have identical blobs at these tips. `LICENSING.md` differs: `master` states that removed `photonics/` and `results/` persist in public history; the candidate adds treatment for research, tool outputs, binary payloads and photos. Reconcile both statements, verify third-party and contributor terms and publication exclusions for added files, and retain notices. Unchanged blobs alone are not a licensing audit.
- **Evidence:** the candidate hardware ledger retains the earlier ledger with two changed lines (date and a device identifier redaction) and adds later GPU and CPU entries. The H0 board session is a bounded single-session observation; implementation-tool timing is separate from physical qualification. The locally preserved H0 bundle and annotated tag have been located, but an independently accessible off-machine copy and its verification remain unestablished by this review.
- **Hardware and software:** changed shared RTL, build flows, VMs and runner include behavior-affecting differences, while the candidate has many additional files. The changed-path list below is an inventory, not an approval of each change. Review each subsystem against its source/build identity, tests, qualification boundaries and release gates before declaring a public release.
- **README:** local `main` contains the reconciled CPU evidence at `9fe2cee`; a further unstaged README edit in the working tree describes the candidate and is not part of either compared commit. Once the publication strategy is selected, review its clone command against the actual public default and run the scoped documentation checks.
- **Public branches:** the two newcomer branches are ancestors of `master`; the archive and research branch are ancestors of local `main`. The southbridge candidate has three commits beyond `master` and is a separate unqualified hardware review. Keep it separate. These observations do not authorize deletion.

No synthesis, full regression, physical test, release approval, push, branch creation, deletion or default change occurred in this review.

## Public-only paths (31)

- `docs/INA226_SESSION_HANDOFF.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-07-28.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-01.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-03.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-04-EVENING.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-04.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-08.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-09.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-10.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-11.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-12.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-13.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-14.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-15.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-16.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-17.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-18.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-20.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-24.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-08-26.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-09-04.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-09-05.md`
- `docs/archive/handovers/SESSION_HANDOVER_2026-09-06.md`
- `docs/archive/legacy/PUBLICATION_STRATEGY_INDEX.md`
- `docs/archive/legacy/SPU13_MARKET_AND_GRANT_POSITIONING.md`
- `docs/archive/legacy/commercialization_and_development_roadmap.md`
- `docs/archive/legacy/public_site_and_outreach_plan.md`
- `docs/archive/legacy/publication_and_promotion_strategy.md`
- `docs/archive/legacy/publication_roadmap_12week.txt`
- `docs/archive/legacy/strategic_roadmap.md`
- `software/vm/spu_vm`

## Changed shared paths (114)

Grouped by directory to support review. Each entry means the blob differs; it is not a finding that either side is correct.

### hardware (24)

- `hardware/boards/artix7/build_a7.sh`
- `hardware/boards/artix7/spu_a7_gpu_vga_top.v`
- `hardware/boards/artix7/spu_a7_vga.xdc`
- `hardware/boards/artix7/spu_a7_vga_fix.xdc`
- `hardware/boards/artix7/synth_a7_gpu_vga.ys`
- `hardware/boards/artix7/synth_a7_gpu_vga_t1d.ys`
- `hardware/boards/tang_primer_25k/spu13_tang25k_gpu_framebuffer_readout_probe.v`
- `hardware/boards/tang_primer_25k/spu13_tang25k_spu4_som_edge_interactive_probe.v`
- `hardware/boards/tang_primer_25k/tang_primer_25k.cst`
- `hardware/docs/coupon_quick_reference.md`
- `hardware/pcb/bench_adapter/bench_adapter_spec.md`
- `hardware/rp2350/CMakeLists.txt`
- `hardware/rp2350/rp2350_su3_j11_smoke.c`
- `hardware/rtl/core/spu13/fpga_chain_arith.vh`
- `hardware/rtl/core/spu13/rplu_pipeline.v`
- `hardware/rtl/core/spu13/spu13_core.v`
- `hardware/rtl/core/spu13/spu_som_bmu.v`
- `hardware/rtl/core/spu4/spu4_som_edge.v`
- `hardware/rtl/core/spu4/spu4_som_edge_wrapper.v`
- `hardware/rtl/gpu/spu_depth_dispatch4.v`
- `hardware/rtl/gpu/spu_gpu_top.v`
- `hardware/rtl/gpu/spu_prepared_scalar_attribute4.v`
- `hardware/rtl/gpu/spu_scene_loader.v`
- `hardware/tests/spu4/spu4_som_edge_interactive_probe_tb.v`

### software (35)

- `software/common/include/spu_lithic_l.h`
- `software/common/include/spu_quadray.h`
- `software/common/tests/spu_lithic_l_test.cpp`
- `software/common/tests/spu_quadray_test.cpp`
- `software/graphics/README.md`
- `software/lib/ina226_capture.py`
- `software/programs/call_demo.sas`
- `software/programs/delta_demo.sas`
- `software/programs/hw_test.sas`
- `software/programs/isa_test.sas`
- `software/programs/laminar_vs_cubic.sas`
- `software/programs/pell_orbit_demo.sas`
- `software/programs/robot_arm_demo.sas`
- `software/programs/ve_orbit.sas`
- `software/programs/ve_proof.sas`
- `software/programs/wildberger_calculus.sas`
- `software/programs/wildberger_chromogeometry.sas`
- `software/programs/wildberger_geometry.sas`
- `software/programs/wildberger_higher_dim.sas`
- `software/programs/wildberger_layer2.sas`
- `software/programs/wildberger_spread.sas`
- `software/spu_gpu_eval/__init__.py`
- `software/spu_gpu_eval/cli.py`
- `software/spu_vm.py`
- `software/spu_vm_test.py`
- `software/tests/test_detached_job_runner.py`
- `software/tests/test_gpu_scene_compiler_s1.py`
- `software/tests/test_gpu_t1e_prepared_scene_oracle.py`
- `software/tests/test_gpu_t1g_pacing.py`
- `software/tests/test_gpu_t1i_uv.py`
- `software/tests/test_gpu_top_integration.py`
- `software/tests/test_ina226_capture.py`
- `software/tools/spu13_asm.py`
- `software/vm/Makefile`
- `software/vm/spu_vm.cpp`

### docs (34)

- `docs/ABOUT.md`
- `docs/BENCH_BOM.md`
- `docs/BENCH_ELECTRICAL_SAFETY.md`
- `docs/CAPABILITY_MATRIX.md`
- `docs/COMPARATIVE_GRAPHICS_LAB.md`
- `docs/CURRENT_STATUS.md`
- `docs/DEMO_TOUR.md`
- `docs/DETACHED_JOB_RUNNER.md`
- `docs/FIRST_HOUR.md`
- `docs/INA226_CAPTURE_RUNBOOK.md`
- `docs/LUCAS_QUICKSTART.md`
- `docs/NEWCOMER_SOFTWARE_QUICKSTART.md`
- `docs/NEWCOMER_TOUR.md`
- `docs/README.md`
- `docs/REPOSITORY_MAP.md`
- `docs/ROTC_KINEMATICS_PAPER.md`
- `docs/SOM_SIDECAR_QUICKSTART.md`
- `docs/SPARSE_JET_MAC.md`
- `docs/SPU4_ABI.md`
- `docs/SPU4_INA226_BENCHMARK_2026-09-08.md`
- `docs/START_HERE.md`
- `docs/TENSEGRITYLINK_FOUR_ACT_CAMPAIGN.md`
- `docs/ZPHI_KARATSUBA_INTEGRATION_PLAN.md`
- `docs/archive/ecp5/COLORLIGHT_I9_PINOUT_VERIFIED.md`
- `docs/build_and_bringup_guide.md`
- `docs/gpu_scene_preview.md`
- `docs/hardware_evidence.md`
- `docs/index.md`
- `docs/isa/ISA_IMPLEMENTATION_MATRIX.md`
- `docs/isa/ISA_PROFILE_PROVENANCE.md`
- `docs/papers/SU3_EXTENSION_PLAN.md`
- `docs/papers/SU3_PAPER_OUTLINE.md`
- `docs/software_guide.md`
- `docs/som_temporal_classification.md`

### knowledge (4)

- `knowledge/ISA_QUICKSTART.md`
- `knowledge/SPU13_ARCHITECTURE.md`
- `knowledge/SYNERGETICS_BEYOND_GEOMETRY.md`
- `knowledge/isa_reference.md`

### tools (7)

- `tools/bench_metrics/ina226_logger_v2.py`
- `tools/bench_metrics/power_log.py`
- `tools/generate_pade_66_q16.py`
- `tools/ina226_capture_pipeline.py`
- `tools/lucas_demo.py`
- `tools/robotics_demo.py`
- `tools/run_detached_job_worker.sh`

### root and other (10)

- `.gitignore`
- `AGENTS.md`
- `CLAUDE.md`
- `CONTRIBUTING.md`
- `LICENSING.md`
- `README.md`
- `examples/02_quadray_orbit/quadray_orbit.sas`
- `mkdocs.yml`
- `pyproject.toml`
- `run_all_tests.py`
