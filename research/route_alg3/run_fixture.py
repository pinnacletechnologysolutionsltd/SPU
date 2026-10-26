"""One bounded fixture route. Usage: run_fixture.py BINARY RUN_ID [POLICY]  (POLICY: fd|fd_shadow|reopen; omit = unset env).
Same argv/inputs as the retained 42-net fixture. Limits: 30 s wall, 4 GiB AS, 16 MiB per file, no core. No retries."""
import json, os, resource, subprocess, sys
from pathlib import Path

B = Path('/home/user/Projects/hardware/SPU/build')
C = B / 'spu_surd_register/backend_compatibility_20261012'
P = C / 'openxc7_serial_route_campaign_repair03_20261017'
argv_src = json.loads((P / 'campaign_01/fixture_route.argv.json').read_text())
binary, run_id = Path(sys.argv[1]).resolve(), sys.argv[2]
policy = sys.argv[3] if len(sys.argv) > 3 else None
out = B / 'route_alg3/runs' / run_id
out.mkdir(parents=True)  # refuses overwrite
argv = list(argv_src)
argv[0] = str(binary)
argv[argv.index('--write') + 1] = str(out / 'routed.json')
argv[argv.index('--fasm') + 1] = str(out / 'fixture.fasm')
env = dict(os.environ, SPU_ROUTE_OUTPUT=str(out), SPU_EXPECTED_ROUTER='router2', SPU_EXPECTED_SEED='1')
env.pop('SPU_ALG3_POLICY', None)
if policy:
    env.update(SPU_ALG3_POLICY=policy, SPU_ALG3_OUT=str(out / 'alg3.jsonl'))

def lim():
    resource.setrlimit(resource.RLIMIT_AS, (4 << 30, 4 << 30))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 << 20, 16 << 20))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

(out / 'argv.json').write_text(json.dumps(dict(argv=argv, policy=policy), indent=1))
with (out / 'native.log').open('w') as log:
    r = subprocess.run(argv, env=env, stdout=log, stderr=subprocess.STDOUT, preexec_fn=lim, timeout=30)
(out / 'exit_status').write_text(f'{r.returncode}\n')
print(run_id, 'exit', r.returncode)
