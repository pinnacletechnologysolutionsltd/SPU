# Geometry layer for v0.3 (experimental)

`spu_geom.py` lets you write exact geometry in Python and compile it to a native v0.3 `programmable-surd` image. It sits on the
mathematical IR (`spu_ir.py`) and the v0.3 backend (`spu_v03_backend.py`). There is no parser and no new language.
Software verification only: the generated programs have run on the oracle and the C++ simulator, **not on hardware**.

## Example

```python
import sys; sys.path[:0] = ['software/sdk', 'software/tests']
import spu_geom as G

g = G.Geometry()
A = g.point((0, 1, 1), 1)            # (sqrt3, 1): a value is an int or an (a, b, d) tuple meaning (a + b*sqrt3)/d
B = g.point(2, (0, 2, 1))            # (2, 2*sqrt3)
g.result(G.quadrance(A, B))          # exactly one result
c = g.compile()
print(c.words, c.exact, c.prediction.rs, c.prediction.result)   # 26, 20 - 8*sqrt3, False, (20, -8, 1)
open('build/quadrance.spui', 'wb').write(c.image)               # then: python3 software/sdk/spu.py run ... --backend sim
```

`compile()` returns `asm` (source text), `image` (an SPUI image), `words`, `instructions`, `prediction` and `exact`.
This image is byte-identical to `software/sdk/examples/quadrance/`.

## What you can write
| Syntax | Meaning |
|---|---|
| `x + y`, `x - y`, `x * y` | one IR operation each, created in Python evaluation order |
| `x ** 2` | one multiplication of `x` by itself. Only the exponent 2 is accepted |
| `-x` | `0 - x`: one constant and one `SSUB` (which can refuse for -2^63) |
| `x + 1`, `2 * x` | ints become constants at the point of use |
| `g.const(a, b, d)` | the value (a + b*sqrt3)/d |
| `G.quadrance(A, B)` | `dx = bx-ax`, `dy = by-ay`, `dx**2 + dy**2` |
| `G.orientation(A, B, C)` | `bx-ax`, `cx-ax`, `by-ay`, `cy-ay`, then `u*v - w*z`. The sign is the orientation |
| `G.triple_quad(q1, q2, q3)` | `s = (q1+q2)+q3`, then `s**2 - 2*((q1**2+q2**2)+q3**2)` |
| `G.triple_quad_points(A, B, C)` | triple-quad of the three edge quadrances |

The operation order of these functions is part of their definition. Nothing is rewritten, merged or simplified, so
`(x + y) - y` stays two operations. To control the order in which constants are loaded, give `point()` raw ints or tuples,
not `Num`s built before the call: in `g.point(2, g.const(0, 2))` the `g.const(0, 2)` argument is created *before* `point()` creates the constant for `2`, so the loads come out in a different order.

## Refusal is visible, not hidden
A `SMUL`, `SADD` or `SSUB` that cannot hold its exact result in 64-bit fields **refuses**: the destination keeps its old value,
the run still ends with `HALT`, and the program's own epilogue sets `S7 = 2` and `RS = 1`. `compile()` replays the generated
instructions and reports this before you run anything:

- `c.prediction.rs`: `True` if any operation would refuse. Then `c.prediction.result` is **not** the answer.
- `c.exact`: the unbounded mathematical value (exact mode). It is not a machine result.

Two mathematically equal expressions can behave differently. The triple-quad expression refuses on some inputs where
`4 * D**2` (D = `orientation`) succeeds, although both are exactly equal. See `software/tests/test_spu_sdk_triple_quad.py`.
The layer does not choose between them for you.

## Limits
- Every coordinate is a constant in the image. v0.3 has no runtime inputs and no data memory, so a new input is a new image.
- Value registers are S0-S6 (S7 is the program's status). Constants are reloaded when registers run out; computed values are
  not, so more than 7 live computed values fail to compile.
- At most 256 words per image (`LOADT` costs 7 words, `SLIK` 1).
- The result must land in S0. There is no move instruction.
- The stale value left after a refusal is not guaranteed to match between allocation strategies. Do not rely on it.
- Only Q(sqrt3). No division, conjugation or comparison of two values.

## Check a result
```sh
python3 software/tests/test_spu_sdk_geom.py        # this layer, against the oracle, the simulator and an exact reference
python3 software/sdk/spu.py verify IMAGE.spui --spu-vm build/sdk/spu_vm
```
