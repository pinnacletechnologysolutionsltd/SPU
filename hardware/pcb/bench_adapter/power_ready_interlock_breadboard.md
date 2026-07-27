# J2 Power-Ready Interlock — Breadboard Prototype

This is the mandatory pre-PCB experiment for the bench adapter Rev B.  It
proves that a powered Pico cannot energise an unpowered FPGA I/O bank through
the SPI cable.

**Part revision (2026-07-27) — U2 reverts to the original TLV3011B.**
Sourcing moved from DigiKey to LCSC, where `TLV3011B` is available, so U2 is
back to the part this circuit was designed around. This is a revert, not a
new substitution, and it is the preferred configuration: see the hysteresis
section below — MAX9063 offered no escape hatch if its fixed internal
hysteresis proved too narrow at bring-up step 1, whereas TLV3011B's inputs
are externally accessible and its feedback path can be sized on the bench.

Order `TLV3011BIDBVR` (SOT-23, **6-pin**) in preference to `TLV3011BIDCKR`
(SC70-6) — easier to hand-solder and 6-pin SOT-23 breakout adapters are far
easier to find. Note the adapter is **SOT-23-6**, not the SOT-23-5 the
MAX9063 route needed. TLV3011 is not offered in a DIP package; any "DIP8"
listing is a pre-mounted breakout module, which is fine for breadboarding,
or a mislabelled listing — confirm before ordering.

**Two same-family traps, both of which silently invert or break the safety
behaviour:**

- **TLV3011 vs TLV3012.** TLV3011 is open-drain; TLV3012 is push-pull. This
  circuit requires open-drain to pull `J2_OE_N` low. Confirm the "11".
- **MAX9062 vs MAX9063** (applies only if the MAX9063 fallback below is
  used). Despite being the same family and package, MAX9062 has the
  *opposite* input polarity from what this circuit needs (datasheet Table 1:
  it asserts its output low when the sense input is *below* threshold, which
  would enable the switch exactly when the target is unpowered).

**Part substitution note (2026-07-21), retained as the fallback path:** the
originally specified SN74CBTLV3125PW and TLV3011BIDBVR were hard to source.
SN74CBTLV3125PW is listed **Obsolete** at DigiKey, which explains the
difficulty; U1 therefore stays on the 74CBTLV3125PGG second source. If
TLV3011B becomes unobtainable again, `MAX9063EUK+T` (SOT-23-5) remains a
valid U2 with a **different divider** — see the fallback values below.

## Circuit

Use one **74CBTLV3125PGG** (U1, Renesas/IDT — pin- and function-compatible
second source for the obsolete SN74CBTLV3125PW). It is a four-channel
bidirectional switch with independent active-low enables and powered-off
(`Ioff`) isolation. Join all four `OE#` pins as `J2_OE_N`. Its `A` ports face
the Pico; its `B` ports face J2/target. Put the existing 100 Ω resistors
between Pico GPIO and U1 A ports. Do not omit the common ground.

Power U1 from the Pico's regulated 3.3 V. Pull `J2_OE_N` to Pico 3.3 V with
10 kΩ. Thus U1 is *off* by default, including while the target is absent.

Use **TLV3011BIDBVR** (U2, TI — open-drain output, integrated **1.242 V**
reference) powered from Pico 3.3 V and ground. Feed J2-6
(`TARGET_3V3_SENSE`) through **137 kΩ** to the comparator sense node and use
**100 kΩ** from that node to ground:

```
100k / (137k + 100k) x 2.94 V = 1.2405 V   (matches the 1.242 V reference)
```

giving the ~2.94 V trip point at J2-6. Unlike MAX9063's fixed internal
polarity, TLV3011B's IN+/IN- are externally accessible, so **the polarity is
set by your wiring** — wire it so the open-drain output pulls `J2_OE_N` low
only when the sense voltage is *above* the threshold. Getting this backwards
enables the switch exactly when the target is unpowered, which is the failure
this whole circuit exists to prevent. **Verify the logic polarity on the
bench before connecting U1** (bring-up step 1).

*Fallback divider if U2 is MAX9063EUK+T instead:* its reference is **0.2 V**,
so the lower leg becomes **10 kΩ** rather than 100 kΩ — 10k/(137k+10k) x
2.94 V ~= 0.200 V, same trip point. Its polarity is fixed internally
(asserts low when `VIN > 0.2 V`), so there is no wiring choice to make.

**External hysteresis tuning is available on TLV3011B** — this is the main
reason to prefer it. Its noninverting input is externally accessible, so the
1 MΩ-class feedback resistor from output back to the reference/input node can
be added to widen hysteresis if bring-up step 1 shows chatter near the
threshold. Size it from the measured chatter band rather than fitting a value
in advance.

*If the MAX9063 fallback is used instead, this escape hatch does not exist.*
Its datasheet states the noninverting input needed for that feedback network
isn't externally accessible, so you get its fixed internal hysteresis only
(~±0.9 mV at the sense pin, roughly ±13 mV reflected at the 2.94 V threshold
through the divider). Bring-up step 1 must then confirm that is wide enough,
with no remedy available if it isn't.

The comparator is powered locally by the Pico, and its target-voltage input
relies on TLV3011B's fail-safe-input property (inputs stay high-impedance and
safe even with VCC or REF at 0 V; the MAX9060–9064 family provides the
equivalent across -0.3 V to +5.5 V independent of supply). **No target 3.3 V
rail is permitted to connect directly to Pico 3.3 V.**

## Bring-up order

1. Build and test U2 alone. With its target-sense input at 0 V,
   `J2_OE_N` must be Pico 3.3 V. Increase a current-limited bench source at
   the sense input and verify it falls only near 2.94 V.
2. Add U1 with no FPGA connected. Confirm all channels are open below the
   threshold and conduct above it.
3. Attach an unpowered target header. Drive CS#/SCK/MOSI continuously from
   the Pico. With a temporary 10 kΩ pull-down on each target-side line,
   verify the target 3.3 V rail remains at 0 V and no target-side signal
   exceeds 100 mV.
4. Power the target normally; verify U1 enables, then run the 2 MHz
   southbridge smoke test.
5. Power down the target while leaving the Pico active. The switch must
   disable before any target-side signal is driven. Repeat with Pico
   unpowered and the target powered.

Do not use a breadboard result as permission to omit the 100 Ω resistors or
the normal operating rule: never deliberately connect a powered driver to an
unpowered target.  The interlock is the second line of defence.
