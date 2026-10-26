# ICOS-0 registration evidence

Detached run `spu-run1-20261025T230209Z-171379`: `TB_FILTER=zz_no_such_tb python3 run_all_tests.py`
-> COMPLETE, exit 0, 730 s; Total PASS 76 / FAIL 0 (BQ-0 baseline run was 75 / 0, so +1 = test_icosian_e8.py).

* Scope: C++ and Python stages only. **Full Verilog regression NOT RUN; not a full-suite PASS.**
* Run on HEAD 61549dd with a dirty worktree; the working-tree runner contained other uncommitted changes. The committed runner adds only the ICOS-0 run block and the icos_pass/icos_fail totals; no summary-table row exists for it.
* Logs omitted (gitignored `build/`).
* Fast fixture ~11 s; exhaustive `test_icosian_e8_full.py` ~47 s is not registered.
