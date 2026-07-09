# Cartesian Bridge — Sensor/Legacy Boundary Contract v0

Contract before code, per house convention (`docs/SPARSE_JET_MAC.md`,
`docs/WHISPER_V1_SPEC.md`). This is the boundary component identified in
`spu_strategy/killer_app_wedge_strategy.md` as shared infrastructure for
every industrial killer-app wedge: the point where a real sensor's
IEEE-754/Cartesian reading crosses into SPU's exact rational field, and
where a classification result crosses back out to a legacy consumer that
has no notion of Q(√3).

## 1. The one claim this document exists to make precise

SPU's "no floating-point drift" property holds **inside** the field.
The moment a real sensor value crosses the boundary, it is quantized —
and quantization is not an approximation error to apologize for, it is
a **stated, tested, bounded rounding contract**. Past this document,
"exact" means "deterministic and bounded," not "lossless." Every
consumer of bridge output must know which one applies where.

## 2. Ingest: float → RationalSurd

**Representation:** a raw scalar sensor channel (vibration amplitude,
current, temperature — one physical quantity, no inherent √3 geometric
content) quantizes to a RationalSurd with **Q = 0** — a pure rational
point, `P/scale`. Multi-channel feature vectors are built as one
RationalSurd per channel, matching `software/lib/rational_som.py`'s
`find_bmu(features: Sequence[RationalSurd], ...)` input shape directly —
no adapter needed beyond the per-channel quantization.

**Quantization rule:** fixed-point, `P = round_half_even(value * scale)`,
clamped to the hardware's signed 16-bit bound `[-32768, 32767]` (the
packed `RationalSurd` P/Q width, per `CLAUDE.md`). Round-half-to-even
(Python's native `round()`, IEEE 754's default) — chosen so repeated
midpoint values don't accumulate a systematic bias in one direction,
which matters for long-running monitors.

**Scale is per-channel, not universal.** Different physical quantities
have wildly different natural ranges (temperature in °C: 0–150 typical
industrial; vibration in g: 0–16; current in A: 0–2 for the bench
INA226). The contract does not pick one default scale — the deployment
states its scale per channel, same as the SQR rotor convention already
uses Q12 (scale 4096) for a ±8.0 range. Getting this wrong (too coarse a
scale) silently degrades classification quality without any error being
raised — it is a deployment-time engineering decision, documented per
sensor, not a library default.

**Saturation, never silent loss:** a value outside the representable
range after scaling does **not** raise, and does **not** silently clamp
without telling you — matching the house pattern already used for
whisper's dissonance field (`min(|residual|, 255)`, explicitly documented
as "hard fault, magnitude uninformative" past that point). The ingest
function returns `(value, saturated: bool, error: float)` — `saturated`
signals magnitude information was lost; `error` is the exact rounding
residual `P/scale - value`, always returned, always inspectable. A
crash-on-overflow design would be actively dangerous for an anomaly
monitor: the moment a sensor spikes hardest is the moment you most need
the monitor to keep running.

## 3. Egress: RationalSurd → legacy scalar

**Representation:** `P/scale + (Q/scale)·√3` evaluated in `float` —
this is the one direction where floating point is the correct target,
not a compromise: a legacy PLC/dashboard/ECU expects a float or a small
integer class ID, and has no obligation to understand Quadray algebra.
This value is for **display and consumption only** — it must never be
fed back into the exact pipeline; any correction/retraining loop stays
in the exact domain and only surfaces to floats at the final reporting
step.

**Classification output (SOM-specific egress, scoped for the anomaly
monitor):** `BmuResult` (`rational_som.py`) already carries
`cluster_label`, `confidence_gap` (exact RationalSurd), and
`ambiguous`. The egress side reports the audit-trail value out loud, not
just a bare class ID — the sellable feature *is* "node X won because
Q_x < Q_y, both exact numbers," so the bridge must carry the exact
quadrance values through to the legacy log line, not just the label.
Deferred to the demo application layer, not this contract: which
`cluster_label` value(s) count as "normal" vs. "anomaly" for a given
deployment — that is a per-installation policy decision, not a bridge
concern.

## 4. Interface (v0 scope)

Lives at `software/lib/cartesian_bridge.py` — a Python oracle, same
pattern as every other numerical contract in this repo
(`rational_som.py`, `a31_field.py`), not under `spu_host` (which is the
RP2350 console client, a different, downstream concern). RTL/C++ parity
ports are a later step, only if a sensor pipeline needs to run
ingest/egress in real time on-device rather than on a host PC.

```
quantize_scalar(value: float, scale: int) -> QuantizeResult
    # QuantizeResult(value: RationalSurd, saturated: bool, error: float)
dequantize_scalar(rs: RationalSurd, scale: int) -> float
    # requires rs.q == 0; raises on non-scalar input (caller bug, not data)
dequantize_surd(rs: RationalSurd, scale: int) -> float
    # general form, evaluates the √3 term — display-only, documented above
quantize_feature_vector(values: Sequence[float], scale: int) -> list[QuantizeResult]
    # per-channel convenience; .value list feeds find_bmu() directly
```

## 5. Acceptance checklist (v0)

- [ ] Round-trip: `dequantize_scalar(quantize_scalar(v, s).value, s)`
      within `1/(2s)` of `v` for all in-range `v` (round-half-even error
      bound).
- [ ] Saturation: values beyond `±32767/s` return `saturated=True`,
      clamped to the boundary, never raise, never silently pass through
      unflagged.
- [ ] Q=0 invariant: every `quantize_scalar` output has `q == 0`.
- [ ] `dequantize_scalar` raises on `q != 0` input (catches
      scalar/surd confusion at the call site, not downstream).
- [ ] Round-half-to-even verified at an actual midpoint case (e.g.
      `value * scale` exactly `x.5`), not just generic rounding.
- [ ] `quantize_feature_vector` output is a valid `Sequence[RationalSurd]`
      for `rational_som.find_bmu` with no adapter code — direct type
      compatibility, checked by an actual `find_bmu` call in the test,
      not just shape inspection.

## 6. What this v0 does not cover (explicitly deferred)

- Multi-sensor time synchronization / sampling-rate reconciliation.
- The anomaly-vs-normal policy layer (which `cluster_label`s alert).
- On-device (RTL/C++) ingest — host-side only for now.
- Geometric (non-scalar, Q≠0) sensor fusion — e.g. a true 3-axis
  accelerometer reading treated as a Quadray displacement rather than
  three independent scalar channels. Real, and probably the more
  accurate model for vibration data specifically, but a design decision
  deferred past v0 to keep this contract's first version tight.

*CC0 1.0 Universal, like the rest of `docs/`.*
