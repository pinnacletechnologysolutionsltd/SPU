"""Exact preview, control and metered left-kernel witnesses; no corpus campaign."""
from pathlib import Path
import sys
import copy
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from software.research.e8_root_images.tables import context
from software.research.e8_root_images import descriptor
from software.research.e8_workload_preparation.fixtures import plan,expand,ownership,checkpoints
from software.research.e8_workload_preparation.left_kernel import run as kernel
from software.research.e8_workload_preparation.preview import run as preview
from software.research.lattice_drycount.ledger import replay


class Preparation(unittest.TestCase):
    def test_plan_identity_and_observation_boundaries(self):
        p=plan()
        self.assertEqual(len(p['configs']),384)
        self.assertEqual(len({c['id'] for c in p['configs']}),384)
        self.assertEqual(checkpoints(8,16),(8,))
        self.assertEqual(checkpoints(8,4),(4,8))
        self.assertEqual(checkpoints(8,'final'),(8,))

    def test_inputs_match_across_regimes_and_cadences(self):
        c=dict(clients=4,length=8,cadence=1,regime='cold_serial',family='scrambled')
        original=expand(c)
        for mode in ('private_lockstep','shared_lockstep'):
            self.assertEqual(expand(dict(c,regime=mode,cadence='final')),original)
        self.assertEqual(max(abs(v) for row in original for v in row['initial_vector']) <= 1 << 31,True)
        inverse=expand(dict(c,family='inverse_pair'))
        self.assertTrue(all(row['tokens'][4:]==tuple(reversed(row['tokens'][:4])) for row in inverse))

    def test_static_ownership_lower_bound(self):
        c=dict(clients=4,length=8,cadence=4,regime='private_lockstep',family='scrambled')
        private=ownership(c)
        shared=ownership(dict(c,regime='shared_lockstep'))
        serial=ownership(dict(c,regime='cold_serial'))
        self.assertEqual(private['root_image_static_lower_bound_bits'],1230720)
        self.assertEqual(shared['root_image_static_lower_bound_bits'],307680)
        self.assertEqual(serial['active_clients'],1)
        self.assertEqual((private['setup_instances'],shared['setup_instances'],serial['setup_instances']),(4,1,4))

    def test_metered_kernel_formula_and_ledger_mutants(self):
        images=descriptor.from_word((0,))
        r,e=kernel(images,2,True)
        self.assertEqual(r['output'],descriptor.from_word((0,2)))
        self.assertEqual(r['ledger_replay']['status'],'REPLAY_PASS')
        self.assertEqual(r['stages']['left_update']['indexed_read'],24)
        self.assertEqual(r['stages']['admission']['multiply'],324)
        bad=copy.deepcopy(r); bad['work']-=1
        with self.assertRaisesRegex(AssertionError,'LEDGER_WORK'): replay(e,bad)
        bad=copy.deepcopy(r); bad['simultaneous_live_bits']-=64
        with self.assertRaisesRegex(AssertionError,'LEDGER_PEAK'): replay(e,bad)

    def test_prefix_observer_and_atomic_controls(self):
        c=dict(id='short',clients=1,length=8,cadence=1,regime='shared_lockstep',family='inverse_pair')
        p=preview(c)
        original=expand(c)[0]['initial_vector']
        self.assertEqual(p['observations'][-1]['value'],original)
        with self.assertRaisesRegex(ValueError,'PREVIEW_SCOPE'): preview(dict(c,length=32))
        with self.assertRaisesRegex(ValueError,'FIXTURE_CLIENTS'): expand(dict(c,clients=True))
        with self.assertRaisesRegex(ValueError,'FIXTURE_CLIENTS'): expand(dict(c,clients=1.0))
        with self.assertRaisesRegex(ValueError,'FIXTURE_LENGTH'): expand(dict(c,length=8.0))
        with self.assertRaisesRegex(ValueError,'FIXTURE_CADENCE'): expand(dict(c,cadence=1.0))
        images=list(context().basis_ids); saved=images[:]
        with self.assertRaisesRegex(ValueError,'INTEGER_TYPE'): kernel(images,True)
        self.assertEqual(images,saved)


if __name__=='__main__':
    unittest.main()
