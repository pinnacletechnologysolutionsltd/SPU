"""R3 export-only indexing with unchanged ending-request event attribution."""
from unittest.mock import patch
import unittest
from w31_arithmetic import Q
from w31_certified import check_route
from w31_prepare import SEQUENTIAL
from w31_routes import preparation, route
from w31_sequential import evaluate
from test_w31_r1_values import synthetic_reference


class Export(unittest.TestCase):
    def test_q00_q15_q16_all_arms(self):
        for arm in SEQUENTIAL:
            state, p = preparation(arm,[Q(2)],[Q(1)])
            self.assertEqual(p['status'],'OK')
            captured = {}
            def capture(trace,arm,tape,working,k):
                values = evaluate(trace,arm,tape,working,k)
                captured[k] = (list(trace.events),dict(trace.counts))
                return values
            with patch('w31_routes.sequential',capture):
                result = route(arm,state,'S3')
            for k in (0,15,16):
                row = result['rows'][k]
                self.assertEqual(row['status'],'OK')
                self.assertTrue(row['increment_available'])
                self.assertEqual(row['values']['increment_to_next'],[5,16] if k<16 else None)
                self.assertNotIn('increment_from_previous',row['values'])
            step = 'c15' if arm=='C2' else 'b22' if arm in ('PH','PHFD','C1') else 'a12'
            self.assertFalse(any('.'+step+'.' in e[0] for e in captured[0][0]))
            self.assertEqual(sum('.'+step+'.' in e[0] for e in captured[16][0]),1)
            for k in range(17):
                self.assertEqual(result['rows'][k]['ledger'],captured[k][1])

    def test_increment_refusal_boundaries(self):
        for ending in (2,16):
            def fixture(trace,arm,tape,state,k):
                values = evaluate(trace,arm,tape,state,k)
                if k == ending-1:
                    # Admissible synthetic retained scalar forces the next A's e1 check.
                    state['_previous_S'] = Q(-(2**31-1))
                return values
            state, _ = preparation('Horner',[Q(2)],[Q(1)])
            with patch('w31_routes.sequential',fixture):
                result = route('Horner',state,'S3')
            rows = result['rows']
            self.assertEqual((result['issued'],result['unissued']),(ending+1,16-ending))
            refused = rows[ending]
            self.assertEqual(refused['status'],'REFUSED')
            self.assertEqual(refused['event_id'],f'Horner.Q.q{ending:02d}.a12.1.e1')
            self.assertEqual(refused['state_before'],refused['state_after'])
            self.assertNotIn('values',refused)
            pending = rows[ending-1]
            self.assertEqual(pending['status'],'OK')
            self.assertFalse(pending['increment_available'])
            self.assertNotIn('increment_to_next',pending['values'])
            for row in rows[ending+1:]:
                self.assertEqual(row['scheduling_outcome'],'NOT_ISSUED')
                for field in ('status','event_id','ledger','values'):
                    self.assertNotIn(field,row)
            result['curve'] = 'SYN'
            check_route(result,synthetic_reference())


if __name__ == '__main__': unittest.main()
