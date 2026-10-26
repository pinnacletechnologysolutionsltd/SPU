"""Bounded, no-retry launch; --preflight never runs registered arithmetic."""
import sys


def check_startup():
    if not (sys.flags.isolated and sys.flags.ignore_environment and sys.flags.no_user_site
            and sys.flags.no_site and sys.flags.safe_path and sys.dont_write_bytecode):
        raise SystemExit('HOLD: outer launcher requires /usr/bin/python3 -I -S -B')


if __name__ == '__main__':
    check_startup()  # Built-in sys only: before any verification imports.

import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time
WORK=Path(__file__).resolve().parent
sys.path.append(str(WORK))  # Sole local root; isolated standard-library paths stay first.
from w31_verify import digest, require, verify_inventory, verify_inputs
from w31_certified import load_reference, REFERENCE_NAME

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'build/qcg_0/w31_independent'


def verify():
    verify_inventory(ROOT, WORK/'SOURCE_INPUTS_R2.sha256')
    manifest=json.loads((WORK/'INPUT_MANIFEST.json').read_text())
    verify_inputs(ROOT, manifest)
    for path,want in manifest['tools'].items():
        got=subprocess.check_output([path,'--version'],text=True).splitlines()[0]
        require(got==want, 'HOLD: tool mismatch: '+path)
    load_reference(ROOT/'research/qcg_0'/REFERENCE_NAME, manifest['inputs'][REFERENCE_NAME])
    return manifest


def sandbox(out=None):
    cmd=['/usr/bin/bwrap','--die-with-parent','--unshare-net','--unshare-pid',
         '--unshare-ipc','--unshare-uts','--new-session','--clearenv',
         '--setenv','PATH','/usr/bin','--setenv','LANG','C.UTF-8',
         '--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64',
         '--symlink','usr/bin','/bin','--proc','/proc','--dev','/dev',
         '--ro-bind',str(WORK),'/work','--chdir','/work']
    cmd+=['--ro-bind',str(ROOT/'research/qcg_0'/REFERENCE_NAME),'/references/'+REFERENCE_NAME]
    if out is not None: cmd+=['--bind',str(out),'/out']
    return cmd


def preflight():
    manifest=verify()
    # Probe the exact namespace/resource envelope without registered arithmetic.
    probe=('import resource,socket\n'
           'if resource.getrlimit(resource.RLIMIT_AS)!=(1073741824,1073741824): raise SystemExit("memory limit")\n'
           'if resource.getrlimit(resource.RLIMIT_FSIZE)!=(4194304,4194304): raise SystemExit("file limit")\n'
           'if socket.if_nameindex()!=[(1,"lo")]: raise SystemExit("network isolation")')
    command=['/usr/bin/timeout','30','/usr/bin/prlimit','--as=1073741824:1073741824',
             '--fsize=4194304:4194304','--']+sandbox()+['/usr/bin/python3','-I','-B','-c',probe]
    subprocess.run(command,check=True,timeout=35)
    return manifest


def finalize(leaf,rc,postcheck,journal=None,slot=None):
    try:
        used=sum(p.stat().st_size for p in leaf.iterdir() if p.is_file())
        cap=rc in (90,153) or (leaf/'CAP_BREACH').exists() or used+4096>10*1024*1024
        record=dict(returncode=rc,pins_after=postcheck,ended_ns=time.time_ns(),output_cap=cap)
        with (leaf/'terminal.json').open('x') as f:
            json.dump(record,f,sort_keys=True); f.flush(); os.fsync(f.fileno())
        mark=('FAILED' if cap or not postcheck else 'TIMEOUT' if rc==124 else
              'COMPLETE' if rc==0 and (leaf/'RUNNER_DONE').is_file() else 'FAILED')
    except OSError:
        mark='FAILED'
        try: (leaf/'FINALIZE_FAILED').touch(exist_ok=False)
        except OSError: pass
    if journal is not None:
        try:
            journal.write(json.dumps(dict(slot=slot,terminal=mark,ended_ns=time.time_ns()))+'\n')
            journal.flush(); os.fsync(journal.fileno())
        except OSError:
            mark='FAILED'
    try: (leaf/mark).touch(exist_ok=False)
    except OSError: pass
    markers=[m for m in ('COMPLETE','FAILED','TIMEOUT') if (leaf/m).exists()]
    if len(markers)!=1:
        raise RuntimeError('RESULT_UNAVAILABLE: terminal marker count != 1')
    return markers[0]


def main():
    check_startup()
    parser=argparse.ArgumentParser()
    parser.add_argument('--preflight',action='store_true')
    parser.add_argument('--authorization-file',type=Path)
    parser.add_argument('--attempt',type=int,choices=(1,2,3))
    args=parser.parse_args()
    preflight()
    if args.preflight:
        print('PASS: non-launching preflight; no attempt consumed')
        return
    pin=digest(WORK/'SOURCE_INPUTS_R2.sha256')
    required='GO QCG-W31 DERIVATION\nsource_manifest_sha256='+pin+'\nattempt='+str(args.attempt)+'\n'
    if not args.attempt or not args.authorization_file or args.authorization_file.read_text()!=required:
        raise SystemExit('HOLD: separate owner authorization bound to source manifest required')
    BASE.mkdir(parents=True,exist_ok=True)
    with (BASE/'attempts.jsonl').open('a+') as journal:
        fcntl.flock(journal,fcntl.LOCK_EX)
        # Exclusive, monotonic directories are the authoritative consumed-slot record.
        slots=[i for i in range(1,4) if (BASE/f'attempt_{i:02d}').exists()]
        slot=args.attempt
        if slot!=max(slots,default=0)+1:
            raise SystemExit('HOLD: attempts are append-only; no retries or skipped slots')
        leaf=BASE/f'attempt_{slot:02d}'
        leaf.mkdir()
        record=dict(slot=slot,started_ns=time.time_ns(),source_manifest_sha256=pin,
                    authorization_sha256=digest(args.authorization_file),policy='no network; no retry')
        journal.write(json.dumps(record,sort_keys=True)+'\n'); journal.flush(); os.fsync(journal.fileno())
        command=['/usr/bin/timeout','30','/usr/bin/prlimit','--as=1073741824:1073741824',
                 '--fsize=4194304:4194304','--']+sandbox(leaf)+[
                     '/usr/bin/python3','-I','-B','/work/derive_w31.py','--bounded-authorized-entry']
        try:
            with (leaf/'launch.json').open('x') as f: json.dump(dict(record,command=command),f)
            with (leaf/'stdout.log').open('xb') as out,(leaf/'stderr.log').open('xb') as err:
                rc=subprocess.run(command,stdout=out,stderr=err).returncode
            try: verify(); postcheck=True
            except Exception: postcheck=False
        except Exception:
            rc,postcheck=1,False
        mark=finalize(leaf,rc,postcheck,journal,slot)
        print(mark,leaf)
        if mark!='COMPLETE': raise SystemExit(1)


if __name__=='__main__': main()
