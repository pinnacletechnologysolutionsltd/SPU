#!/usr/bin/env bash
# Focused T1p Q1 and selector-off T1o through T1i regressions.
set -euo pipefail

python3 software/tests/test_gpu_t1p_predicate_bits.py
python3 software/tests/test_gpu_t1o_per_primitive_material.py
python3 software/tests/test_gpu_t1n_runtime_material.py
python3 software/tests/test_gpu_t1m_fragment_alu.py
python3 software/tests/test_gpu_t1l_material_ops.py
python3 software/tests/test_gpu_t1k_grid.py
python3 software/tests/test_gpu_t1j_checker.py
python3 software/tests/test_gpu_t1j_checker_visibility.py
python3 software/tests/test_gpu_t1i_uv.py
python3 software/tests/test_gpu_top_integration.py

bash -n hardware/boards/artix7/build_a7.sh
python3 -m py_compile software/tests/test_gpu_t1p_predicate_bits.py
git diff --check
