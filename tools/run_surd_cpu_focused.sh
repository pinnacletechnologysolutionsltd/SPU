#!/usr/bin/env bash
set -euo pipefail
focused_out="${1:?existing detached evidence directory required}"
test -d "$focused_out"
sha256sum --check build/spu_surd_register/main_cpu_integration_20261007/implementation_freeze_01/sources.sha256 \
  > "$focused_out/source_guard.log" 2>&1
python3 software/tests/test_spu13_core_surd.py --kernels --output-dir "$focused_out/cpu"
echo 'COMPLETE focused CPU correctness and complete retained kernel campaign'
