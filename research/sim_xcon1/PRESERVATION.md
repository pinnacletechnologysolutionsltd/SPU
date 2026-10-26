# SIM-XCON-1 evidence preservation (SIM-XCON-1P)

Date: 2026-10-23. Preserves the single completed SIM-XCON-1 run; nothing was rerun, regenerated or modified. Original evidence stays in the gitignored `build/sim_release0/xcon1/` (retained location of the full run directory, including `run_01/cpp.rgb8`, `run_01/py.rgb8`, the built `spu-sim` and the `git archive c1e0676` source tree).

## Result
Single execution, `TERMINAL` = `terminal_exit=0`, `ALL_PASS` in 18.0 s (deadline 600 s). No other attempt exists.

| Identity | Value |
|---|---|
| spu-sim commit (clean, 0 dirty lines) | `c1e0676eee5d2398b8d90eec43bd55b2d2f6b924` |
| spu-sim executable (built from `git archive c1e0676`) | `32d937aec29248da8c49bbf4a1bb2a8679ff6aa4e14bf2b1565c35584865e754` |
| Wire packet `fixtures/gpu_t1d_scene_wire_64b.bin` | `aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee` |
| Reference JSON | `7c48bdeffac97bba871e5c92663168900cb617f8586976e66f09077e11b7f138` |
| Frozen manifest `manifest.json` | `4c367309dfa7f3d0f36a36739a507f6ba9b2e9260b28616195acef3b6ef27e1f` |
| `freeze.py` / `run_xcon1.py` | `a7c42a9e…4ab5` / `e1a5bf0c…c6a` (see `PRE_RUN_HASHES.txt`) |
| `run_01/result.json` | `e2f76f5d7d4edfa7491386e5eef7d49583125ff13394bc8cf82c59156479f1b8` |
| C++ frame = Python frame (640x480 RGB8, 921,600 B) | `96950fa5610063be28056ab0ff9f198a94bbc38ab9aa48949684592d69de7a10` |

Comparison: C++ and Python frames byte-identical; 29/29 frozen pixels agree with both frames; RTL datapath test (existing `test_gpu_device_model_s2.py` helper, unmodified; generated bench `run_01/rtl_tb.v`, commands `run_01/rtl_commands.json`) printed 29 PIXEL lines and `PASS`, all matching.

## Retained here
Frozen manifest, pre-run hashes, `freeze.py`, `run_xcon1.py`, `pre_research_status.txt` (research-repo `git status` before the run), stdout/stderr/TERMINAL, `run_01/{result.json,rtl_tb.v,rtl_commands.json,build.log}`, and `run_01/frame_640x480.rgb8.gz` (gzip of the frame; decompressed SHA-256 equals the frame hash above). `SHA256SUMS` binds every file here. Raw `cpp.rgb8`/`py.rgb8` (SHA above), the executable and the build tree stay external in `build/`.

## Discarded draft
`manifest_draft1_discarded.json` (SHA-256 `9645d18013e14a79816c23befd01c9df78712101c0da51c107792b29ca6de779`, 21 points) was written 2026-10-23 17:20:45, before the frozen `manifest.json` (17:20:50) and before any comparison or execution. Discarded because its search bounds missed adjacent-outside-edge and near-tie depth cases. It was never run against any frame, so it is not an execution attempt. The `freeze.py` that generated it was overwritten by the revised one and was not kept; the draft file itself is the only record.

## Evidential limits
- C++ vs Python: full-frame byte equality, one scene.
- RTL: selected-pixel **colour** agreement at 29 pixels only; coverage, winner and depth are recorded in the manifest but implied only through the winning colour.
- Expected colours come from the reference JSON (6 pixels) and the Python exact oracle (rest); not an independent third oracle.
- No full-frame RTL equivalence. No current FPGA execution. No SIM-G3 qualification (still INCOMPLETE). No broader GPU qualification.
- The Python model and research inputs were an uncommitted tree; they are pinned by file SHA-256 in the manifest (research HEAD recorded there), not by commit.
- To log RTL output, the runner wrapped the helper's `subprocess.run` (tee only); the helper source was unchanged.
