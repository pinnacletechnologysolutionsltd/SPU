"""Synthetic qualification only: never call registered case/tape constructors."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from collections import Counter
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('reference_derive',HERE/'derive.py')
derive=importlib.util.module_from_spec(spec)
spec.loader.exec_module(derive)
from accounting import Budget, Kernels, Ledger, Refusal, storage
from controls import Oracle, inject, request, reject_fault, validate_result
from pell import coefficients, product, norm, step
from semantics import State, decimal


def seeded(arm='C',limits=None):
    ledger=Ledger(cap=100_000)
    state=State(ledger,arm,limits)
    # Deliberately nonregistered starting graph and values; not a registered
    # RESET/STEP/OBSERVE microcase or a prefix of a nominal tape.
    for node,value in enumerate((5,-2,3)):
        old=state.f['k.'+str(node)]
        state.f['k.'+str(node)]=ledger.allocate(value,'synthetic.seed',retained=True)
        ledger.drop(old)
        if arm in 'AB':
            ledger.drop_pair(state.primary[node])
            a,b=coefficients(value)
            pair=ledger.pair(ledger.allocate(a,'seed',retained=True),
                             ledger.allocate(b,'seed',retained=True),'seed')
            state.primary[node]=pair
            state.cache[node]['pair']=pair
            for container,key in ((state.cache[node],'ref'),(state.f,'primary.ref.'+str(node))):
                ledger.drop(container[key])
                container[key]=ledger.allocate(pair.identity,'seed','ref',True)
    return ledger,state


class Synthetic(unittest.TestCase):
    def test_oracle_general_integer_identities(self):
        x,y=(7,-4),(-3,5)
        self.assertEqual(step(step(x,1),-1),x)
        self.assertEqual(norm(product(x,y)),norm(x)*norm(y))

    def test_strict_arithmetic_types(self):
        with self.assertRaises(TypeError):
            step((True,3),1)
        with self.assertRaises(TypeError):
            coefficients(True)

    def test_typed_storage(self):
        self.assertEqual(storage(3,'key'),64)
        self.assertEqual(storage('REFUSED','status'),2)
        self.assertEqual(storage(False,'bool'),1)
        with self.assertRaises(ValueError):
            storage(2**64,'ref')

    def test_helper_result_ownership(self):
        l,s=seeded()
        values=[l.allocate(x,'synthetic',retained=True) for x in (7,-4,-3,5)]
        retained=set(l.slots)
        pair=Kernels(l,s.c).pair(values,'synthetic.multiply')
        self.assertEqual(pair.values(),product((7,-4),(-3,5)))
        self.assertEqual(set(l.slots)-retained,{pair.a.name,pair.b.name})
        l.drop_pair(pair)
        self.assertEqual(set(l.slots),retained)

    def test_export_refusal_rolls_back_ladder(self):
        l,s=seeded(limits={'O':2})
        before,slots=s.identity(),set(l.slots)
        out=s.execute(request('OBSERVE'),'synthetic.C.export')
        self.assertTrue(out['refused'])
        self.assertEqual(out['output']['receipt']['code'],'COEFFICIENT_LIMIT')
        self.assertEqual(s.identity(),before)
        self.assertEqual(set(l.slots),slots)
        self.assertFalse(any(x['valid'].value for x in s.directory))

    def test_observation_matches_independent_coefficients(self):
        for arm in 'ABCD':
            l,s=seeded(arm)
            result=s.execute(request('OBSERVE'),'synthetic.'+arm+'.observe')
            self.assertFalse(result['refused'])
            self.assertEqual(result['output']['pairs'],decimal([coefficients(k) for k in (5,-2,3)]))

    def test_fresh_validation_and_warm_cache(self):
        l,s=seeded()
        first=s.execute(request('OBSERVE'),'synthetic.C.first')
        before=l.counts.copy()
        second=s.execute(request('OBSERVE'),'synthetic.C.second')
        self.assertEqual(first['output'],second['output'])
        self.assertEqual(l.counts['OBSERVE.INSTALL'],before['OBSERVE.INSTALL'])
        self.assertGreater(l.counts['OBSERVE.VISIT'],before['OBSERVE.VISIT'])
        self.assertTrue(all(x.retained for x in l.slots.values()))

    def test_observe_work_denial_boundaries(self):
        l,s=seeded()
        start=l.used
        successful=s.execute(request('OBSERVE'),'synthetic.C.deny')
        self.assertFalse(successful['refused'])
        length=l.used-start
        # Early loads, nested arithmetic, receipt/serialization and final COMMIT.
        boundaries=range(length)
        for offset in sorted(boundaries):
            ledger,state=seeded()
            before,slots=state.identity(),set(ledger.slots)
            ledger.cap=ledger.used+offset
            result=state.execute(request('OBSERVE'),'synthetic.C.deny')
            self.assertTrue(result['refused'],offset)
            self.assertEqual(result['output']['receipt']['code'],'WORK_LIMIT')
            self.assertEqual(state.identity(),before)
            self.assertEqual(set(ledger.slots),slots)
            self.assertEqual(ledger.used,ledger.cap)
            self.assertEqual(ledger.live_bits,sum(storage(x.value,x.kind) for x in ledger.slots.values()))

    def test_set_noop_one_commit(self):
        l,s=seeded()
        self.assertFalse(s.execute(request('SET','u',9),'synthetic.C.set9')['refused'])
        before=s.identity(); counts=l.counts.copy()
        result=s.execute(request('SET','u',9),'synthetic.C.noop')
        self.assertEqual(s.identity(),before)
        self.assertFalse(result['output']['changed'])
        self.assertEqual(l.counts['EVENT.COMMIT']-counts['EVENT.COMMIT'],1)
        for kind in ('EVAL','INVALIDATE','INSTALL'):
            self.assertEqual(l.counts['EVENT.'+kind],counts['EVENT.'+kind])

    def test_set_commit_denial(self):
        l,s=seeded(); start=l.used
        s.execute(request('SET','u',9),'synthetic.C.set')
        length=l.used-start
        for offset in (0,1,length//2,length-1):
            ledger,state=seeded(); before=state.identity()
            ledger.cap=ledger.used+offset
            result=state.execute(request('SET','u',9),'synthetic.C.set')
            self.assertTrue(result['refused'])
            self.assertEqual(state.identity(),before)

    def test_metadata_width_refusal(self):
        l,s=seeded(limits={'P':3})
        before=s.identity()
        result=s.execute(request('SET','u',19),'synthetic.C.width')
        self.assertEqual(result['output']['receipt']['code'],'ARITH_LIMIT')
        self.assertIn('.u.P.test',result['output']['receipt']['stage'])
        self.assertEqual(s.identity(),before)

    def test_raw_guard_precedes_first_use(self):
        l,s=seeded(limits={'R':3})
        # Begin within the raw bound, then cross it on the prospective source.
        for node,value in ((0,7),(2,5)):
            old=s.f['k.'+str(node)]
            s.f['k.'+str(node)]=l.allocate(value,'synthetic.seed',retained=True)
            l.drop(old)
        before=s.identity()
        out=s.execute(request('STEP',0,1),'synthetic.C.raw')
        self.assertEqual(out['output']['receipt']['code'],'ARITH_LIMIT')
        self.assertIn('.k.0.R.test',out['output']['receipt']['stage'])
        self.assertEqual(s.identity(),before)

    def test_synthetic_mixed_updates_match_truth_and_versions(self):
        outputs={}; counters={}
        tape=((1,1),(0,-1),(1,-1),(0,-1),(0,1))
        for arm in 'ABCD':
            l,s=seeded(arm)
            powers=[5,-2]
            versions=[0,0]
            for index,(target,delta) in enumerate(tape):
                result=s.execute(request('STEP',target,delta),'synthetic.'+arm+'.mixed.'+str(index))
                self.assertFalse(result['refused'])
                powers[target]+=delta; versions[target]+=1
            read=s.execute(request('OBSERVE'),'synthetic.'+arm+'.final')
            self.assertFalse(read['refused'])
            self.assertEqual(read['output']['pairs'],decimal([coefficients(k) for k in powers+[sum(powers)]]))
            receipt=read['output']['receipt']
            self.assertEqual(receipt['versions'],decimal(versions+[len(tape),0,0,0]))
            outputs[arm]=read['output']; counters[arm]=dict(l.counts)
        self.assertEqual(outputs['A'],outputs['D'])
        self.assertEqual(counters['A'],counters['B'])
        self.assertEqual(counters['C'],counters['D'])

    def test_set_equal_noop_and_commit_denial(self):
        l,s=seeded(); start=l.used; before=s.identity()
        result=s.execute(request('SET_EQUAL',0,5),'synthetic.C.equal')
        self.assertFalse(result['refused'])
        self.assertFalse(result['output']['changed'])
        self.assertEqual(s.identity(),before)
        length=l.used-start
        ledger,state=seeded(); before=state.identity()
        ledger.cap=ledger.used+length-1
        denied=state.execute(request('SET_EQUAL',0,5),'synthetic.C.equal')
        self.assertTrue(denied['refused'])
        self.assertTrue(denied['output']['receipt']['stage'].endswith('.COMMIT'))
        self.assertEqual(state.identity(),before)

    def test_product_fault_uses_internal_product_state(self):
        for arm in 'ABCD':
            l,s=seeded(arm)
            s.execute(request('STEP',1,1),'synthetic.'+arm+'.product',fault='product_exponent')
            observed=s.execute(request('OBSERVE'),'synthetic.'+arm+'.read_product')
            self.assertFalse(observed['refused'])
            self.assertEqual(observed['output']['pairs'][0],decimal(coefficients(5)))
            self.assertEqual(observed['output']['pairs'][1],decimal(coefficients(-1)))
            self.assertNotEqual(observed['output']['pairs'][2],decimal(coefficients(4)))

    def test_pair_kernel_failure_leaves_no_scratch(self):
        l,s=seeded(limits={'R':3})
        operands=[l.allocate(x,'synthetic',retained=True) for x in (7,4,3,5)]
        slots=set(l.slots)
        with self.assertRaises(Refusal):
            Kernels(l,s.c).pair(operands,'synthetic.raw_multiply')
        self.assertEqual(set(l.slots),slots)

    def test_domain_and_shape_before_freshness(self):
        l,s=seeded()
        inject(s,'bad_proof','synthetic.corrupt')
        bad=s.execute(request('STEP',8,1),'synthetic.C.bad_domain')
        self.assertEqual(bad['output']['receipt']['code'],'OUT_OF_DOMAIN')
        typed=s.execute(request('STEP',True,1),'synthetic.C.bad_type')
        self.assertEqual(typed['output']['receipt']['operation_status'],'INVALID')
        l.modeled_cap=l.modeled_used
        denied=s.execute({'unexpected':True},'synthetic.C.denied')
        self.assertEqual(denied['output']['receipt']['code'],'WORK_LIMIT')
        self.assertTrue(denied['output']['receipt']['stage'].endswith('.ENTER'))

    def test_snapshot_fault_is_internal(self):
        l,s=seeded()
        changed=s.execute(request('STEP',0,1),'synthetic.C.step',fault='stale_snapshot')
        self.assertFalse(changed['refused'])
        observed=s.execute(request('OBSERVE'),'synthetic.C.stale')
        self.assertEqual(observed['output']['receipt']['code'],'STALE')
        self.assertEqual(l.counts['OBSERVE.INSTALL'],0)

    def test_proof_fault_precedes_expansion(self):
        l,s=seeded()
        inject(s,'bad_proof','synthetic.proof')
        result=s.execute(request('OBSERVE'),'synthetic.C.proof')
        self.assertEqual(result['output']['receipt']['code'],'INVALID_STATE')
        self.assertFalse(any(x['valid'].value for x in s.directory))

    def test_inverse_fault_targets_z2(self):
        for arm in 'ABCD':
            l,s=seeded(arm)
            s.execute(request('STEP',1,-1),'synthetic.'+arm+'.inverse',fault='inverse_sign')
            result=s.execute(request('OBSERVE'),'synthetic.'+arm+'.read')
            self.assertFalse(result['refused'])
            self.assertEqual(result['output']['pairs'][0],decimal(coefficients(5)))
            self.assertNotEqual(result['output']['pairs'][1],decimal(coefficients(-3)))

    def test_old_key_mutation_is_detectable(self):
        l,s=seeded()
        s.execute(request('OBSERVE'),'synthetic.C.populate')
        s.execute(request('STEP',0,1),'synthetic.C.change',fault='old_key')
        result=s.execute(request('OBSERVE'),'synthetic.C.poison',fault='old_key')
        self.assertNotEqual(result['output']['pairs'][0],decimal(coefficients(6)))

    def test_writer_requires_full_set_and_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            writer=derive.Writer(Path(directory)/'new')
            with self.assertRaises(RuntimeError):
                writer.finish()
            with self.assertRaises(Refusal):
                writer.write('nominal.json',{'synthetic':'x'*(2*1024**2)})
            self.assertFalse((writer.destination/'manifest.json').exists())
            for name in derive.FILES[:-1]:
                writer.write(name,{'synthetic':True,'status':'DERIVED_PENDING_INDEPENDENT_ACCEPTANCE'})
            writer.write('manifest.json',{'files':writer.hashes.copy(),'acceptance':'PENDING'})
            identity=writer.finish()
            self.assertEqual(derive.digest(writer.destination/'manifest.json'),identity)
            self.assertEqual(set(x.name for x in writer.destination.iterdir()),set(derive.FILES))

    def test_writer_interrupted_publication_has_no_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            writer=derive.Writer(Path(directory)/'new')
            for name in derive.FILES:
                value={'synthetic':True,'status':'DERIVED_PENDING_INDEPENDENT_ACCEPTANCE'}
                if name=='manifest.json':
                    value.update(files=writer.hashes.copy(),acceptance='PENDING')
                writer.write(name,value)
            real=derive.os.link
            calls=[]
            def fail_third(source,destination):
                calls.append(destination)
                if len(calls)==3:
                    raise OSError('synthetic interruption')
                return real(source,destination)
            with patch.object(derive.os,'link',fail_third):
                with self.assertRaises(OSError):
                    writer.finish()
            self.assertFalse((writer.destination/'manifest.json').exists())
            self.assertFalse(writer.finished)

    def test_resource_assertion_is_fail_closed(self):
        with patch.object(derive.resource,'getrlimit',return_value=(1,1)):
            with self.assertRaises(RuntimeError):
                derive.assert_limits()

    def test_equality_fault_rejected_against_truth(self):
        l,s=seeded()
        observed=s.execute(request('OBSERVE'),'synthetic.C.equal_fault',fault='equality_true')
        expected=dict(observed['output'],equal=False)
        self.assertTrue(reject_fault(expected,observed['output'],'equality_true')['rejected'])
        with self.assertRaises(AssertionError):
            reject_fault(expected,expected,'equality_true')

    def test_pair_load_cannot_mint_proof(self):
        l,s=seeded(); before=s.identity()
        result=s.execute(request('LOAD_PAIR',7,4),'synthetic.C.load')
        self.assertEqual(result['output']['receipt']['code'],'OUT_OF_DOMAIN')
        self.assertEqual(before,s.identity())
        forged={'receipt':dict(result['output']['receipt'],operation_status='OK',code=None,stage=None),'proof':'UNIT'}
        self.assertTrue(reject_fault(result['output'],forged,'mint_proof')['rejected'])

    def test_primitive_replay_is_deterministic(self):
        summaries=[]
        for _ in range(2):
            l,s=seeded()
            s.execute(request('SET','u',9),'synthetic.C.replay.set')
            s.execute(request('OBSERVE'),'synthetic.C.replay.observe')
            summaries.append(l.summary())
        self.assertEqual(summaries[0],summaries[1])

    def test_byte_work_reserved_before_buffer_growth(self):
        for cap,maximum_bytes in ((1,0),(2,32)):
            ledger=Ledger(cap=cap)
            with self.assertRaises(Refusal):
                ledger.serialize({'synthetic':'x'*65},'synthetic.bytes')
            self.assertEqual(ledger.buffer_bytes,maximum_bytes)
            ledger.private_cleanup()
            self.assertEqual(ledger.buffer_bytes,0)

    def test_malformed_status_is_independently_checked(self):
        l,s=seeded()
        req=request('SET','u',True)
        result=s.execute(req,'synthetic.C.invalid')
        result['output']['receipt']['operation_status']='REFUSED'
        with self.assertRaises(AssertionError):
            validate_result(s,Oracle(l,'synthetic.oracle'),req,result,'synthetic.invalid')

    def test_writer_rejects_unbound_or_accepted_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            writer=derive.Writer(Path(directory)/'new')
            for name in derive.FILES[:-1]:
                writer.write(name,{'synthetic':True,'status':'DERIVED_PENDING_INDEPENDENT_ACCEPTANCE'})
            with self.assertRaises(ValueError):
                writer.write('manifest.json',{'files':{},'acceptance':'PENDING'})
            with self.assertRaises(ValueError):
                writer.write('manifest.json',{'files':writer.hashes.copy(),'acceptance':'PASS'})
            self.assertFalse((writer.destination/'manifest.json').exists())

    def test_synthetic_driver_checks_math_and_semantics(self):
        # Distinct synthetic tape; never any registered nominal/control case.
        tape=[request('SET','u',9),request('SET','u',9),request('STEP',0,-1),
              request('STEP',1,-1),request('OBSERVE'),request('SET_EQUAL',0,-1),
              request('STEP',0,1),request('OBSERVE')]
        for arm in 'ABCD':
            result,faults=derive.execute_case(arm,tape,Budget(),'synthetic.driver')
            self.assertEqual(len(result['records']),len(tape))
            self.assertEqual(faults,[])
            self.assertTrue(result['records'][1]['unchanged'])
            self.assertTrue(any(key.startswith('REFERENCE.') for key in result['ledger']['counts']))
            combined=Counter(result['setup_counts'])+Counter(result['final_check_counts'])
            for row in result['records']:
                combined.update(row['counts'])
            self.assertEqual(dict(combined),result['ledger']['counts'])


if __name__=='__main__':
    unittest.main()
