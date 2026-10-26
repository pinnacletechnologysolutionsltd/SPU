# Draft README blocks — for John to edit, 2026-08-10

Two blocks, drafted after the os8088 / HN discussion. **Not applied to
`README.md`.** Edit freely — block A especially is your voice, and how you
characterise the split is your call, not mine.

Context for why these are worded as they are: the os8088 thread did not turn on
*using* AI. It turned on a README saying "Everything here is hand-written" while
the contributor list included CLAUDE. Once that one claim was shown false,
commenters stopped believing the hardware photographs too. The defence is not
prose — it is (1) saying it plainly before anyone asks, and (2) pointing at
things a reader can check without trusting either of us.

Placement: **A** after the badges, before "Start here". **B** replaces the
existing "Quick Start (30 seconds to proof)".

---

## Block A — disclosure

```markdown
## How this was built

SPU-13 is designed, specified and directed by John Curley. Much of the RTL,
tooling and documentation was **written with AI assistance** — principally
Claude — under a contract-and-audit process. Commits containing AI-assisted work
carry a `Co-Authored-By:` trailer in the git history.

Nothing here is claimed to be hand-written.

What is the author's: the architecture and the mathematics — exact arithmetic
over `Q(√3)`, `A₃₁` and `Z[φ]/L_p`, the Davis Gate as an exact zero test rather
than an epsilon comparison, Fibonacci-gated dispatch — and the rule below.

**The oracle is normative.** Correctness here is not decided by reviewing
generated code. It is decided by bit-exact agreement between the RTL and an
independent software implementation, checked by a testbench gate that must pass
100% before anything merges. If the RTL and the oracle disagree, the RTL is
wrong. That rule is what makes AI-written hardware checkable at all, and it is
the reason this repository can show you results instead of asking you to trust
its authorship.

Two consequences you can verify rather than take on faith:

- **Hardware claims cite their evidence.** Any statement that something was
  observed on physical hardware cites a section of
  [`docs/hardware_evidence.md`](hardware_evidence.md) — date, build and
  load commands, bitstream SHA-256, raw captured proof lines. Claims that have
  no such section are labelled `[NO ENTRY]` in place rather than quietly
  asserted. There are currently seven.
- **Negative results stay published.** Failed hypotheses, retracted
  conclusions and measurements that did not go our way are kept in the record,
  not deleted. See `AGENTS.md` for the standing example.
```

---

## Block B — check it yourself

```markdown
## Check it yourself (no trust required)

Every command below runs from a fresh anonymous clone and either prints the
stated number or does not.

```bash
# 1. Full regression — RTL testbenches, C++ and Python oracles
python3 run_all_tests.py                          # 188/188, 0 FAIL

# 2. The RTL is checked against an independent oracle, not against review.
#    These six [4/4] Padé vectors were derived from software/lib/a31_field.py
#    and are re-derivable from it; the bench drives them through the RTL and
#    compares all four A₃₁ result lanes exactly, in both pipeline modes.
TB_FILTER=rplu_thimble python3 run_all_tests.py   # Verilog Tests: 2, Passed: 2
                                                  # (both pipeline modes)
cat hardware/tests/spu13/pade_eval_vectors.mem    # the vectors, in plain hex

#    run_all_tests.py reports pass/fail, not per-check counts. To see the
#    bench's own tally, run it directly:
iverilog -g2012 -y hardware/rtl/gpu -y hardware/rtl/core/spu13 \
    -y hardware/rtl/core/shared -y hardware/rtl/math -y hardware/rtl/common \
    -I hardware/rtl/arch -s rplu_thimble_pade_tb \
    -o build/thimble.vvp hardware/tests/spu13/rplu_thimble_pade_tb.v
vvp build/thimble.vvp                             # PASS: rplu_thimble_pade_tb (33/33)

# 3. Software oracles, independently
python3 software/tests/test_rational_robotics.py  # PASS (104 checks)
python3 software/tests/test_lucas_mac_oracle.py   # COMPOSITE ZERO-DRIFT: PASS
                                                  # 166666 identity macros,
                                                  # 999996 primitive ops
python3 software/tests/test_rotc_vm_rtl_trace.py  # VM/RTL trace equivalence

# 4. The product path, end to end
python3 tools/som_sensor_replay.py                # SENSOR_REPLAY: PASS
                                                  # windows=18 exact=18/18
                                                  # ambiguous=0, plus dataset
                                                  # and map SHA-256
```

**What you cannot check from a clone, and why.** Bitstreams are build artifacts
and are not committed; `build/` is gitignored. Silicon results are therefore
recorded rather than reproduced here — each one in
[`docs/hardware_evidence.md`](hardware_evidence.md) pins its bitstream by
SHA-256 and byte count and includes the raw captured output, so a claim can be
matched against a specific image rather than a description of one. Reproducing
them needs the board.

**A note on counts.** `run_all_tests.py`'s summary counts *benches and
variants*, not individual checks — a bench that goes from 8 to 33 internal
checks does not move the headline. `TB_FILTER` filters only the Verilog benches;
the C++ and Python suites run regardless. Read the per-bench lines, not just the
total.

**Read one entry to judge the rest.** §3.2e.7 is the standard the others are
held to: a hash-pinned bitstream, ten runs rather than one, an internal positive
control (the float64 arm must diverge, and does, at step 79 in every run), and
an explicit statement of what it does *not* establish.
```

---

## Verification of Block B, 2026-08-10

Every command above was run from a **fresh clone** of this repo at `2ecf1c0`
(not the working tree — the 2026-07-19 blocker was fresh-clone-only and a
working-tree run cannot see it). Results:

| Claim | Status |
|---|---|
| `188/188, 0 FAIL` | verified, fresh clone |
| `Verilog Tests: 2, Passed: 2` | verified |
| `33/33`, both pipeline modes | verified — but **not visible from the runner**, see below |
| six `[4/4]` vectors, plain hex | verified — 6 records present |
| `PASS (104 checks)` | verified verbatim |
| LUCAS zero-drift | verified — 999996 ops, not "1M"; wording corrected |
| ROTC trace equivalence | verified — prints `angles 0-35`, not 0-11 |
| `SENSOR_REPLAY: PASS windows=18 exact=18/18 ambiguous=0` | verified verbatim, both SHA-256s present |

**One claim in the first draft was false and is now fixed.** It said each bench
"prints 33/33 in its own output above the summary." It does not:
`run_all_tests.py:437-450` captures each bench's stdout and discards it on pass,
printing only `[name] PASSED`; full output appears only on FAIL. A reader
following that instruction would have seen nothing and concluded the number was
invented. Replaced with the direct `iverilog`/`vvp` command, which does print it.

Worth noticing that this is the exact failure mode the block exists to prevent,
found inside the block itself — which is an argument for running every command
in a "check it yourself" section before publishing it, rather than writing it
from knowledge of what the tests do.

**Optional, your call:** `run_all_tests.py` could take a `VERBOSE=1` env var to
echo bench stdout on pass, which would make the simpler original wording true
and help anyone auditing any bench. That touches the regression gate, so I have
not done it.

## Also fix while you are in there

`README.md` line ~121 currently reads:

    python3 run_all_tests.py                  # 173/173 at this revision

**It is 188/188 at HEAD** (2026-08-10). A stale count in the most-read file is
the cheapest possible thing for a skeptic to catch, and it costs more than it
looks — it is the same shape as the os8088 "hand-written" line: a small
verifiable statement that turns out not to match, which then licenses doubt
about everything larger.

Consider dropping "at this revision" and pinning to a date instead, or writing
the assertion so it cannot go stale: *"prints `Total PASS:` with zero
failures."*
