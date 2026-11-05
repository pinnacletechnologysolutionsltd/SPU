#!/bin/bash
# IDNT-R1 focused regression: runner-equivalent release benches reaching spu13_core/fpga_chain
# (+ new IDNT bench) against the modified core, then core-simulating Python gates.
set -u
cd "$(dirname "$0")/../.."
export PATH=/home/john/.local/opt/oss-cad-suite-20261027/bin:/usr/local/bin:/usr/bin:/bin
rc=0
/usr/bin/python3 build/idnt-r1/run_benches.py . - build/idnt-r1/regress_list.txt build/idnt-r1/regress-benches || rc=1
for t in test_rotc_vm_rtl_trace.py test_irotc_vm_trace.py test_regen_equivalence.py test_regen_emulator.py test_regen_asm.py; do
  if /usr/bin/python3 software/tests/$t > build/idnt-r1/regress-benches/$t.log 2>&1; then echo "PASS $t"; else echo "FAIL $t"; rc=1; fi
done
exit $rc
