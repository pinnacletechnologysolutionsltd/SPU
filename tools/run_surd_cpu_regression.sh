#!/usr/bin/env bash
set -euo pipefail
regression_out="${1:?existing detached evidence directory required}"
test -d "$regression_out"
sha256sum --check build/spu_surd_register/main_cpu_integration_20261007/implementation_freeze_01/sources.sha256
bash tools/verify_repo.sh
TB_FILTER=surd_register python3 run_all_tests.py
TB_FILTER=spu13_core_surd_tb python3 run_all_tests.py
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py
A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all
echo 'COMPLETE required CPU Surd regression and post-change Padé build'
