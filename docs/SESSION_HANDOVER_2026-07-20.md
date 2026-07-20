# SPU-13 Session Handover — 2026-07-20

## Stop state

The publication and first proof-first optimization tranches are closed.

- `master` and `origin/master` both point to
  `9c2aa40790144d2852497a0706445b0467cfbd2b`.
- The worktree was clean before this handover was added.
- The last independently reproduced full regression was 173/173, including
  130/130 Verilog testbenches.
- RPLU v0.1 is published as DOI
  [`10.5281/zenodo.21446713`](https://doi.org/10.5281/zenodo.21446713).
- LUCAS v0.1 is published as DOI
  [`10.5281/zenodo.21447441`](https://doi.org/10.5281/zenodo.21447441).
- Both DOI badges are present in the root README.

The live LUCAS PDF is the independently rebuilt artifact from source commit
`f1e4dbf06aa1163cc98005feb063ec8aae7c933a`. Its SHA-256 is:

```text
0d0cce5b52c75419d8f4b1d3ef60f82c174f491f6e623529fc03452e8ed60876
```

Three editable Zenodo metadata cleanups remain for the LUCAS record: replace
the abbreviated hash instruction with the full digest above, split the
comma-separated keyword group into separate keywords, and remove the extra
spaces before `FPGA` in the title. These do not require a new record version.

## First task next session: close the Karatsuba proof gaps

Commit `4f509c5` contains the isolated three-product Z[phi] multiplier
candidate. The production multiplier remains unchanged. Before onboarding or
integration work:

1. Add a second formal width configuration, approximately `X_W=8`, `Y_W=6`,
   so width plumbing is checked beyond the existing reduced proof.
2. Extend the formal harness to prove two back-to-back transactions, including
   the return to idle and recapture of new operands.
3. Re-run both SymbiYosys configurations, the full-width extrema/random RTL
   testbench, and `python3 run_all_tests.py`.
4. Commit the proof-only hardening separately.

Useful restart commands:

```sh
git status --short
git log -5 --oneline --decorate
sby -f hardware/tests/spu13/spu13_zphi_mul_serial_karatsuba_formal.sby
TB_FILTER=zphi_mul_serial_karatsuba python3 run_all_tests.py
python3 run_all_tests.py
```

Do not swap the candidate into `spu13_zphi_mul_serial.v` yet. Integration-shaped
place-and-route comparison, downstream tensegrity regressions, and board proof
remain gates for the later RPLU v0.2/tower tranche.

## Second task while components ship: onboarding tranche

Curate the existing project rather than adding another engine:

1. `docs/FIRST_HOUR.md`: clone, full regression, hardware-free VM example,
   one small Forge program, and an optional Tang SOM section; include expected
   output for every command.
2. `docs/QUADRAY_FOR_PROGRAMMERS.md`: teach the four-axis representation,
   normalization, one exact rotation, and the reason exactness is preserved.
3. `docs/DEMO_TOUR.md`: one command and one honest claim boundary each for
   robotics zero drift, LUCAS exact arithmetic, Iris SOM classification, and
   the Voronoi explainer.
4. Link all three from the README and the `docs/index.md` new-user path.

Acceptance is a fresh anonymous clone in which every documented command runs
verbatim and nothing before the optional board section requires hardware.

## Bench procurement and hardware-day order

The immediate purchase should support the existing coarse
normal/load/stall-current experiment:

- INA226 breakout; confirm the fitted shunt value before interpreting current;
- solderless breadboard/prototyping wire kit;
- 3.3 V-compatible logic analyzer;
- SN74CBTLV3125 and TLV3011B interlock parts;
- 100-ohm series resistors for bench SPI lines;
- a small, safely powered repeatable load such as a fan or motor, if one is not
  already available.

When the parts arrive, prove the power-safe interlock transitions first. Do
not connect independently powered 3.3 V rails and do not leave a southbridge
powered and driving an unpowered FPGA. Then verify the INA226 identity, shunt,
cadence, and logger schema before collecting labelled normal/load/stall
sessions. Freeze capture hashes and physical-session splits before scoring.
Only replay a model in FPGA after the software truth gate passes.

Neither a new ECP5 nor Kintex-7 board gates this work. Choose ECP5 when the next
objective is an open-toolchain, portable reference design; choose Kintex-7
when the objective is the larger full-stack image and additional arithmetic
capacity. Review the exact board, I/O voltage, programmer support, stock, and
current price before ordering either.

## Explicitly parked

- production Karatsuba swap and integration P&R;
- A31 tower multiplier/inverter schedule audit and machine-searched schedules;
- RPLU v0.2 claim update;
- high-rate bearing diagnosis;
- custom bench PCB fabrication;
- autonomous tensegrity proposal/actuation control.

The sensor capture is the decisive next product experiment. Until hardware
arrives, proof hardening and first-hour onboarding are the highest-leverage
tasks that do not consume that experiment's evidence budget.
