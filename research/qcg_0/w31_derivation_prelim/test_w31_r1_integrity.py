"""Synthetic R1 negative controls; never edit the frozen inventories or sources."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from w31_verify import verify_inventory


class Integrity(unittest.TestCase):
    def test_optimized_inventory_and_source_rejection(self):
        work = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory(prefix='w31_r1_integrity_') as directory:
            root = Path(directory)
            payload, inventory = root/'synthetic.txt', root/'synthetic.sha256'
            payload.write_text('synthetic original\n')
            pin = hashlib.sha256(payload.read_bytes()).hexdigest()
            original = pin+'  synthetic.txt\n'
            code = (f'import sys; sys.path.insert(0,{str(work)!r}); '
                    f'from w31_verify import verify_inventory; '
                    f'verify_inventory({str(root)!r},{str(inventory)!r})')
            for flags, optimization in [(['-O'], '0'), ([], '2')]:
                environment = dict(os.environ, PYTHONOPTIMIZE=optimization)
                command = [sys.executable, '-B', *flags, '-c', code]
                inventory.write_text(original)
                payload.write_text('synthetic original\n')
                result = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=3)
                self.assertEqual(result.returncode, 0, result.stderr)
                # Modified inventory must fail even though optimization removes asserts.
                inventory.write_text('0'*64+'  synthetic.txt\n')
                result = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=3)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('HOLD: pin mismatch: synthetic.txt', result.stderr)
                # Independently test drift in a file covered by an unchanged inventory.
                inventory.write_text(original)
                payload.write_text('synthetic modified\n')
                result = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=3)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('HOLD: pin mismatch: synthetic.txt', result.stderr)

    def test_empty_inventory_refused(self):
        with tempfile.TemporaryDirectory(prefix='w31_r1_empty_') as directory:
            inventory = Path(directory)/'synthetic.sha256'
            inventory.write_text('')
            with self.assertRaisesRegex(ValueError, 'empty inventory'):
                verify_inventory(directory, inventory)


if __name__ == '__main__': unittest.main()
