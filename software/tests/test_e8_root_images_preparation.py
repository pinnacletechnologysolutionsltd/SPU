"""Short literal E8 descriptor, inverse, reduced-word and rejection witnesses."""
from pathlib import Path
import sys
import unittest
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from software.research.e8_root_images.tables import context,storage_inventory
from software.research.e8_root_images import descriptor as d
from software.research.e8_root_images import wire,reference
from software.research.e8_root_images.reduced import length,reduced_word
from software.research.e8_root_images.linear import identity,multiply,transpose,inverse


class RootImages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx=context()

    def test_independent_full_simple_reflection_table(self):
        self.assertEqual(reference.check_context(self.ctx)['reflection_entries'],1920)

    def test_literal_noncommuting_sides_and_output(self):
        x=(1,)*8
        a=d.from_word((0,2))
        b=d.from_word((2,0))
        self.assertNotEqual(a,b)
        self.assertEqual(d.apply(a,x),(0,2,0,0,0,0,0,2))
        self.assertEqual(d.apply(b,x),(2,0,0,0,0,0,0,2))
        start=d.from_word((0,))
        self.assertEqual(d.left(start,2),a)
        self.assertEqual(d.right(start,2),b)
        self.assertEqual(d.cartesian(a),reference.word_matrix((0,2)))

    def test_both_inverse_orders_and_gram_inverse(self):
        a=d.from_word((0,2,3))
        inv=d.inverse(a)
        self.assertEqual(inv,d.from_word((3,2,0)))
        self.assertEqual(d.compose(a,inv),self.ctx.basis_ids)
        self.assertEqual(d.compose(inv,a),self.ctx.basis_ids)
        c=d.simple_matrix(a)
        g=self.ctx.gram
        candidate=multiply(multiply(inverse(g),transpose(c)),g)
        self.assertEqual(multiply(c,candidate),identity())
        self.assertNotEqual(multiply(c,transpose(c)),identity())

    def test_reduced_word_and_longest_element(self):
        self.assertEqual(reduced_word(d.from_word((0,2,2,0)))['tokens'],())
        a=d.from_word((0,2))
        r=reduced_word(a)
        self.assertEqual(r['length'],length(a))
        self.assertEqual(d.from_word(r['tokens']),a)
        self.assertNotEqual(d.from_word(tuple(reversed(r['tokens']))),a)
        longest=tuple(self.ctx.index(tuple(-v for v in a)) for a in self.ctx.basis)
        r=reduced_word(longest)
        self.assertEqual(r['length'],120)
        self.assertTrue(all(old-new==1 for _,old,new in r['steps']))
        self.assertEqual(d.from_word(r['tokens']),longest)

    def test_admission_and_token_controls(self):
        identity_ids=self.ctx.basis_ids
        controls=[((0,)*8,'DESCRIPTOR_DUPLICATE'),((True,)+identity_ids[1:],'DESCRIPTOR_INDEX'),
                  ((240,)+identity_ids[1:],'DESCRIPTOR_INDEX'),(identity_ids[:-1],'DESCRIPTOR_SHAPE'),
                  ((identity_ids[1],identity_ids[0])+identity_ids[2:],'DESCRIPTOR_GRAM')]
        for value,reason in controls:
            with self.assertRaisesRegex(ValueError,reason): d.admit(value)
        for value in (True,-1,8):
            with self.assertRaisesRegex(ValueError,'GENERATOR_INDEX'): d.left(identity_ids,value)
        with self.assertRaisesRegex(ValueError,'WORD_LIMIT'): d.from_word([0]*257)

    def test_wire_identity_reserved_ids_and_storage(self):
        packet=wire.encode(self.ctx.basis_ids)
        self.assertEqual(len(packet),76)
        self.assertEqual(packet[:4],bytes((1,0xE8,8,0)))
        self.assertEqual(wire.decode(packet),self.ctx.basis_ids)
        for index,reason in ((0,'WIRE_SCHEMA'),(4,'WIRE_ROOT_IDENTITY'),(36,'WIRE_BASIS_IDENTITY')):
            bad=bytearray(packet); bad[index]^=1
            with self.assertRaisesRegex(ValueError,reason): wire.decode(bytes(bad))
        bad=packet[:68]+bytes((240,))+packet[69:]
        with self.assertRaisesRegex(ValueError,'DESCRIPTOR_INDEX'): wire.decode(bad)
        with self.assertRaisesRegex(ValueError,'WIRE_LENGTH'): wire.decode(packet[:-1])
        inventory=storage_inventory(self.ctx)
        self.assertEqual(inventory['static_total_bits'],sum(inventory['static_objects_bits'].values()))
        self.assertEqual(inventory['descriptor_payload_bits'],64)
        self.assertGreater(inventory['static_total_bits'],64)

    def test_table_corruption_and_atomic_failure(self):
        rows=list(self.ctx.reflections); row=list(rows[0]); row[0]=(row[0]+1)%240; rows[0]=tuple(row)
        with self.assertRaisesRegex(ValueError,'TABLE_REFERENCE|TABLE_INVOLUTION'):
            reference.check_context(replace(self.ctx,reflections=tuple(rows)))
        state=list(self.ctx.basis_ids); saved=state[:]
        with self.assertRaisesRegex(ValueError,'GENERATOR_INDEX'): d.left(state,True)
        self.assertEqual(state,saved)
        with self.assertRaisesRegex(ValueError,'E8_LATTICE_INPUT'): d.apply(state,(True,)*8)


if __name__=='__main__':
    unittest.main()
