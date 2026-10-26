# Attempt 2: fold static SCALE2 carry primitives

Check the frozen candidate before submission:

```bash
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_05/test_launch.py
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_05/test_placement.py
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_05/worker.py preflight
python3 tools/doc_audit.py --actual-pass 243
git diff --check -- spu_strategy/contract_surd_placer_carry_repair_2026-10-11.md
```

Launch the next serialized slot:

```bash
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_05/launch.py
```

## Reviewed defect and minimal correction

Attempt 1 has a unique FAILED marker, exit 1, duration 1,497 seconds. SA completed its cooling loop but failed relative-constraint legalization on the chain rooted at `cpu.$auto$alumacc.cc:512:replace_alu$84216.genblk1.slice[0].genblk1.carry4$split$muxcy0$PACKED_CARRY4$`. The mapped synthesis log traces it to the lower D component's 32-bit SCALE2 doubling expression in frozen `spu13_core.v:1576`. This identifies the failed chain, not a proven congestion cause.

The eight 32-bit halves of the SCALE2 operation contain 64 CARRY4 primitives with S=0000 and CYINIT=0. All eight roots have CI=0; the remaining CI inputs are previous CO[3] outputs. For this static form the installed primitive model gives CO=DI and O={DI[2:0],CI}. These primitives implement wires, although packing turns them into relative-placement chains.

Generate `preparation_05/cpu_folded.json` from the original frozen mapped CPU with `fold_carry.py`. Eliminate precisely these 64 cells and substitute their exact, transitively resolved net aliases throughout surviving connections, module port bits and netname bits. Check exact membership, types, empty parameters, widths, constants, chain structure, unique output drivers and absence of data feedback. Preserve every surviving cell's nonconnection properties and all other modules. Leave the unrelated 65th zero-propagate core primitive untouched.

No RTL, ISA, operand widths, state, retirement, reset, clocks, five-lane Surd arithmetic or REGEN expressions change. SCALE2 still doubles each 32-bit half independently; carry never crosses a half boundary. DSP count remains 80. Keep the prior SA placer, regions, seed 1, tool and 25 MHz constraints unchanged.

## Evidence required before launch

`mapped_carry_proof_02` contains a SAT proof of the entire eight-cell chain against `/opt/oss-cad-suite/share/yosys/xilinx/cells_sim.v`, covering 32 independent data bits plus arbitrary root carry. That domain is stronger than each actual chain's tied-zero root and possible data aliases. The same template applies independently to all eight structurally checked chains. The proof checks every CO and O bit; a deliberately poisoned candidate must fail. A nonzero propagate input must be rejected by the rewrite guard.

This is two-state combinational equivalence of the affected primitive network, not full-CPU sequential equivalence or unknown/high-impedance simulation parity. The source RTL is not rewritten. Retain `rewrite.json`, original/candidate hashes, model hash, proof/poison fixtures, commands and logs. The earlier eight-cell prototype and pack check remain separately recorded; only the reviewed 64-cell candidate is submitted.

Require `packed_preflight_07` PASS on the actual revised CPU, including unchanged functional topology across region application and all 80 DSP memberships. Before routing, recheck topology and actual DSP placement, as in the existing campaign. Freeze the candidate, dependencies, scripts, preflight and proofs in `preparation_05/inputs.json`. Refuse changed inputs, active FPGA tools, ambiguous prior results, failed preflight or exhausted allocation.

## Budget and acceptance

Use slot 2 of the owner-authorized three-attempt campaign: 7,200 seconds per attempt, 21,600 seconds cumulative. Attempt 1 is consumed. No timeout extension, new allocation or automatic retry is introduced. Evidence for this launch is `routing_03`; preserve prior attempts and serialize execution.

After LAUNCHED record unit/evidence and end the agent turn. Interpret exactly one COMPLETE, FAILED or TIMEOUT marker. Only independent review of legal routing, complete required timing coverage and PASS at 25 MHz can establish timing acceptance. No fit, timing or silicon result is inferred from a local primitive proof or successful packing. Before closing any qualified hardware/build-flow repair, apply the full AGENTS.md gates under the applicable budget; this launch is an experimental candidate, not qualification closure.
