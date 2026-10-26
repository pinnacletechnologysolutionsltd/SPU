"""Bounded writer (contract §9 runner cap contract): the only path to disk and stdout. Exclusive create, per-file and running-total caps."""
import os
import sys

FILE_CAP, TOTAL_CAP = 4 * 1024 * 1024, 8 * 1024 * 1024


class CapBreach(Exception):
    pass


class Out:
    def __init__(self, directory, file_cap=FILE_CAP, total_cap=TOTAL_CAP):
        self.dir, self.file_cap, self.total_cap, self.total = directory, file_cap, total_cap, 0

    def _admit(self, n):
        if n > self.file_cap or self.total + n > self.total_cap:
            raise CapBreach("%d bytes" % n)
        self.total += n

    def write(self, name, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self._admit(len(data))
        with open(os.path.join(self.dir, name), "xb") as f:
            f.write(data)

    def say(self, line):
        data = (line + "\n").encode("utf-8")
        self._admit(len(data))
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()

    def breach(self):
        """Best effort: create the empty CAP_BREACH marker; the caller then exits 90 and never writes RUNNER_DONE."""
        try:
            open(os.path.join(self.dir, "CAP_BREACH"), "xb").close()
        except OSError:
            pass
        return 90
