# SPU / Wukong wiring example

This board-specific example accompanies the [generic interface](README.md).
It is not a universal PMOD cable standard.

## Physical cable and firmware profile

| Signal | A1 Pico GPIO / physical pin | Adapter J2 | This Wukong J11 / FPGA ball |
|---|---|---|---|
| CS# | GP17 / 22 | 1 | 7 / J4 |
| MOSI | GP19 / 25 | 2 | 9 / B4 |
| MISO | GP16 / 21 | 3 | 10 / B5 |
| SCK | GP18 / 24 | 4 | 8 / G4 |
| GND | All digital ground pads | 5 | 11 |
| Target bank 3.3V | **Never Pico pin 36** | 6 | 12, provisional pending rail verification |

J2 is a 1x6 2.54mm male header. The cable is mapped, **not straight-through**
to Wukong or Tang. Confirm pin 1 and viewing orientation physically.
A1 pin 33 (AGND) is unused on this carrier; analog circuitry is not connected.
VBUS, VSYS, 3V3_EN, RUN, ADC_VREF and unused GPIOs are explicitly NC.
The module remains powered by its own USB connector.

The GP16–19 profile matches
[the full-size Pico firmware](../../rp2350/rp2350_su3_j11_smoke.c), which sets
CPOL=0/CPHA=0. It differs from older RP2350-Zero GP0–3 wiring; use a matching
firmware build. The live source currently requests 25kHz; historical 2MHz
operation does not qualify this new circuit at 2MHz.
The remapped target balls follow
[the current Artix constraints](../../boards/artix7/spu_a7_100t.xdc).
Do not reuse this unit's damaged J11 upper-row pins.


## Schematic source update

The manufacturer's [V02 schematic](https://github.com/DavidJRichards/QMTECH_XC7A100T_Wukong_Board/blob/main/Documents/QMTECH-XC7A100T_200T-Wukong-Board-V02-20210426.pdf), inspected on 2026-11-05, shows J11-6/12 and Bank 35 VCCO on the same 3V3 net. Its U5 is a TPS563201; that component rating does not establish spare peripheral current. Confirm the physical board revision and continuity before using this mapping. Earlier review notes predate this schematic inspection.
