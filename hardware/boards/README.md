# SPU-13 Board Targets

## Active Boards

| Board | Chip | LUTs | DSP | Role |
|---|---|---|---|---|
| **Artix-7 200T** | XC7A200T | 215K | 740 | Full stack development |
| **Artix-7 100T** | XC7A100T | 101K | 240 | Primary development |
| **Artix-7 35T** | XC7A35T | 33K | 90 | Deployment / field units |
| **Tang Primer 25K** | GW5A-25K | 23K | 56 | Gowin regression |
| **ECP5 25F** | LFE5U-25F | 24K | 56 | Open bitstream validation |
| **iCESugar Pro** | iCE40UP5K | 5K | 0 | Medical sensor node |

## Spins (Artix-7 family)

| Spin | Modules | Use Case | Min Board |
|---|---|---|---|
| `FULL` | MATH + SOM + GPU + RPLU + I2S + Gatekeeper | Development | 100T |
| `MULTIMEDIA` | MATH + GPU + RPLU + I2S + Gatekeeper | Gaming, visualisation | 100T |
| `INTELLIGENCE` | SOM + RPLU + Gatekeeper | Classification, clustering | 35T |
| `ROBOTICS` | MATH + Gatekeeper | Kinematics, avionics | 35T |
| `SENSOR` | MATH only | Medical wearables | 35T / iCE40 |
| `CUSTOM` | Manual ENABLE_* flags | Any | Any |

## Building

```bash
# Artix-7 (primary)
bash hardware/boards/artix7/build_a7.sh 100t full
bash hardware/boards/artix7/build_a7.sh 35t robotics
bash hardware/boards/artix7/build_a7.sh 200t multimedia

# Tang 25K (regression)
bash build_25k_spu13_math_probe.sh

# ECP5 (open validation)
# See hardware/boards/ecp5_25f/

# iCESugar (sensor node)
# See hardware/boards/icesugar/
```

## Archived Boards

Moved to `hardware/boards/archive/`:
- GW1N1 (1K LUTs — too small)
- Tang Nano 9K (8K LUTs — too small)
- Tang Primer 20K (20K LUTs — superseded by 25K)
- Gowin 20K / Mega (voltage issues, aspirational)
