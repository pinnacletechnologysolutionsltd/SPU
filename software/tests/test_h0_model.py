"""Deterministic lifecycle and negative controls for the abstract H0 model."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from spu_host.h0_model import H0Model, Identity, Outcome, Phase, Request


class H0ModelTests(unittest.TestCase):
    def test_success_in_both_event_orders(self):
        for terminal_first in (True, False):
            with self.subTest(terminal_first=terminal_first):
                m = H0Model()
                tx = m.submit(Request("ECHO", 42)).identity
                if terminal_first:
                    self.assertTrue(m.terminal(tx, Outcome.SUCCESS, 42))
                    self.assertEqual(m.record.phase, Phase.ACTIVE)
                    self.assertIsNone(m.record.result)
                    self.assertTrue(m.effect_committed(tx))
                else:
                    self.assertTrue(m.effect_committed(tx))
                    self.assertEqual(m.record.phase, Phase.ACTIVE)
                    self.assertTrue(m.terminal(tx, Outcome.SUCCESS, 42))
                self.assertEqual((m.record.identity, m.record.outcome, m.record.result),
                                 (tx, Outcome.SUCCESS, 42))

    def test_unsupported_is_accepted_without_result(self):
        m = H0Model()
        a = m.submit(Request("UNKNOWN", 7))
        self.assertTrue(a.accepted)
        self.assertEqual((m.record.identity, m.record.phase, m.record.outcome,
                          m.record.result),
                         (a.identity, Phase.COMPLETE, Outcome.UNSUPPORTED, None))
        self.assertFalse(m.effect_committed(a.identity))

    def test_busy_cannot_replace_active(self):
        m = H0Model()
        tx = m.submit(Request("ECHO", 3)).identity
        before = m.record
        a = m.submit(Request("UNKNOWN", 9))
        self.assertEqual((a.accepted, a.reason, a.identity), (False, "BUSY", None))
        self.assertEqual(m.record, before)
        self.assertTrue(m.terminal(tx, Outcome.SUCCESS, 3))
        self.assertTrue(m.effect_committed(tx))
        self.assertEqual(m.record.result, 3)

    def test_stale_duplicate_and_malformed_events_are_inert(self):
        m = H0Model()
        old = m.submit(Request("ECHO", 1)).identity
        self.assertTrue(m.effect_committed(old))
        self.assertTrue(m.terminal(old, Outcome.SUCCESS, 1))
        new = m.submit(Request("ECHO", 2)).identity
        before = m.record
        self.assertFalse(m.terminal(old, Outcome.SUCCESS, 1))
        self.assertFalse(m.effect_committed(old))
        self.assertFalse(m.terminal(new, Outcome.SUCCESS, 1))
        self.assertFalse(m.terminal(new, Outcome.REFUSED, 2))
        self.assertFalse(m.terminal(Identity(99, 99), Outcome.SUCCESS, 2))
        self.assertEqual(m.record, before)
        self.assertTrue(m.effect_committed(new))
        self.assertFalse(m.effect_committed(new))
        self.assertFalse(m.terminal(new, Outcome.REFUSED))
        self.assertTrue(m.terminal(new, Outcome.SUCCESS, 2))
        self.assertFalse(m.terminal(new, Outcome.SUCCESS, 2))
        self.assertEqual((m.record.identity, m.record.result), (new, 2))

    def test_refusal_does_not_reuse_prior_result(self):
        m = H0Model()
        old = m.submit(Request("ECHO", 8)).identity
        m.effect_committed(old)
        m.terminal(old, Outcome.SUCCESS, 8)
        new = m.submit(Request("ECHO", 4)).identity
        self.assertTrue(m.terminal(new, Outcome.REFUSED))
        self.assertEqual((m.record.identity, m.record.outcome, m.record.result),
                         (new, Outcome.REFUSED, None))

    def test_known_reset_invalidates_active_and_old_epoch(self):
        m = H0Model()
        old = m.submit(Request("ECHO", 5)).identity
        self.assertTrue(m.terminal(old, Outcome.SUCCESS, 5))
        m.reset()
        self.assertIsNone(m.record)
        new = m.submit(Request("ECHO", 5)).identity
        self.assertNotEqual(old, new)
        self.assertFalse(m.effect_committed(old))
        self.assertFalse(m.terminal(old, Outcome.SUCCESS, 5))
        self.assertEqual(m.record.phase, Phase.ACTIVE)
        self.assertTrue(m.effect_committed(new))
        self.assertTrue(m.terminal(new, Outcome.SUCCESS, 5))

    def test_invalid_request_does_not_allocate_identity(self):
        m = H0Model()
        self.assertEqual(m.submit(Request("ECHO", True)).reason, "INVALID_REQUEST")
        self.assertIsNone(m.record)
        self.assertEqual(m.submit(Request("ECHO", 1)).identity, Identity(0, 1))

    def test_busy_after_terminal_before_commit(self):
        m = H0Model()
        tx = m.submit(Request("ECHO", 17)).identity
        self.assertTrue(m.terminal(tx, Outcome.SUCCESS, 17))
        before = m.record
        self.assertEqual(m.submit(Request("ECHO", 99)).reason, "BUSY")
        self.assertEqual(m.record, before)
        self.assertTrue(m.effect_committed(tx))
        self.assertEqual((m.record.identity, m.record.request, m.record.phase,
                          m.record.outcome, m.record.result),
                         (tx, Request("ECHO", 17), Phase.COMPLETE,
                          Outcome.SUCCESS, 17))

    def test_reset_after_commit_before_terminal(self):
        m = H0Model()
        old = m.submit(Request("ECHO", 7)).identity
        self.assertTrue(m.effect_committed(old))
        m.reset()
        self.assertIsNone(m.record)
        new = m.submit(Request("ECHO", 9)).identity
        before = m.record
        self.assertNotEqual(old, new)
        self.assertFalse(m.terminal(old, Outcome.SUCCESS, 7))
        self.assertFalse(m.effect_committed(old))
        self.assertEqual(m.record, before)
        self.assertTrue(m.terminal(new, Outcome.SUCCESS, 9))
        self.assertEqual(m.record, before)
        self.assertTrue(m.effect_committed(new))
        self.assertEqual((m.record.identity, m.record.request, m.record.phase,
                          m.record.outcome, m.record.result),
                         (new, Request("ECHO", 9), Phase.COMPLETE,
                          Outcome.SUCCESS, 9))

    def test_refusal_late_commit_notification_is_inert(self):
        m = H0Model()
        tx = m.submit(Request("ECHO", 11)).identity
        self.assertTrue(m.terminal(tx, Outcome.REFUSED))
        refused = m.record
        self.assertFalse(m.effect_committed(tx))
        self.assertEqual(m.record, refused)
        self.assertEqual((refused.identity, refused.request, refused.phase,
                          refused.outcome, refused.result),
                         (tx, Request("ECHO", 11), Phase.COMPLETE,
                          Outcome.REFUSED, None))

    def test_invalid_terminal_variants_are_inert(self):
        m = H0Model()
        tx = m.submit(Request("ECHO", 1)).identity
        before = m.record
        self.assertFalse(m.terminal(tx, Outcome.UNSUPPORTED))
        self.assertFalse(m.terminal(tx, Outcome.SUCCESS, True))
        self.assertEqual(m.record, before)
        self.assertTrue(m.effect_committed(tx))
        self.assertFalse(m.terminal(tx, Outcome.REFUSED))
        self.assertEqual(m.record, before)
        self.assertTrue(m.terminal(tx, Outcome.SUCCESS, 1))
        self.assertEqual((m.record.identity, m.record.outcome, m.record.result),
                         (tx, Outcome.SUCCESS, 1))

    def test_malformed_identity_cannot_commit_or_finish(self):
        class Lookalike:
            def __eq__(self, other):
                raise AssertionError("malformed identity must not be compared")

        class IdentitySubclass(Identity):
            pass

        bad_ids = (Identity(False, True), Identity(0.0, 1), Identity(0, 1.0),
                   Identity(0.0, 1.0), Lookalike(), IdentitySubclass(0, 1), None)
        for bad in bad_ids:
            with self.subTest(identity=bad):
                m = H0Model()
                tx = m.submit(Request("ECHO", 7)).identity
                before = m.record
                self.assertEqual(tx, Identity(0, 1))
                self.assertFalse(m.effect_committed(bad))
                self.assertFalse(m.terminal(bad, Outcome.SUCCESS, 7))
                self.assertEqual(m.record, before)
                # A valid terminal alone must not publish after a bad commit.
                self.assertTrue(m.terminal(tx, Outcome.SUCCESS, 7))
                self.assertEqual(m.record, before)
                self.assertTrue(m.effect_committed(tx))
                completed = m.record
                self.assertEqual((completed.identity, completed.outcome, completed.result),
                                 (tx, Outcome.SUCCESS, 7))
                self.assertFalse(m.effect_committed(bad))
                self.assertFalse(m.terminal(bad, Outcome.SUCCESS, 7))
                self.assertEqual(m.record, completed)

    def test_malformed_terminal_does_not_latch_before_valid_events(self):
        m = H0Model()
        tx = m.submit(Request("ECHO", 9)).identity
        before = m.record
        self.assertFalse(m.terminal(Identity(False, True), Outcome.SUCCESS, 9))
        self.assertTrue(m.effect_committed(tx))
        self.assertEqual(m.record, before)
        self.assertTrue(m.terminal(tx, Outcome.SUCCESS, 9))
        self.assertEqual((m.record.identity, m.record.outcome, m.record.result),
                         (tx, Outcome.SUCCESS, 9))


if __name__ == "__main__":
    unittest.main()
