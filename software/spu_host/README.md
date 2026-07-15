# spu_host — Python client for the Southbridge console

Wraps the RP2350/RP2040 diagnostic console
(`hardware/rp_common/spu_diag.c`) so a bench PC (or any Python-capable
host) can drive an SPU board over USB CDC without hand-rolling serial
line parsing. Written once against the console grammar; per the
homogeneity contract in `knowledge/INTERCONNECT_ARCHITECTURE.md` §2, it
works unmodified against any board the southbridge firmware targets.

## Install

```bash
pip install pyserial   # already in requirements.txt
```

No package install step yet — import directly from the repo:

```python
import sys
sys.path.insert(0, "path/to/SPU")
from software.spu_host import SPUHostClient
```

## Usage

```python
import serial
from software.spu_host import SPUHostClient

ser = serial.Serial("/dev/ttyACM0", 115200, timeout=0.05)
client = SPUHostClient(ser)
client.connect()          # drains the startup banner

print(client.status())    # {'raw': b'...', 'lfi': 13, 'flags': 165, ...}
print(client.manifold())  # 32 raw bytes (4 axes x RationalSurd P,Q)
print(client.qr_commit()) # {'valid': True, 'lane': 3, 'A': ..., ...}

client.write_chord(0x0A00000000000000)          # QLDI-style instruction
client.write_rplu_cfg(sel=3, material=5, addr=15, data=0xDEADBEEF)
client.load_tensegrity_sd("/TGR/06_fault_not_in_equilibrium.tgr", vector_id=6)
print(client.tensegrity_status())
```

## CLI

```bash
python3 -m software.spu_host --port /dev/ttyACM0 status
python3 -m software.spu_host --port /dev/ttyACM0 raw sdhydrate
```

## Method <-> opcode map

| Method | Opcode | Protocol doc section |
|---|---|---|
| `status()` | `0xAC` | Status |
| `manifold()` | `0xA0` | Manifold Burst |
| `scale_table()` | `0xAD` | Scale Table |
| `qr_commit()` | `0xAE` | QR Commit |
| `hex_projection()` | `0xAF` | HEX Projection |
| `rplu_config_telemetry()` | `0xB0` | see discrepancy note below |
| `write_chord(data)` | `0xB1` | Instruction Write |
| `load_tensegrity_sd(path, vector_id)` | `0xB2` | Transactional TGR1 Load |
| `tensegrity_status()` | `0xB3` | TGR1 Verdict + Loader Diagnostics |
| `write_rplu_cfg(sel, material, addr, data)` | `0xA5` | RPLU Config Write |

`raw(cmd)` is the escape hatch for firmware-specific console commands not
part of the typed binary protocol (`ping`, `hydrate`, `classify`,
`result`, `sd*`, `somwrite`, `featwrite`) — those vary by probe build.

**Known discrepancy:** `0xB0` is documented in
`docs/SOUTHBRIDGE_SPI_PROTOCOL.md` as "Sentinel Telemetry" (8 satellite
nodes), but the firmware that actually exercises it today decodes RPLU2
config-write telemetry instead (`magic=SPUC`, write-record echo,
checksum). `rplu_config_telemetry()` follows the firmware that runs
today; see the protocol doc's 0xB0 section for the open resolution item.

## Testing

`software/tests/test_spu_host_parser.py` exercises the response parser
against canned byte streams shaped exactly like real firmware output — no
hardware required, wired into `run_all_tests.py`.

## Design notes

- The console is a **text/line protocol** layered by the firmware over
  the binary SPI opcodes — this library speaks that text grammar, not
  raw SPI framing (which lives entirely on the MCU side).
- The only reliable end-of-response marker is the bare `> ` prompt (no
  trailing newline); `console.py` accumulates bytes until it sees one.
- Every typed method raises `SPUProtocolError` on an `ERR` response or an
  unparseable reply, rather than returning `None`/partial data.

CC0 1.0 Universal.
