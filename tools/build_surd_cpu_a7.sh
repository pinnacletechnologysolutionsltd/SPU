#!/usr/bin/env bash
# One declared campaign: matched disabled/enabled core mappings, one enabled P&R.
set -euo pipefail
cpu_out="${1:?existing detached evidence directory required}"
test -d "$cpu_out"
sha256sum --check build/spu_surd_register/main_cpu_integration_20261007/build_repair_freeze_03/sources.sha256 > "$cpu_out/source_guard.log"
source tools/env_openxc7.sh
test -f build/chipdb/xc7a100tfgg676.bin
python3 - "$cpu_out" <<'PY'
from pathlib import Path
import json, sys
out=Path(sys.argv[1])
focused=Path('build/spu_surd_register/main_cpu_integration_20261007/focused_01')
regression=focused.parent/'regression_01'
for prerequisite in (focused,regression):
    markers=[name for name in ('COMPLETE','FAILED','TIMEOUT') if (prerequisite/name).exists()]
    if markers!=['COMPLETE'] or json.loads((prerequisite/'result.json').read_text())['exit_code']!=0:
        raise SystemExit(f'prerequisite has not passed: {prerequisite}')
sources=(focused/'cpu/rtl_source_list.txt').read_text().splitlines()
sources.append('hardware/boards/artix7/spu_a7_surd_cpu_bench_top.v')
(out/'source_list.txt').write_text('\n'.join(sources)+'\n')
for enabled in (0,1):
    # Elaborate only the wrapper's frozen configuration, not default-enabled core branches.
    text='read_verilog -defer -sv -Ihardware/rtl/arch '+ ' '.join(sources)+'\n'
    text+=f'hierarchy -check -top spu_a7_surd_cpu_bench_top -chparam ENABLE_SURD_CPU {enabled}\nproc\nopt\n'
    # The end label is exclusive: include prepare, stop immediately before DSP mapping.
    text+='synth_xilinx -family xc7 -top spu_a7_surd_cpu_bench_top -run begin:map_dsp\n'
    # Skip DSP inference only for REGEN products. map_dsp restores soft products
    # to exact $mul cells before ordinary LUT/carry synthesis; no RTL edits.
    text+='select -assert-any spu13_regen/t:$mul\n'
    text+=f'select -write {out}/cpu_{enabled}.regen_soft_mul.txt spu13_regen/t:$mul\n'
    text+='chtype -set $__soft_mul spu13_regen/t:$mul\n'
    text+='select -clear\n'
    text+='synth_xilinx -family xc7 -top spu_a7_surd_cpu_bench_top -run map_dsp: '
    text+=f'-json {out}/cpu_{enabled}.json\nstat\n'
    (out/f'cpu_{enabled}.ys').write_text(text)
PY
for enabled in 0 1; do
    yosys -Q -s "$cpu_out/cpu_${enabled}.ys" > "$cpu_out/cpu_${enabled}.yosys.log" 2>&1
done
python3 - "$cpu_out" <<'PY'
from pathlib import Path
import json,sys
out=Path(sys.argv[1]); audit={}
for enabled in (0,1):
    design=json.loads((out/f'cpu_{enabled}.json').read_text())
    by_module={name:sum(cell['type']=='DSP48E1' for cell in module['cells'].values())
               for name,module in design['modules'].items()}
    # Retained hierarchy has one instance of each DSP-bearing arithmetic module.
    total=sum(by_module.values())
    audit[str(enabled)]={'dsp_by_module':{n:c for n,c in by_module.items() if c},
                         'dsp_total':total,'regen_dsp':by_module.get('spu13_regen',0)}
(out/'dsp_allocation.json').write_text(json.dumps(audit,indent=2)+'\n')
for enabled in (0,1):
    if audit[str(enabled)]['regen_dsp']!=0:raise SystemExit('REGEN DSP exclusion failed')
if audit['1']['dsp_by_module'].get('surd_cpu_products')!=80:
    raise SystemExit('five-lane Surd DSP allocation changed')
if audit['1']['dsp_total']>240:raise SystemExit('integrated DSP allocation still exceeds 100T')
PY
nextpnr-xilinx --chipdb build/chipdb/xc7a100tfgg676.bin \
  --xdc hardware/boards/artix7/spu_a7_surd_cpu_bench.xdc \
  --json "$cpu_out/cpu_1.json" --write "$cpu_out/cpu_1.pnr.json" \
  --fasm "$cpu_out/cpu_1.fasm" --log "$cpu_out/cpu_1.nextpnr.log" \
  --freq 25 --seed 1 > "$cpu_out/cpu_1.nextpnr.stdout" 2>&1
echo 'COMPLETE integrated canonical CPU mapping and routing, 25 MHz logical target'
