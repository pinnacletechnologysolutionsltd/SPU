"""Short closure, ownership, export and refusal witnesses; not qualification."""
from pathlib import Path
import sys
import unittest
from dataclasses import replace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from software.research.e8_validated_state.session import Session
from software.research.e8_validated_state.handles import StateKey,Export
from software.research.e8_root_images import descriptor,wire
from software.research.e8_root_images.tables import context
from software.research.lattice_drycount.ledger import replay


class ValidatedState(unittest.TestCase):
    def packet(self):
        return wire.encode(context().basis_ids)

    def test_import_and_all_permitted_generators_without_gram_repetition(self):
        s=Session(True); h=s.import_wire(self.packet()); expected=context().basis_ids
        for j in range(8):
            before=s.report()['work']
            s.transform(h,j)
            self.assertEqual(s.report()['work']-before,117)
            expected=descriptor.left(expected,j)
            out=s.export_wire(h)
            self.assertEqual(wire.decode(out.payload),expected)
            s.release_export(out)
        r=s.report()
        self.assertEqual(r['stages']['import/gram']['multiply'],324)
        self.assertTrue(all(v.get('multiply',0)==0 for k,v in r['stages'].items() if k.startswith('transform')))
        self.assertEqual(replay(s.events(),r)['status'],'REPLAY_PASS')

    def test_noncommuting_materialization_and_export_lifetimes(self):
        s=Session(True); h=s.import_wire(self.packet())
        s.transform(h,0); s.transform(h,2)
        before=s.report()['work']; packet=s.export_wire(h)
        self.assertEqual(s.report()['work']-before,495)
        before=s.report()['work']; vector=s.materialize(h,(1,)*8)
        self.assertEqual(vector.payload,(0,2,0,0,0,0,0,2))
        self.assertEqual(s.report()['work']-before,28302)
        self.assertEqual(s.report()['live_exports'],2)
        s.release_export(packet); s.release_export(vector); s.retire(h)
        self.assertEqual((s.report()['live_states'],s.report()['live_exports']),(0,0))
        self.assertEqual(s.report()['retained_live_bits'],307904)
        replay(s.events(),s.report())

    def test_forged_foreign_and_retired_state(self):
        s=Session(); other=Session(); h=s.import_wire(self.packet())
        for key in (StateKey(),h):
            with self.assertRaisesRegex(ValueError,'UNKNOWN_FOREIGN_OR_RETIRED_STATE'):
                other.transform(key,0)
        with self.assertRaisesRegex(ValueError,'STATE_HANDLE_TYPE'): s.transform(context().basis_ids,0)
        s.retire(h)
        with self.assertRaisesRegex(ValueError,'UNKNOWN_FOREIGN_OR_RETIRED_STATE'): s.transform(h,0)

    def test_refusals_preserve_state_and_ownership(self):
        s=Session(); h=s.import_wire(self.packet())
        baseline=s.report()['retained_live_bits']
        for j,side,reason in ((True,'left','INTEGER_TYPE'),(8,'left','GENERATOR_INDEX'),
                              (0,'right','UNSUPPORTED_INTERNAL_OPERATION'),(0,True,'SIDE_TYPE')):
            with self.assertRaisesRegex(ValueError,reason): s.transform(h,j,side)
            self.assertEqual(s.report()['retained_live_bits'],baseline)
        for vector,reason in (((True,)*8,'INTEGER_TYPE'),((1,0,0,0,0,0,0,0),'LATTICE_PARITY'),
                              (((1 << 63)-4,)*8,'SCALAR_RANGE')):
            with self.assertRaisesRegex(ValueError,reason): s.materialize(h,vector)
            self.assertEqual(s.report()['retained_live_bits'],baseline)
        out=s.export_wire(h); self.assertEqual(out.payload,self.packet()); s.release_export(out)

    def test_invalid_import_and_setup_context_are_rejected(self):
        s=Session(); baseline=s.report()['retained_live_bits']
        packet=self.packet()
        bads=[packet[:-1],bytes((0,))+packet[1:],packet[:68]+bytes((240,))+packet[69:],packet[:68]+bytes(8)]
        for value in bads:
            with self.assertRaises(ValueError): s.import_wire(value)
            self.assertEqual(s.report()['live_states'],0)
            self.assertEqual(s.report()['retained_live_bits'],baseline)
        c=context(); rows=list(c.reflections); row=list(rows[0]); row[0]=(row[0]+1)%240; rows[0]=tuple(row)
        with patch('software.research.e8_validated_state.session.context',return_value=replace(c,reflections=tuple(rows))):
            with self.assertRaisesRegex(ValueError,'TABLE_REFERENCE|TABLE_INVOLUTION'): Session()

    def test_alias_capacity_and_export_capabilities(self):
        s=Session(); a=s.import_wire(self.packet()); b=s.import_wire(self.packet())
        s.transform(a,0); old=s.export_wire(b); self.assertEqual(old.payload,self.packet())
        forged=Export(old.payload,old.key)
        with self.assertRaisesRegex(ValueError,'EXPORT_RECORD_IDENTITY'): s.release_export(forged)
        s.release_export(old)
        with self.assertRaisesRegex(ValueError,'UNKNOWN_FOREIGN_OR_RELEASED_EXPORT'): s.release_export(old)
        handles=[a,b]+[s.import_wire(self.packet()) for _ in range(6)]
        before=s.report()['retained_live_bits']
        with self.assertRaisesRegex(ValueError,'STATE_CAPACITY'): s.import_wire(self.packet())
        self.assertEqual(s.report()['retained_live_bits'],before)
        self.assertEqual(s.report()['live_states'],8)
        for h in handles: s.retire(h)


if __name__=='__main__':
    unittest.main()
