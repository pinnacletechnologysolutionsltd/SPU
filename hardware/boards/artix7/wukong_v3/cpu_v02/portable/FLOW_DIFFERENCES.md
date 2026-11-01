# CPU-REPRO-1: portable flow vs. the original flow

Original: `provenance/original_flow/` (preserved, unmodified). Portable: this directory. Source, XDC, clock constraints, synthesis flow script
(`tools/vivado/spu_vivado_flow.tcl`), thread cap (`general.maxThreads 2`), implementation steps and `BITSTREAM.*` properties are the same.

| Item | Original | Portable | Effect |
|---|---|---|---|
| Repository root | clone `/home/john/.local/gate/spu-int3b-c3efc18` | derived from script location (6 levels up) | none on design |
| Filelist | `experiment/.../candidate.f` (`cc5a0359…`) | `filelists/candidate_portable.f` (same 22 `sv` entries and order, 5 paths rewritten) | file paths only; `filelist_sha256` in the manifest differs by design |
| Vivado cwd | clone root | `build/cpu-repro-1/<RUN>/work` | keeps `clockInfo.txt`/journals out of the checkout |
| Vivado install | `source /home/john/2026.1/Vivado/settings64.sh` | `$VIVADO_SETTINGS` (required); version 2026.1 and SW build 6511674 enforced | none if the build matches |
| Phase P input | fixed path to golden `synth.dcp`; gated on its sha256 `938f0772…` | `route.tcl` takes the checkpoint as argv1 (the run's own synth.dcp); no hash gate | the only line changed from `route_phase_p.tcl` is `open_checkpoint` |
| Phase 4B input | fixed path to golden `routed.dcp`; gated on `48e0e161…` | `bitstream.tcl` takes argv1 (the run's own routed.dcp); no hash gate | the only line changed from `gen_bitstream.tcl` is `open_checkpoint` |
| Memory guard | `guard.sh` | the same file, sourced from `provenance/original_flow/` | none |
| Launch floor | MemAvailable >= 5 GiB, disk >= 20 GiB | same, in `preflight.sh` | none |
| ROM validation | `rom_check.py` with `build/cpu-board-2r-isolated/board_tb.v` and `frontend.v` | not run; ROM properties and load nets are dumped with the preserved `dump_rom*.tcl` and diffed against the golden dumps | `board_tb.v` is not needed for synthesis or bitstream; it was used only by this post-hoc check |
| Post-build checks | `bit_check.py` | `compare.py` (payload, header, golden-vs-run) | the verdict rests on the `.bin` hash only |
| Output location | `build/vivado/*` in the clone | `build/cpu-repro-1/<RUN>/{synth,route,bit,analysis,meta,work}` | none |
| Phase boundaries | three separate Vivado invocations | the same three invocations | none |

## Expected non-identities (not failures)
- `run_manifest.txt`: `started`, `host`, `git_head`, `git_status_sha256` and `filelist_sha256` differ.
- `.bit` header carries the build date and time (golden: 2026/10/30 17:17:58), so the `.bit` sha256 `442a229e…` is not expected to reproduce. The payload (`.bin`, `cc259988…`) is the bit-exact criterion.
- `.dcp` files embed serialisation metadata; their hashes are informational.
