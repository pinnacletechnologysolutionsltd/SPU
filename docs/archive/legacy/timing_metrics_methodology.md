# Timing Metrics Methodology

This project uses claim levels so white-paper tables do not mix simulation,
synthesis, routed timing, and physical bench evidence.

## Claim Levels

| Claim level | Required evidence | Allowed wording |
|---|---|---|
| Oracle/simulation | Python oracle or RTL testbench pass | "simulation-verified" |
| Synthesized | Yosys or vendor synthesis completes with resource report | "synthesizes to N resources" |
| Post-route | nextpnr/Vivado/Gowin P&R completes with timing report | "post-route fmax is X MHz" |
| Packed bitstream | Bitstream/package step completes | "bitstream generated" |
| Bench-verified | FPGA loaded and observed over UART/SPI/logic analyzer | "verified in silicon/on FPGA" |

Sub-20 ns or sub-100 ns claims require post-route timing. Bench claims require
the post-route report plus the board observation log.

## Metrics Artifacts

The canonical generated artifacts live under `build/metrics/`:

- `*.json` is the machine-readable source for tables.
- `*.md` is the paper/editor-friendly summary.
- The summary always links back to the raw nextpnr report and log.

Generate metrics from an existing nextpnr report:

```bash
python3 tools/collect_fpga_metrics.py \
  --name tang25k_lucas_mac_probe \
  --board "Tang Primer 25K" \
  --device GW5A-LV25MG121NES \
  --toolchain "Yosys + nextpnr-himbaechel + gowin_pack" \
  --top spu13_tang25k_lucas_mac_probe \
  --report build/spu13_lucas_mac_probe_timing_report.json \
  --log build/spu13_lucas_mac_probe_nextpnr.log \
  --out-json build/metrics/tang25k_lucas_mac_probe.json \
  --out-md build/metrics/tang25k_lucas_mac_probe.md
```

The Tang Lucas fast-path build runs this automatically:

```bash
bash build_25k_spu13_lucas_mac_probe.sh
```

The Tang PHSLK microprobe does the same for the cross-multiply coherence
primitive:

```bash
bash build_25k_spu13_lucas_phslk_probe.sh
```

The Artix-7 wrapper emits equivalent artifacts after P&R when the OpenXC7
environment is available:

```bash
A7_FREQ=2 bash hardware/boards/artix7/build_a7.sh 100t lucas pnr
```

## Citation Rules

- Cite fmax and critical-path delay from the `Fmax` and `Critical Paths`
  sections of the generated Markdown.
- For Gowin resource tables, prefer the `Console Utilization` values when
  matching nextpnr's printed device-utilization table. Keep `Utilization`
  available as the JSON report view.
- If a result is `FAST_ONLY=1`, state the covered operations explicitly.
  For example, the Tang Lucas probe covers PSCALE/PCHIRAL and PSCALE
  zero-drift, not PMUL/PINV/PHSLK silicon.
- Cite PHSLK timing only from the PHSLK-specific post-route artifact. The
  current Tang 25K microprobe is valid for post-route timing/resource claims,
  not for full-sidecar or bench-verified claims.
