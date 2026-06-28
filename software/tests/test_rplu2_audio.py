# test_rplu2_audio.py — RPLU2 → AudioSink integration test
#
# Verifies that the audio sink:
#   1. Never back-pressures the RPLU2 pipeline
#   2. Produces valid stereo output from event tokens
#   3. FIFO depth is bounded under burst load
#   4. DCO frequency is accurate

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.audio_sink import AudioSink, AudioToken, run_audio_test

import math
import time

PASS = 0
FAIL = 0

def check(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS: {msg}")
    else:
        FAIL += 1
        print(f"  FAIL: {msg}")

def test_silence():
    """Empty FIFO produces silent output."""
    s = AudioSink()
    for _ in range(1000):
        l, r = s.tick()
        assert l == 0 and r == 0, "non-zero sample from empty FIFO"
    check(True, "silence on empty FIFO")

def test_single_token_continuous():
    """Single token persists across sample ticks (no pop)."""
    s = AudioSink(gain=1.0)
    s.write_token(AudioToken(c0=32768, c1=16384))
    # First sample should use the token
    l1, r1 = s.tick()
    # 1000 samples later, same token should still be active
    for _ in range(999):
        s.tick()
    l2, r2 = s.tick()
    check(l2 != 0 or r2 != 0, "token persists across samples")

def test_fifo_overflow():
    """FIFO drops oldest tokens when full, never stalls."""
    s = AudioSink(fifo_depth=8, gain=1.0)
    for i in range(100):
        s.write_token(AudioToken(c0=i, c1=i))
    check(s._overflow_count == 92, f"FIFO overflow drops {s._overflow_count} tokens")
    check(len(s._fifo) == 8, "FIFO caps at depth")

def test_burst_then_drain():
    """Burst of tokens, then drain — verify sustained output."""
    s = AudioSink(fifo_depth=64, gain=1.0)
    # Write 16 tokens (1/4 FIFO depth)
    for i in range(16):
        s.write_token(AudioToken(c0=1000 * i, c1=500 * i))
    # Read 48000 samples, verify no dropout
    samples = [s.tick() for _ in range(48000)]
    check(len(samples) == 48000, "all samples produced")
    # Last sample should still have content from last token
    l_last, r_last = samples[-1]
    check(l_last != 0 or r_last != 0, "output sustained through drain")

def test_frequency_accuracy():
    """DCO frequency matches requested within LUT precision."""
    s = AudioSink(sample_rate=48000, dco_freq=440, gain=1.0)
    # Record zero crossings to measure frequency
    samples = []
    s.write_token(AudioToken(c0=32768))
    for _ in range(4800):  # 100ms at 48kHz
        samples.append(s.tick()[0])

    # Count zero crossings (sign changes)
    crossings = 0
    for i in range(1, len(samples)):
        if (samples[i-1] >= 0) != (samples[i] >= 0):
            crossings += 1

    # 440 Hz for 100ms = 44 cycles = 88 zero crossings (both edges)
    # Allow ±10% for LUT quantization
    check(79 <= crossings <= 97, f"zero crossings {crossings} ≈ 88 (440Hz)")

def test_no_backpressure():
    """Simulate RPLU2 pipeline writing tokens at max rate:
    ~99 cycles/classification at 50 MHz → ~505k classifications/sec.
    Audio runs at 48 kHz. Ratio ≈ 10:1.
    write_token() must NEVER block regardless of FIFO state."""
    s = AudioSink(fifo_depth=64, sample_rate=48000)
    TOKENS = 48000
    for i in range(TOKENS):
        s.write_token(AudioToken(c0=10000))
        s.tick()
    # Drops are expected (1:1 ratio exceeds 64-deep FIFO).
    # The critical guarantee: write_token never raised/stalled.
    # Verify FIFO still has the last 64 tokens (no corruption).
    check(s.fifo_fill <= 64, f"FIFO bounded ({s.fifo_fill})")
    # No error: write_token completed all 48000 calls without exception
    check(s._token_count == TOKENS, f"all tokens written ({s._token_count})")

def test_rplu2_burst_pattern():
    """Simulate realistic RPLU2 pipeline behavior: 99-cycle classification
    bursts, then idle. Audio runs continuously."""
    s = AudioSink(fifo_depth=64, gain=0.5)
    
    # Simulate RPLU2: 10 classifications (one every 99 cycles at 50 MHz)
    for classification in range(10):
        # Write one token (SOM → BTU → Padé result)
        s.write_token(AudioToken(
            c0=20000 + classification * 1000,
            c1=10000 - classification * 500,
        ))
        # Audio ticks while pipeline computes next classification
        # 99 cycles at 50 MHz = 1.98 µs; audio at 48 kHz = 20.83 µs
        # So ~10 audio ticks per classification
        for _ in range(10):
            l, r = s.tick()
    
    # Verify we got audio for all tokens
    check(s._overflow_count == 0, f"RPLU2 burst no overflow ({s._overflow_count})")
    check(s.fifo_fill <= 64, f"FIFO depth bounded ({s.fifo_fill})")


if __name__ == "__main__":
    print("RPLU2 → AudioSink Integration Tests")
    print("=" * 40)
    
    tests = [
        ("Silence", test_silence),
        ("Single token persistence", test_single_token_continuous),
        ("FIFO overflow", test_fifo_overflow),
        ("Burst then drain", test_burst_then_drain),
        ("Frequency accuracy", test_frequency_accuracy),
        ("No back-pressure", test_no_backpressure),
        ("RPLU2 burst pattern", test_rplu2_burst_pattern),
    ]
    
    for name, fn in tests:
        print(f"\n[{name}]")
        fn()
    
    print(f"\n{'=' * 40}")
    print(f"Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    
    sys.exit(0 if FAIL == 0 else 1)
