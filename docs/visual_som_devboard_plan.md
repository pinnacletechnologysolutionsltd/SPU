# Visual SOM Development Board Plan

The visual board is a deterministic telemetry surface for SPU-13 bring-up,
debugging, demos, and funding conversations. It must not sit in the hot compute
path. The SPU-13 computes, then emits bounded telemetry frames; an RP2040/RP2350
or host tool renders those frames on a screen.

## Purpose

- Make SOM, RPLU, Davis Gate, rotor, and memory-tier behavior visible without
  a logic analyzer.
- Provide repeatable public demos: same firmware, same input trace, same visual
  map every run.
- Support OSHWA evidence by exposing exact boot and runtime state instead of an
  opaque animation.
- Keep the processor shippable even when no display is attached.

## Architecture

```
SPU-13 / Tang 25K
    |
    | deterministic telemetry frames
    v
RP2040/RP2350 display bridge or host visualizer
    |
    | SPI / parallel RGB / USB CDC / UART
    v
OLED, TFT, LED matrix, or desktop dashboard
```

The first implementation should run on the host from simulator and RTL traces.
The second implementation should run on an RP2040/RP2350 display bridge. The
production board can then route the same telemetry ABI to an onboard display
header or fitted screen.

## Display Views

### 1. SOM Class Map

Hex or rectangular node map showing:

- best matching unit
- second-best unit
- cluster label
- material ID
- confidence gap
- ambiguity flag

Recommended encoding:

- cell hue = cluster/material class
- cell brightness = laminar weight or recent activity
- outline = current BMU
- split outline = second-best unit
- hatch/dim marker = ambiguous match

### 2. RPLU Material Map

Material table state showing:

- active material ID
- loaded material slot count
- RPLU address
- dissociation mask
- Morse flash CRC/checksum
- runtime update activity

This is the public demo view for the pre-flashed periodic table pack.

### 3. Davis Gate / Stability Map

Stability trace showing:

- manifold tension
- Davis pass/fail
- Henosis pulse count
- laminar/turbulent mode
- recovery direction

This view is useful for proving deterministic recovery and for robotics
closed-loop testing.

### 4. Rotor / Kinematics Map

Rotation and kinematic state showing:

- six-step rational rotor phase
- forward/inverse step
- active axis pair
- quadrance error
- inverse-balance flag

This should become the robotics bring-up screen once the rational kinematics
suite is rebuilt.

### 5. Memory Tier Map

Memory placement view showing:

- active sector
- BRAM slot use
- streaming/cold slot use
- Nguyen weight
- tension velocity
- promotion/eviction event

This becomes important when SDRAM hydration is available on the replacement
Tang 25K.

## Visual Telemetry ABI v0

Use a fixed-size binary frame. Keep it small enough for UART during bring-up and
easy to mirror into SPI/USB CDC later.

```
byte  0      magic 0x53       "S"
byte  1      magic 0x56       "V"
byte  2      version          0
byte  3      frame_type
byte  4..7   sequence
byte  8..11  cycle_count
byte 12..13  flags
byte 14..15  payload_len
byte 16..N   payload
last 4       crc32 over header+payload
```

Initial `frame_type` assignments:

| Type | Name | Payload |
|---|---|---|
| 0x01 | SOM_BMU | best, second, label, material, best_q, gap, flags |
| 0x02 | RPLU_STATUS | material, addr, dissoc_mask, loaded_count, checksum |
| 0x03 | DAVIS_STATUS | tension, pass flag, pulse count, mode |
| 0x04 | ROTOR_STATUS | phase, inverse flag, axis pair, quadrance error |
| 0x05 | MEMORY_TIER | sector, bram_slots, streaming_slots, weight, d_tension |

All numeric fields are unsigned or two's-complement integers. No floats are
allowed in the telemetry ABI. Display-only conversion is permitted after the
frame is received.

## Implementation Phases

### Phase 0: Host Replay

- Add a Python renderer that consumes deterministic JSON/CSV output from the VM
  and RTL trace tests.
- Render the SOM map, RPLU material table, and Davis stability view on desktop.
- Use recorded traces as funding/demo assets.

### Phase 1: UART Telemetry Adapter

- Reuse the existing 115200 baud Tang 25K UART proof path.
- Encode the v0 telemetry frames as binary or ASCII-safe hex during early
  bring-up.
- Extend `tools/visualizer.py` to parse and display the frame types.

### Phase 2: RP2040/RP2350 Display Bridge

- Keep the microcontroller as a renderer, not a decision-maker.
- Receive frames over UART/SPI/USB CDC.
- Render to SSD1306, ST7789, or LED matrix.
- Expose raw frames over USB for host logging.

### Phase 3: Production Dev Board

- Add a display connector or fitted display.
- Pre-flash the RPLU periodic pack.
- Provide a boot demo that cycles through SOM, RPLU, Davis, rotor, and memory
  tier maps.
- Publish frame ABI, renderer source, and golden traces as OSHWA evidence.

## Immediate Next Step

Before the replacement Tang 25K arrives, implement Phase 0:

1. Generate deterministic visual frames from existing SOM BMU and ROTC trace
   tests.
2. Add a desktop renderer for the five map views.
3. Save golden trace files under `build/` only, not in the repo.
4. Once SDRAM pins are available, add the memory-tier hydration view.
