"""H0-SW-2 software-only bounded program lifecycle tests."""
import hashlib
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from software.spu_host.h0_model import Identity
from software.spu_host.h0_program import ProgramController, State
from software.tools.surd_cpu_encoding import encode_surd


def program(a, b, d):
    slices = (a, 0, b, 0, d, 0)
    words = [encode_surd("SLI", ["S0", str(i), str(v)]) for i, v in enumerate(slices)]
    words += [encode_surd("SLD", ["S0"]), encode_surd("SMUL", ["S0", "S0", "S0"])]
    words += [encode_surd("SRD", ["S0", str(i)]) for i in range(6)]
    return b"".join(w.to_bytes(8, "big") for w in words)


def digest(data):
    return hashlib.sha256(data).hexdigest()


class ProgramTests(unittest.TestCase):
    def test_two_distinct_programs_without_reconfiguration(self):
        c = ProgramController()
        identities = []
        for data, expected in ((program(1, 2, 3), (13, 4, 9)),
                               (program(2, 1, 2), (7, 4, 4))):
            loaded = c.load(data, digest(data))
            self.assertTrue(loaded.ok)
            identities.append(loaded.identity)
            self.assertTrue(c.verify(loaded.identity).ok)
            self.assertTrue(c.execute(loaded.identity).ok)
            self.assertEqual(c.result(loaded.identity).reason, "NOT_COMPLETE")
            self.assertTrue(c.advance_simulation(loaded.identity).ok)
            result = c.result(loaded.identity)
            self.assertEqual((result.reason, result.identity, result.value),
                             ("SIMULATED_RESULT", loaded.identity, expected))
        self.assertNotEqual(*identities)
        self.assertEqual(c.result(identities[0]).reason, "STALE_IDENTITY")

    def test_integrity_and_unsupported_refuse_execution(self):
        c = ProgramController()
        p = program(1, 2, 3)
        tx = c.load(p, "0" * 64).identity
        self.assertEqual(c.verify(tx).reason, "INTEGRITY")
        self.assertEqual(c.execute(tx).reason, "BAD_STATE")
        bad = bytearray(p)
        bad[0] = 0xff
        bad = bytes(bad)
        tx = c.load(bad, digest(bad)).identity
        self.assertEqual(c.verify(tx).reason, "UNSUPPORTED_PROGRAM")
        self.assertEqual(c.result(tx).reason, "NOT_COMPLETE")
        for data in (program(1001, 0, 1), program(1, 1, 0)):
            tx = c.load(data, digest(data)).identity
            self.assertEqual(c.verify(tx).reason, "UNSUPPORTED_PROGRAM")

    def test_busy_refusals_preserve_execution_and_result(self):
        c = ProgramController()
        p = program(1, 2, 3)
        tx = c.load(p, digest(p)).identity
        c.verify(tx)
        c.execute(tx)
        other = program(2, 1, 2)
        self.assertEqual(c.load(other, digest(other)).reason, "BUSY")
        self.assertEqual(c.state, State.ACTIVE)
        self.assertEqual(c.execute(tx).reason, "BAD_STATE")
        self.assertTrue(c.advance_simulation(tx).ok)
        self.assertEqual(c.result(tx).value, (13, 4, 9))
        self.assertEqual(c.load(b"bad", "x").reason, "INVALID_LOAD")
        self.assertEqual(c.result(tx).value, (13, 4, 9))

    def test_reset_and_malformed_identity_are_inert(self):
        c = ProgramController()
        p = program(1, 2, 3)
        old = c.load(p, digest(p)).identity
        self.assertEqual(c.verify(Identity(False, True)).reason, "STALE_IDENTITY")
        self.assertEqual(c.verify(Identity(0.0, 1)).reason, "STALE_IDENTITY")
        self.assertTrue(c.verify(old).ok)
        c.execute(old)
        c.reset()
        self.assertEqual(c.state, State.EMPTY)
        new = c.load(p, digest(p)).identity
        self.assertNotEqual(old, new)
        self.assertEqual(c.advance_simulation(old).reason, "STALE_IDENTITY")
        self.assertEqual(c.result(old).reason, "STALE_IDENTITY")
        self.assertTrue(c.verify(new).ok)
        c.execute(new)
        c.advance_simulation(new)
        self.assertEqual(c.result(new).value, (13, 4, 9))

    def test_state_and_shape_validation(self):
        c = ProgramController()
        self.assertEqual(c.load(b"", "0" * 64).reason, "INVALID_LOAD")
        p = program(1, 2, 3)
        self.assertEqual(c.load(p, "A" * 64).reason, "INVALID_LOAD")
        tx = c.load(p, digest(p)).identity
        self.assertEqual(c.execute(tx).reason, "BAD_STATE")
        self.assertTrue(c.verify(tx).ok)
        self.assertEqual(c.verify(tx).reason, "BAD_STATE")
        self.assertEqual(c.result(tx).reason, "NOT_COMPLETE")


if __name__ == "__main__":
    unittest.main()
