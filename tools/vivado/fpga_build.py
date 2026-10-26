#!/usr/bin/env python3
"""Small detached Vivado build launcher for exploratory SPU FPGA work."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
VIVADO_DEFAULT = 'vivado'
FILELIST_DEFAULT = Path('spu_strategy/rclk1_b2_xsim/rclk1_b2_physical_sources_proposed.f')
XDC_DEFAULT = Path('spu_strategy/rclk1_b2_xsim/spu_a7_tensegrity_link_b2_proposed.xdc')
TOP_DEFAULT = 'rclk1_b2_candidate_top'
PART_DEFAULT = 'xc7a100tfgg676-1'
MEMORY_MAX = 5 * 1024**3
SWAP_MAX = 4 * 1024**3
PREFLIGHT_SWAP_FREE_MIN = 4 * 1024**3
PREFLIGHT_SWAP_USED_MAX = 4 * 1024**3
DEFAULT_TIMEOUT = {'synth': 900, 'route': 2700, 'report': 300, 'all': 2700}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    temp.replace(path)


def source_inputs(filelist: Path, xdc: Path) -> list[Path]:
    paths = [filelist, xdc, ROOT / 'tools/vivado/fpga_build.tcl']
    include_dirs: list[Path] = []
    for number, raw in enumerate(filelist.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        fields = line.split()
        if fields[0] in {'sv', 'verilog', 'incdir'} and len(fields) == 2:
            candidate = ROOT / fields[1]
            if not candidate.exists():
                raise FileNotFoundError(f'{filelist}:{number}: missing {candidate}')
            if fields[0] == 'incdir':
                include_dirs.append(candidate)
            else:
                paths.append(candidate)
        elif fields[0] != 'define':
            raise ValueError(f'{filelist}:{number}: unsupported file-list row')
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)

    # Hash headers actually pulled in by RTL, recursively, rather than treating
    # an include directory or the old handoff's manifest as a source identity.
    headers: set[Path] = set()
    pending = [p for p in paths if p.suffix.lower() in {'.v', '.sv'}]
    include_re = re.compile(r'^\s*`include\s+["<]([^">]+)[">]')
    while pending:
        source = pending.pop()
        try:
            lines = source.read_text(errors='replace').splitlines()
        except OSError:
            continue
        for line in lines:
            match = include_re.match(line)
            if not match:
                continue
            name = match.group(1)
            candidates = [source.parent / name, *(d / name for d in include_dirs)]
            found = next((p.resolve() for p in candidates if p.is_file()), None)
            if found is None:
                raise FileNotFoundError(f'{source}: included file not found: {name}')
            if found not in headers:
                headers.add(found)
                pending.append(found)
    return paths + sorted(headers)


def cgroup_dir() -> Path | None:
    try:
        line = next(row for row in Path('/proc/self/cgroup').read_text().splitlines()
                    if row.startswith('0::'))
        return Path('/sys/fs/cgroup') / line.split('::', 1)[1].lstrip('/')
    except (OSError, StopIteration):
        return None


def verify_cgroup() -> tuple[Path, dict]:
    path = cgroup_dir()
    if path is None:
        raise RuntimeError('kernel cgroup v2 membership unavailable; build not launched')
    observed = {}
    for filename, expected in (('memory.max', MEMORY_MAX), ('memory.swap.max', SWAP_MAX)):
        value = int((path / filename).read_text().strip())
        observed[filename] = value
        if value != expected:
            raise RuntimeError(f'{filename} is {value}, expected {expected}; build not launched')
    return path, observed


def cgroup_usage(path: Path | None) -> dict:
    if path is None:
        return {}
    result = {}
    for filename, key in (('memory.peak', 'memory_peak_bytes'),
                          ('memory.swap.peak', 'swap_peak_bytes'),
                          ('memory.events', 'memory_events')):
        try:
            raw = (path / filename).read_text().strip()
            if filename == 'memory.events':
                result[key] = {k: int(v) for k, v in (line.split() for line in raw.splitlines())}
            else:
                result[key] = int(raw)
        except (OSError, ValueError):
            continue
    return result


def git_value(*args: str) -> str:
    proc = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else 'unavailable'


def host_preflight() -> dict:
    values = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, value, *_ = line.split()
        if key in {'MemAvailable:', 'SwapTotal:', 'SwapFree:'}:
            values[key[:-1]] = int(value) * 1024
    available = values.get('MemAvailable', 0)
    swap_free = values.get('SwapFree', 0)
    swap_used = values.get('SwapTotal', 0) - swap_free
    if available < int(4.5 * 1024**3):
        raise RuntimeError('preflight MemAvailable is below 4.5 GiB')
    if swap_free < PREFLIGHT_SWAP_FREE_MIN or swap_used > PREFLIGHT_SWAP_USED_MAX:
        raise RuntimeError('preflight swap does not meet 4 GiB free / 4 GiB used limits')
    manager = subprocess.run(['systemctl', '--user', 'show-environment'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if manager.returncode:
        raise RuntimeError('user systemd manager unavailable: ' + manager.stderr.strip())
    active = []
    for proc in Path('/proc').glob('[0-9]*/comm'):
        try:
            if proc.read_text().strip().lower() == 'vivado':
                active.append(proc.parent.name)
        except OSError:
            pass
    if active:
        raise RuntimeError('another Vivado process is active: ' + ', '.join(active))
    return {'mem_available_bytes': available, 'swap_free_bytes': swap_free,
            'swap_used_bytes': swap_used, 'user_systemd': 'available',
            'existing_vivado_pids': active}


def report_inventory(out: Path) -> dict:
    def display(path: Path) -> str:
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)
    reports = []
    for path in sorted(out.glob('*.rpt')):
        reports.append({'path': display(path), 'sha256': sha(path)})
    return {
        'reports': reports,
        'timing_reports': [r for r in reports if 'timing' in Path(r['path']).name],
        'utilization_reports': [r for r in reports if 'utilization' in Path(r['path']).name],
        'checkpoints': [{'path': display(p), 'sha256': sha(p)}
                        for p in sorted(out.glob('*.dcp'))],
    }


def output_artifacts(out: Path) -> list[dict]:
    names = ('vivado.log', 'vivado.jou', 'vivado.stdout.log', 'vivado.stderr.log', 'COMPLETE', 'FAILED')
    result = []
    for name in names:
        path = out / name
        if not path.is_file():
            continue
        try:
            shown = str(path.relative_to(ROOT))
        except ValueError:
            shown = str(path)
        result.append({'path': shown, 'sha256': sha(path)})
    return result


def run_worker(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    out = run_dir / 'output'
    out.mkdir(parents=True, exist_ok=False)
    filelist = ROOT / args.filelist
    xdc = ROOT / args.xdc
    inputs = source_inputs(filelist, xdc)
    if args.stage in {'route', 'report'}:
        checkpoint = Path(args.checkpoint).resolve()
        if not checkpoint.is_file():
            raise FileNotFoundError(f'checkpoint not found: {checkpoint}')
        input_hashes = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
        input_hashes[str(checkpoint)] = sha(checkpoint)
    else:
        checkpoint = None
        input_hashes = {str(p.relative_to(ROOT)): sha(p) for p in inputs}

    version = subprocess.run([args.vivado, '-version'], capture_output=True, text=True, timeout=20)
    if version.returncode:
        raise RuntimeError(f'Vivado version query failed ({version.returncode}): {version.stderr.strip()}')
    cgroup, limits = (None, {}) if args.smoke else verify_cgroup()
    manifest_path = run_dir / 'manifest.json'
    start_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    manifest = {
        'format': 'SPU_FPGA_BUILD_MANIFEST_V1', 'run_id': run_dir.name,
        'stage': args.stage, 'status': 'RUNNING', 'exit_code': None,
        'started_utc': start_utc, 'ended_utc': None,
        'source_revision': git_value('rev-parse', 'HEAD'),
        'worktree_status': git_value('status', '--short'),
        'vivado_version': version.stdout.strip(), 'vivado_executable': args.vivado,
        'top': args.top, 'part': args.part, 'filelist': args.filelist,
        'xdc': args.xdc, 'input_sha256': input_hashes,
        'resource_limits_bytes': {'memory_max': MEMORY_MAX, 'swap_max': SWAP_MAX},
        'cgroup_limits_readback_bytes': limits,
        'timeout_seconds': args.timeout, 'command': [], 'output_directory': str(out),
        'limitations': ['exploratory build; no qualification evaluator or timing verdict is applied'],
    }
    argv = [args.vivado, '-mode', 'batch', '-log', str(out / 'vivado.log'),
            '-journal', str(out / 'vivado.jou'), '-source', str(ROOT / 'tools/vivado/fpga_build.tcl'),
            '-tclargs', '-mode', args.stage, '-top', args.top, '-part', args.part,
            '-outdir', str(out)]
    if args.stage in {'synth', 'all'}:
        argv += ['-filelist', args.filelist, '-xdc', args.xdc]
    if checkpoint is not None:
        argv += ['-checkpoint', str(checkpoint)]
    manifest['command'] = argv
    write_json(manifest_path, manifest)

    stdout_path = out / 'vivado.stdout.log'
    stderr_path = out / 'vivado.stderr.log'
    interrupted: list[int] = []
    old_handlers = {}
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        old_handlers[sig] = signal.signal(sig, lambda signum, _frame: interrupted.append(signum))
    started = time.monotonic()
    process = None
    try:
        with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
            process = subprocess.Popen(argv, cwd=ROOT, stdout=stdout, stderr=stderr, start_new_session=True)
            while process.poll() is None:
                if interrupted:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                        process.wait(timeout=7)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    break
                time.sleep(0.25)
        rc = process.returncode
        markers = [name for name in ('COMPLETE', 'FAILED') if (out / name).is_file()]
        if interrupted:
            status = 'TIMEOUT' if interrupted[0] == signal.SIGTERM else 'INTERRUPTED'
        elif rc == 0 and markers == ['COMPLETE']:
            status = 'COMPLETE'
        else:
            status = 'FAILED'
        manifest.update(status=status, exit_code=rc, ended_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                        duration_seconds=round(time.monotonic() - started, 3),
                        terminal_markers=markers, resources=cgroup_usage(cgroup),
                        artifacts=output_artifacts(out), **report_inventory(out))
        if status == 'FAILED':
            manifest['failure'] = 'Vivado returned nonzero or did not write exactly one COMPLETE marker'
    except Exception as exc:
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=7)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        manifest.update(status='FAILED', exit_code=process.returncode if process else 125,
                        ended_utc=dt.datetime.now(dt.timezone.utc).isoformat(), failure=str(exc),
                        resources=cgroup_usage(cgroup), artifacts=output_artifacts(out),
                        **report_inventory(out))
    finally:
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)
        write_json(manifest_path, manifest)
    return 0 if manifest['status'] == 'COMPLETE' else (124 if manifest['status'] == 'TIMEOUT' else 1)


def launch(args: argparse.Namespace) -> int:
    if args.stage in {'route', 'report'} and not args.checkpoint:
        raise ValueError(f'{args.stage} requires --checkpoint')
    if args.stage in {'synth', 'all'}:
        source_inputs(ROOT / args.filelist, ROOT / args.xdc)
    if args.stage in {'route', 'report'} and not Path(args.checkpoint).expanduser().resolve().is_file():
        raise FileNotFoundError(f'checkpoint not found: {args.checkpoint}')
    preflight = host_preflight()
    if args.timeout is not None and args.timeout <= 0:
        raise ValueError('--timeout must be positive')
    # Accept either an explicit path or a command name from PATH so this
    # development entry point is not tied to one workstation's install tree.
    candidate = Path(args.vivado).expanduser()
    resolved = candidate.resolve() if candidate.parent != Path('.') else shutil.which(args.vivado)
    vivado = str(resolved) if resolved else ''
    if not Path(vivado).is_file() or not os.access(vivado, os.X_OK):
        raise FileNotFoundError(f'Vivado executable not found or not executable: {vivado}')
    run_id = f"dev_{args.stage}_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:6]}"
    run_dir = ROOT / 'build/vivado' / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    launcher_out = run_dir / 'launcher'
    timeout = args.timeout or DEFAULT_TIMEOUT[args.stage]
    worker = [sys.executable, '-B', str(Path(__file__).resolve()), '--worker',
              '--stage', args.stage, '--run-dir', str(run_dir), '--vivado', vivado,
              '--timeout', str(timeout), '--top', args.top, '--part', args.part,
              '--filelist', args.filelist, '--xdc', args.xdc]
    if args.checkpoint:
        worker += ['--checkpoint', args.checkpoint]
    scope_unit = f'spu-fpga-{run_id.replace("_", "-")}'
    scoped = ['systemd-run', '--user', '--scope', '--unit', scope_unit,
              f'--property=MemoryMax={MEMORY_MAX}', f'--property=MemorySwapMax={SWAP_MAX}',
              '--', *worker]
    write_json(run_dir / 'request.json', {
        'format': 'SPU_FPGA_BUILD_REQUEST_V1', 'run_id': run_id, 'stage': args.stage,
        'timeout_seconds': timeout, 'memory_max_bytes': MEMORY_MAX, 'swap_max_bytes': SWAP_MAX,
        'vivado': vivado, 'top': args.top, 'part': args.part,
        'filelist': args.filelist, 'xdc': args.xdc, 'host_preflight': preflight,
        'checkpoint': args.checkpoint, 'scope_unit': scope_unit, 'worker_command': worker,
    })
    result = subprocess.run([str(ROOT / 'tools/run_detached_job.sh'), '--output',
                             str(launcher_out.relative_to(ROOT)), '--timeout', str(timeout),
                             '--notify-desktop', '--', *scoped], cwd=ROOT)
    if result.returncode:
        write_json(run_dir / 'launch_error.json', {'status': 'NOT_LAUNCHED', 'exit_code': result.returncode})
        return result.returncode
    print(f'BUILD_LAUNCHED run={run_id} evidence={run_dir}')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('synth', 'route', 'report', 'all'), nargs='?')
    parser.add_argument('--stage', dest='stage_option', choices=('synth', 'route', 'report', 'all'))
    parser.add_argument('--vivado', default=str(VIVADO_DEFAULT))
    parser.add_argument('--top', default=TOP_DEFAULT)
    parser.add_argument('--part', default=PART_DEFAULT)
    parser.add_argument('--filelist', default=str(FILELIST_DEFAULT))
    parser.add_argument('--xdc', default=str(XDC_DEFAULT))
    parser.add_argument('--checkpoint')
    parser.add_argument('--timeout', type=int)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--run-dir')
    parser.add_argument('--smoke', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.stage_option:
        args.stage = args.stage_option
    if args.worker:
        if not args.stage or not args.run_dir:
            parser.error('internal worker needs --stage and --run-dir')
        return run_worker(args)
    if not args.stage:
        parser.error('choose synth, route, report or all')
    try:
        return launch(args)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'FPGA_BUILD PRECHECK FAILED: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
