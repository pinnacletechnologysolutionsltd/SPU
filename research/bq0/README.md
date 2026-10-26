# BQ-0 registration evidence

Detached run `spu-run1-20261025T215044Z-160522`: `TB_FILTER=zz_no_such_tb python3 run_all_tests.py`
-> COMPLETE, exit 0, 731 s; Total PASS 75 / FAIL 0; "BQ-0 Biquadratic Oracle Tests: 1".

* Scope: C++ and Python stages only. The Verilog stage was filtered out: **full Verilog regression NOT RUN; not a full-suite PASS.**
* Run was on HEAD 0ec1add with a dirty worktree (other uncommitted changes in `run_all_tests.py` and elsewhere were present).
* Full stdout/stderr logs omitted (gitignored `build/`); `summary.txt` has the relevant lines.
* The run used the working-tree runner, which also had the summary-table row `BQ-0 Biquadratic Oracle` (the line in `summary.txt`). That row sits inside a table block that exists only in uncommitted work by others, so it is NOT in the BQ-0 commit; the committed registration is the run block plus the pass/fail totals.
