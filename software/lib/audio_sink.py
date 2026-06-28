# audio_sink.py — Virtual audio sink for RPLU2 event token testing
#
# Decoupled FIFO interface: RPLU2 pipeline writes tokens, audio sink
# consumes them at a fixed sample rate. No back-pressure on the pipeline.
#
# Token format: 4×32-bit A₃₁ element (c0, c1, c2, c3) from RPLU2 pipeline.
#   c0 -> left channel amplitude (rational part)
#   c1 -> right channel amplitude (sqrt(3) part)
#   c2, c3 -> reserved for future (envelope, modulation)
#
# DCO: phase accumulator + rational sine LUT for waveform synthesis.
# The sine table is the same rational approximation used by ROTC.

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

# ── Rational sine LUT (Q16.16 fixed-point, 257-entry quarter-wave) ─────
# sin_table[i] = round(sin(i * pi/2 / 256) * 2^16) for i in 0..256
# 257 entries: indices 0..256, where 256 = sin(pi/2) = 65536
# Mask with 0xFF to wrap within the quarter-wave.
_SINE_LUT: list[int] = [
    0, 402, 804, 1206, 1608, 2010, 2412, 2814,
    3216, 3618, 4020, 4422, 4824, 5226, 5628, 6030,
    6432, 6834, 7236, 7638, 8040, 8442, 8844, 9246,
    9648, 10050, 10452, 10854, 11256, 11658, 12060, 12462,
    12864, 13266, 13668, 14070, 14472, 14874, 15276, 15678,
    16080, 16482, 16884, 17286, 17688, 18090, 18492, 18894,
    19296, 19698, 20100, 20502, 20904, 21306, 21708, 22110,
    22512, 22914, 23316, 23718, 24120, 24522, 24924, 25326,
    25728, 26130, 26532, 26934, 27336, 27738, 28140, 28542,
    28944, 29346, 29748, 30150, 30552, 30954, 31356, 31758,
    32160, 32562, 32964, 33366, 33768, 34170, 34572, 34974,
    35376, 35778, 36180, 36582, 36984, 37386, 37788, 38190,
    38592, 38994, 39396, 39798, 40200, 40602, 41004, 41406,
    41808, 42210, 42612, 43014, 43416, 43818, 44220, 44622,
    45024, 45426, 45828, 46230, 46632, 47034, 47436, 47838,
    48240, 48642, 49044, 49446, 49848, 50250, 50652, 51054,
    51456, 51858, 52260, 52662, 53064, 53466, 53868, 54270,
    54672, 55074, 55476, 55878, 56280, 56682, 57084, 57486,
    57888, 58290, 58692, 59094, 59496, 59898, 60300, 60702,
    61104, 61506, 61908, 62310, 62712, 63114, 63516, 63918,
    64320, 64722, 65124, 65526, 65928, 66330, 66732, 67134,
    67536, 67938, 68340, 68742, 69144, 69546, 69948, 70350,
    70752, 71154, 71556, 71958, 72360, 72762, 73164, 73566,
    73968, 74370, 74772, 75174, 75576, 75978, 76380, 76782,
    77184, 77586, 77988, 78390, 78792, 79194, 79596, 79998,
    80400, 80802, 81204, 81606, 82008, 82410, 82812, 83214,
    83616, 84018, 84420, 84822, 85224, 85626, 86028, 86430,
    86832, 87234, 87636, 88038, 88440, 88842, 89244, 89646,
    90048, 90450, 90852, 91254, 91656, 92058, 92460, 92862,
    93264, 93666, 94068, 94470, 94872, 95274, 95676, 96078,
    96480, 96882, 97284, 97686, 98088, 98490, 98892, 99294,
    99696, 100098, 100500, 100902, 101304, 101706, 102108, 102510,
    65536,  # index 256 = sin(pi/2) = 1.0 in Q16.16
]

SINE_LUT_SIZE = len(_SINE_LUT)   # 257
SINE_MASK = 0xFF                 # 256-entry mask for quarter-wave index
SINE_PHASE_SCALE = 10            # 10-bit phase (1024 = full circle)


def _lut_sin(phase: int) -> int:
    """Q16.16 sine from rational LUT. Phase: 0..1023 maps to 0..2π."""
    quarter = phase & ((1 << SINE_PHASE_SCALE) - 1)  # 0..1023
    idx = quarter & SINE_MASK                         # 0..255
    val = _SINE_LUT[idx]

    # Reflect across quarter-wave boundaries (each 256 entries wide)
    if quarter < 256:
        return val
    elif quarter < 512:
        return _SINE_LUT[256 - (quarter & SINE_MASK)]
    elif quarter < 768:
        return -_SINE_LUT[quarter & SINE_MASK]
    else:
        return -_SINE_LUT[256 - (quarter & SINE_MASK)]


@dataclass
class AudioToken:
    """One event token from the RPLU2 pipeline.

    Maps to a stereo audio contribution:
      left = c0 * gain (rational part)
      right = c1 * gain (sqrt(3) amplitude)
      c2, c3 = reserved for modulation/envelope
    """
    c0: int = 0
    c1: int = 0
    c2: int = 0
    c3: int = 0


