# Artix-7 attempt 3: mapped ordinary-core carry segmentation

**Status:** repair candidate; physical experiment authorized within existing campaign.

Run the focused candidate checks:

```bash
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_06/split_carry.py
timeout 55s python3 build/spu_surd_register/product_placement_repair_20261011/preparation_06/prove_split.py
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_06/test_placement.py
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_06/test_launch.py
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_06/worker.py preflight
```

Submit only after actual candidate packing, segmentation retention, region checks,
proof/negative controls and frozen-input checks pass:

```bash
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_06/launch.py
```

## Evidence and pre-execution review

Attempt 2 routing_03 has one FAILED marker, exit1, 1,566 seconds. SA cooling
completed but relative-constraint legalization failed on the 8-CARRY4 chain rooted
at core `$84264`, mapped from frozen `spu13_core.v:1282` rs_sub64. Routing was not
reached and 25 MHz remains unqualified. Attempt1 failed on a static SCALE2 chain;
its exact folding is retained. One of three authorized 7,200-second slots remains.

The private observer amendment qualification is CLOSED_PASS_PRIVATE_OBSERVER:
17 fixtures and deterministic capture overhead only. It does not establish live
router speedup or authorize tool replacement. Keep the existing observed binary.
The six-replica aligned-decode RTL proposal remains unapplied and outside this
mapped repair; its internal-interface and full qualification gates are separate.

Moving CI to CYINIT alone cannot split the chain: this exact Xilinx packer lowers
both to MUXCY connections and groups them again. Insert LUT1 INIT=2'b10 identity
buffers at every fourth CARRY4 boundary only in the frozen ordinary-core module.
An identity-buffer driver prevents grouping across that boundary. The packer may
add a carry feed-out cell and LUT: record actual counts and resulting group sizes.

## Scope and arithmetic preservation

Start from preparation_05/cpu_folded.json. Validate the frozen 185 core CARRY4
population, acyclic unbranched CO[3]-to-CI chains, empty parameters and zero
CYINIT at every nonroot. Insert precisely 25 LUT1 buffers across 17 long chains.
Rewrite only each boundary cell's CI; preserve all DI/S/O/CO nets, original cells,
ports, attributes, aliases and every other module. All Surd arithmetic modules,
five product lanes, 80 DSPs, REGEN, registers, ISA, retirement and reset stay
unchanged. No RTL edit, resynthesis or precision/latency change is introduced.

Exhaustively prove a nine-cell template with arbitrary DI, S, CI and CYINIT inputs
against the installed Xilinx primitive model, comparing every O and CO bit.
This covers all actual core chain lengths and both possible boundaries. Require
an inverted LUT negative control to fail and invalid graph/parameter controls to
reject before mutation. This establishes local two-state combinational
equivalence, not full CPU sequential or X/Z equivalence.

Packing must retain the boundaries, cover the reported failing chain, preserve
all DSP assignments and report LUT/carry overhead. A segmentation mechanism
that is merged away or produces unexpected long carry groups must halt launch.
No claim of improved placement or routing follows from successful packing.

## Launch and acceptance

Retain SA, seed1, 25 MHz, existing DSP regions, chip database and tool. Freeze
candidate/dependencies/proofs/scripts/packing evidence and refuse changed files,
active FPGA tools, ambiguous earlier markers, failed gates or exhausted budget.
Use final slot of max3, per-attempt7,200s, cumulative21,600s campaign. Prior
recorded tool time is3,063s; those two slots remain consumed. No automatic retry.

Submit through the detached runner into a fresh routing_04 directory. Record unit
and evidence, then end the turn. Require exactly one COMPLETE/FAILED/TIMEOUT
marker before interpreting the attempt. Exit zero still requires separate review
of legal routing, complete required timing coverage and PASS at25 MHz.

Full repository/trace/math/Padé gates remain mandatory before hardware/build-flow
repair qualification closure. This bounded physical candidate experiment is not
closure. No AOR implementation or source change is part of this work.
