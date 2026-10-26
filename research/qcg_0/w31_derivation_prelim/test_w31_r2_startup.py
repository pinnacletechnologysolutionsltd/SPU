"""Outer-startup controls: temporary synthetic project, no registered entry."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

WORK = Path(__file__).resolve().parent


class Startup(unittest.TestCase):
    def run_python(self, flags, args, environment):
        return subprocess.run(['/usr/bin/python3', *flags, *args], env=environment,
                              capture_output=True, text=True, timeout=3)

    def test_injection_cannot_bypass_invalid_checksum(self):
        with tempfile.TemporaryDirectory(prefix='w31_r2_startup_') as directory:
            root = Path(directory)
            work = root/'research/qcg_0/w31_derivation_prelim'
            work.mkdir(parents=True)
            for name in ('launch_w31.py','w31_verify.py','w31_certified.py'):
                shutil.copyfile(WORK/name,work/name)
            payload = root/'synthetic.txt'
            payload.write_text('synthetic payload\n')
            original = hashlib.sha256(payload.read_bytes()).hexdigest()+'  synthetic.txt\n'
            inventory = work/'SOURCE_INPUTS_R2.sha256'
            hook = (f'import sys\nsys.path.insert(0,{str(work)!r})\n'
                    'import w31_verify\nw31_verify.require=lambda condition,message: None\n'
                    'print("INJECTED_STARTUP")\n')
            pythonpath = root/'injected_path'
            pythonpath.mkdir()
            userbase = root/'userbase'
            user_site = userbase/f'lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages'
            user_site.mkdir(parents=True)
            (pythonpath/'sitecustomize.py').write_text(hook)
            (user_site/'sitecustomize.py').write_text(hook)
            (user_site/'usercustomize.py').write_text(hook)
            baseline = (f'import sys; sys.path.insert(0,{str(work)!r}); '
                        'from w31_verify import verify_inventory; '
                        f'verify_inventory({str(root)!r},{str(inventory)!r}); print("BYPASS")')
            for origin in ('pythonpath','user_site'):
                environment = dict(os.environ, PYTHONOPTIMIZE='2', PYTHONUSERBASE=str(userbase),
                                   PYTHONPATH=str(pythonpath) if origin=='pythonpath' else '')
                for optimized in (False,True):
                    extra = ['-O'] if optimized else []
                    inventory.write_text('0'*64+'  synthetic.txt\n')
                    vulnerable = self.run_python(['-B',*extra],['-c',baseline],environment)
                    self.assertEqual(vulnerable.returncode,0,vulnerable.stderr)
                    self.assertIn('INJECTED_STARTUP',vulnerable.stdout)
                    self.assertIn('BYPASS',vulnerable.stdout)
                    isolated = self.run_python(['-I','-S','-B',*extra],
                                               [str(work/'launch_w31.py'),'--preflight'],environment)
                    self.assertNotEqual(isolated.returncode,0)
                    self.assertIn('HOLD: pin mismatch: synthetic.txt',isolated.stderr)
                    self.assertNotIn('INJECTED_STARTUP',isolated.stdout+isolated.stderr)
                    self.assertFalse((root/'build').exists())
                    # A changed covered payload is also rejected with intact inventory.
                    inventory.write_text(original)
                    payload.write_text('synthetic changed\n')
                    drift = self.run_python(['-I','-S','-B',*extra],
                                            [str(work/'launch_w31.py'),'--preflight'],environment)
                    self.assertNotEqual(drift.returncode,0)
                    self.assertIn('HOLD: pin mismatch: synthetic.txt',drift.stderr)
                    self.assertNotIn('INJECTED_STARTUP',drift.stdout+drift.stderr)
                    payload.write_text('synthetic payload\n')

    def test_isolated_preflight_and_missing_authorization(self):
        base = WORK.parents[2]/'build/qcg_0/w31_independent'
        self.assertFalse(base.exists())
        with tempfile.TemporaryDirectory(prefix='w31_r2_valid_') as directory:
            root = Path(directory)
            userbase = root/'userbase'
            user_site = userbase/f'lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages'
            user_site.mkdir(parents=True)
            hook = 'raise SystemExit("INJECTED_STARTUP")\n'
            (root/'sitecustomize.py').write_text(hook)
            (root/'w31_verify.py').write_text(hook)
            (user_site/'sitecustomize.py').write_text(hook)
            (user_site/'usercustomize.py').write_text(hook)
            environment = dict(os.environ, PYTHONPATH=str(root), PYTHONUSERBASE=str(userbase),
                               PYTHONOPTIMIZE='2')
            for extra in ([],['-O']):
                flags = ['-I','-S','-B',*extra]
                preflight = self.run_python(flags,[str(WORK/'launch_w31.py'),'--preflight'],environment)
                self.assertEqual(preflight.returncode,0,preflight.stderr)
                self.assertIn('PASS: non-launching preflight; no attempt consumed',preflight.stdout)
                self.assertNotIn('INJECTED_STARTUP',preflight.stdout+preflight.stderr)
                denied = self.run_python(flags,[str(WORK/'launch_w31.py')],environment)
                self.assertNotEqual(denied.returncode,0)
                self.assertIn('HOLD: separate owner authorization',denied.stderr)
                self.assertNotIn('INJECTED_STARTUP',denied.stdout+denied.stderr)
                self.assertFalse(base.exists())

    def test_unsafe_startup_rejected(self):
        environment = dict(os.environ, PYTHONPATH='', PYTHONOPTIMIZE='0')
        for flags in (['-B'],['-I','-B'],['-S','-B'],['-I','-S']):
            result = self.run_python(flags,[str(WORK/'launch_w31.py'),'--preflight'],environment)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('HOLD: outer launcher requires /usr/bin/python3 -I -S -B',result.stderr)


if __name__ == '__main__': unittest.main()