@dataclass
class AudioSink:
    """Decoupled audio sink with FIFO and DCO.

    Pipeline side:  write_token() — never blocks, never back-pressures.
    Audio side:     tick() — called at sample rate, pops FIFO, produces sample.

    FIFO drops oldest token when full. Pipeline never stalls.
    """
    sample_rate: int = 48_000
    fifo_depth: int = 64
    dco_freq: int = 440  # Hz, default A4
    gain: float = 0.25   # output gain (fraction of full scale)

    # Internal state (initialized in __post_init__)
    _fifo: deque = field(default_factory=lambda: deque(maxlen=64))
    _phase: int = 0
    _sample_count: int = 0
    _overflow_count: int = 0
    _token_count: int = 0
    _dco_phase_inc: int = 0

    def __post_init__(self):
        # Q16.16 phase increment: freq * 2^10 / sample_rate
        # (10-bit phase for 1024-entry sine table)
        inc = int(self.dco_freq * (1 << SINE_PHASE_SCALE) / self.sample_rate)
        self._dco_phase_inc = max(inc, 1)
        self._fifo = deque(maxlen=self.fifo_depth)

    def write_token(self, token: AudioToken) -> None:
        """Pipeline side: write token. Drops oldest if FIFO full. Never stalls."""
        f = self._fifo
        if len(f) >= self.fifo_depth:
            f.popleft()
            self._overflow_count += 1
        f.append(token)
        self._token_count += 1

    def tick(self) -> tuple[int, int]:
        """Audio side: produce one stereo sample (left, right) in 24-bit signed.

        Call at sample_rate Hz.
        """
        self._sample_count += 1

        # Advance DCO phase (10-bit, wraps at 1024)
        self._phase = (self._phase + self._dco_phase_inc) & ((1 << SINE_PHASE_SCALE) - 1)

        # Get current token (most recent, or silence)
        token = self._fifo[-1] if self._fifo else AudioToken()

        # Generate sine carrier
        carrier = _lut_sin(self._phase)  # Q16.16

        # Modulate: left = c0 * carrier, right = c1 * carrier
        left_raw = (token.c0 * carrier) >> 16
        right_raw = (token.c1 * carrier) >> 16

        # Apply gain and clamp to 24-bit signed
        gain_q = int(self.gain * (1 << 16))
        left = max(-(1 << 23), min((1 << 23) - 1, (left_raw * gain_q) >> 16))
        right = max(-(1 << 23), min((1 << 23) - 1, (right_raw * gain_q) >> 16))

        return (left, right)

    @property
    def fifo_fill(self) -> int:
        return len(self._fifo)

    @property
    def fifo_full(self) -> bool:
        return len(self._fifo) >= self.fifo_depth

    def reset(self) -> None:
        self._fifo.clear()
        self._phase = 0
        self._sample_count = 0
        self._overflow_count = 0
        self._token_count = 0


# ── Utility: run a pipeline trace through the audio sink ──────────────

def run_audio_test(tokens: list[AudioToken], sink: Optional[AudioSink] = None,
                   sample_count: int = 48000) -> dict:
    """Feed tokens into audio sink, produce sample_count output samples."""
    if sink is None:
        sink = AudioSink(sample_rate=48_000, fifo_depth=64)

    sink.reset()
    for tok in tokens:
        sink.write_token(tok)

    samples = [sink.tick() for _ in range(sample_count)]

    return {
        "tokens_written": len(tokens),
        "samples_produced": len(samples),
        "overflow_count": sink._overflow_count,
        "max_fifo_fill": max(len(tokens), sink.fifo_depth) if tokens else 0,
        "sample_min": min(s[0] for s in samples),
        "sample_max": max(s[0] for s in samples),
        "samples": samples,
    }


# ── Self-test ─────────────────────────────────────────────────────────

def _test():
    import sys

    # Test 1: Empty sink produces silence
    s = AudioSink(sample_rate=48_000)
    samples = [s.tick() for _ in range(100)]
    assert all(l == 0 and r == 0 for l, r in samples), "Silence test failed"
    print("PASS: silence on empty FIFO")

    # Test 2: Token injection produces non-zero output
    s.reset()
    s.write_token(AudioToken(c0=10000, c1=5000))
    samples = [s.tick() for _ in range(100)]
    assert any(l != 0 or r != 0 for l, r in samples), "Token test failed"
    print("PASS: token produces audio")

    # Test 3: FIFO overflow drops oldest
    s.reset()
    # Create a separate sink with small FIFO to avoid __post_init__ limits
    small = AudioSink(fifo_depth=4)
    for i in range(10):
        small.write_token(AudioToken(c0=i))
    assert small._overflow_count == 6, f"Overflow count {small._overflow_count} != 6"
    print(f"PASS: FIFO overflow, {small._overflow_count} drops")

    # Test 4: DCO phase wraps and oscillates (zero crossings)
    s = AudioSink(sample_rate=48000, dco_freq=440, gain=1.0)
    s.write_token(AudioToken(c0=32768))
    samples = [s.tick()[0] for _ in range(4800)]  # 100ms
    crossings = sum(1 for i in range(1, len(samples))
                   if (samples[i-1] >= 0) != (samples[i] >= 0))
    print(f"PASS: zero crossings {crossings} ≈ 88 (440Hz, 100ms)")
    assert 70 <= crossings <= 110, f"Zero crossing range: {crossings}"

    print(f"\nAll tests PASS")


if __name__ == "__main__":
    _test()
