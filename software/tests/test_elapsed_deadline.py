"""Elapsed-clock tests; simulated suspend, never suspends the host."""
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.run_elapsed_deadline import supervise

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp)/'deadline.json'
    assert supervise([sys.executable, '-c', 'pass'], 1, path) == 0
    assert not json.loads(path.read_text())['elapsed_deadline_breached']
    assert supervise([sys.executable, '-c', 'import time; time.sleep(2)'], .05, path) == 124
    assert json.loads(path.read_text())['elapsed_deadline_breached']
    # Boot time jumps over budget while active time barely advances.
    ticks = iter([0, 2_000_000_000, 2_000_000_001, 2_000_000_002])
    def resumed():
        return dict(boottime_ns=next(ticks, 2_000_000_003), monotonic_ns=1, utc_ns=5)
    assert supervise([sys.executable, '-c', 'import time; time.sleep(2)'], 1, path, resumed) == 124
    result = json.loads(path.read_text())
    assert result['elapsed_seconds'] >= 2 and result['active_seconds'] == 0
    # A completed child with exit0 after suspend must still be classified TIMEOUT.
    from unittest.mock import patch
    class Completed:
        pid = 123456
        def poll(self): return 0
        def wait(self): return 0
    ticks = iter([0, 2_000_000_000, 2_000_000_001])
    def late_completion():
        return dict(boottime_ns=next(ticks),monotonic_ns=1,utc_ns=5)
    with patch('tools.run_elapsed_deadline.subprocess.Popen',return_value=Completed()), \
         patch('tools.run_elapsed_deadline.os.killpg') as kill:
        assert supervise(['fixture'],1,path,late_completion)==124
        assert json.loads(path.read_text())['command_exit_code']==0
        assert kill.called
print('PASS elapsed deadline: success, timeout, simulated suspend and late completion')
