# C++ VM Release Review — 2026-10-15

## Result

The C++ VM passes the checked conformance surface and the documented example
smoke checks on this checkout. This is a release check for the implemented
subset, not a claim of full ISA, Python VM, or RTL parity.

## Reproducible checks

Run from the repository root:

```bash
python3 software/tests/test_isa_conformance.py
python3 software/tests/test_isa_fold_conformance.py
python3 software/tests/test_canonical_control.py
make -B -C software/vm test
./software/vm/spu_vm examples/02_quadray_orbit/quadray_orbit.sas --quiet
./software/vm/spu_vm examples/03_davis_equilibrium/equilibrium.sas --quiet
./software/vm/spu_vm examples/01_scalar_fibonacci/fibonacci.sas --steps 12 --quiet
```

For the packaged Python `spu-sim` identity, a local isolated-target walkthrough
can be repeated with Python 3.11 and pip:

```bash
python3.11 -m pip wheel --no-deps --wheel-dir build/wheel .
python3.11 -m pip install --no-deps --target /tmp/spu-package build/wheel/spu_toolkit-0.2.0-py3-none-any.whl
PYTHONPATH=/tmp/spu-package /tmp/spu-package/bin/spu-sim examples/02_quadray_orbit/quadray_orbit.sas --quiet
PYTHONPATH=/tmp/spu-package /tmp/spu-package/bin/spu-sim examples/03_davis_equilibrium/equilibrium.sas --quiet
```

The conformance, fold, control, and Makefile checks pass. Quadray Orbit and
Davis Equilibrium exit 0 after normal HALT. Fibonacci is an intentional loop:
the final command stops at its instruction budget, reports that it did not
reach HALT, and exits 3. Invalid, missing, zero, negative, and trailing-text
`--steps` arguments are rejected with exit 1. A HALT on the final permitted
step exits 0.

## Clean snapshot walkthrough and command identity

The walkthrough used an isolated snapshot based on commit
`4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`, overlaid with the current
`software/`, `examples/`, `README.md`, `pyproject.toml`,
`docs/software_guide.md`, and this review. This was a reproducible clean
snapshot of the release inputs, not a
claim that the dirty main checkout was itself a clean Git commit. The package
was built with Python 3.11.6 and an isolated setuptools/wheel build environment. The wheel
`spu_toolkit-0.2.0-py3-none-any.whl` built successfully (SHA-256
`4a052b71a8ca10e3d98565a5c916baae889fc7d280ff92b80f91484479b90922`) and is
preserved as the [walkthrough wheel](../../build/spu_surd_register/backend_compatibility_20261012/upstream_report_preparation_20261015/software_wheel/spu_toolkit-0.2.0-py3-none-any.whl).
That exact wheel was installed into an isolated target and exercised. Adding
`wheel` to `[build-system].requires` was necessary for this clean build; the
initial no-isolation check without that dependency failed at `bdist_wheel`.
The wheel was installed with pip's `--target` option, so the walkthrough put
that target on `PYTHONPATH` when invoking its generated `spu-sim` script.

The repository's packaged `spu-sim` entry point resolves to
`spu_vm:main` in `software/spu_vm.py`. It is the legacy Python VM, not the C++
binary. In the isolated package run, Quadray Orbit exited 0 but displayed raw
`RationalSurd` object representations. Davis Equilibrium exited 2 after SNAP
failures. The C++ `software/vm/spu_vm` is a separate implementation: its
Quadray Orbit and Davis Equilibrium runs both halted normally, and its focused
release checks passed. The owner-accepted SIM-1 contract describes a future
separate `spu-sim` repository; that repository is not present in this checkout
and none of these results qualify it.

## Scope and limits

The supported C++ instruction surface is listed in the
[ISA conformance report](ISA_CONFORMANCE_2026-10-10.md). Unsupported instruction
families remain rejected. The report also records semantic differences that
still prevent a full cross-VM parity claim, including scalar arithmetic width
and ROTC coverage. In particular, passing these checks does not qualify the
C++ VM as a general replacement for the Python VM or RTL.

## Reviewed file identities

SHA-256 at review time:

| File | SHA-256 |
| --- | --- |
| `README.md` | `3456d3045960552250a8ad845f817b3498196b0dd51c76a3c43ac26b78e01c94` |
| `pyproject.toml` | `00bfbc4a11c342ea85bf86a28b2630419c96c9b384a70141418d9940feae37e7` |
| `software/spu_vm.py` (Python `spu-sim` implementation) | `89440f2dfe3bc6e32ace60a71103437a11d0a1c1f1c17ab3994a920aef21c859` |
| `software/vm/spu_vm.cpp` | `6da999439615f6652974dbb2522c2902ed676bcf0f5fb872e4a2d7dc4b79a049` |
| `software/vm/Makefile` | `2b377becb67a178d6236495cd1fd4948e9769214372cdfbe63b1fa2602908a74` |
| `software/tests/test_isa_conformance.py` | `7766f6e53d4fd2bf49e34bd94f53f89c4c33e11243905566c0a6e96a1ed0fcff` |
| `examples/01_scalar_fibonacci/fibonacci.sas` | `8bc4d4e0211b9a840d7709565f2cf66fd076f3108a4cd5aca5879f10d5143e23` |
| `examples/02_quadray_orbit/quadray_orbit.sas` | `c8cd65ad0d5e10598f3abdf809930a34d3fa9db999252bd450c0b540e01c8cd6` |
| `examples/03_davis_equilibrium/equilibrium.sas` | `dc15070e46b2ba1d00498c88166a3cdec7382973e120a2cff03f8a03ae8cf5fb` |
| Built `software/vm/spu_vm` | `ac97263b0454ed235175f225285b44fa12d66a9f619f7372c342b23dbb827cff` |
| `spu_toolkit-0.2.0-py3-none-any.whl` | `4a052b71a8ca10e3d98565a5c916baae889fc7d280ff92b80f91484479b90922` |

Examples are software demonstrations only. They provide no FPGA timing,
placement, routing, or silicon evidence. Packet 06 remains independently
qualified for route integrity, with timing qualification on HOLD; see the
[hardware evidence ledger](../hardware_evidence.md#339-packet-06-independent-route-integrity-audit).
