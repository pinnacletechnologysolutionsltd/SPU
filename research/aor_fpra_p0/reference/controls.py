"""Registered stimuli and independently calculated truth/semantic checks."""
from copy import deepcopy
from accounting import Refusal
from pell import Truth, coefficients, product
from semantics import decimal

FAULTS=frozenset(('inverse_sign','product_exponent','old_key','stale_snapshot',
                 'mint_proof','equality_true','bad_proof'))


def request(op,*args):
    return {'op':op,'args':list(args)}


def cases():
    obs=request('OBSERVE')
    plus,minus=request('STEP',0,1),request('STEP',0,-1)
    rows=[
        ([request('STEP',1,-1),obs],{},'inverse_sign'),
        ([plus,request('STEP',1,1),obs],{},'product_exponent'),
        ([obs,plus,obs],{},'old_key'),
        ([obs,plus,obs],{},'stale_snapshot'),
        ([request('LOAD_PAIR',0,0)],{},'mint_proof'),
        ([plus,obs],{},'equality_true'),
        ([obs,obs],{},None),
        ([plus,obs,request('SET_EQUAL',0,1),obs],{},None),
        ([obs,request('SET','u',1),obs],{},None),
        ([plus,minus,obs],{},None),
        ([request('EXPAND',0)],{},None),
        ([plus]*8+[obs,obs],{},None),
        ([minus]*8+[obs],{},None),
        ([plus],{'E':0},None),
        ([obs],{'O':0},None),
        ([obs]+[request('STEP',1,1)]*32+[obs],{'O':31},None),
        ([{'op':'STEP','args':[]}],{'work':0},None),
        ([{'op':'STEP','args':[0]}],{'E':0},None),
        ([request('PAIR_MUL',2,1,2,1)],{'R':1},None),
        ([obs],{},'bad_proof')]
    return [{'id':i,'requests':deepcopy(tape),'limits':limits,'fault':fault}
            for i,(tape,limits,fault) in enumerate(rows,1)]


class Oracle:
    """No cache, ladder, kernel or modeled-state values establish truth."""
    def __init__(self,ledger,prefix):
        self.l,self.prefix=ledger,prefix
        self.sequence=0
        for index in range(23):
            self.charge('COPY','initial_scalar.'+str(index))
        self.truth=Truth()
        self.k,self.v,self.snap=[0]*3,[0]*6,[[],[],[0,0],[0],[0],[0]]
        self.g,self.u,self.uv=0,0,0

    def charge(self,kind,stage):
        self.sequence+=1
        self.l.event(kind,self.prefix+'.'+str(self.sequence)+'.'+stage,'REFERENCE')

    def receipt(self):
        return decimal({'g':self.g,'versions':self.v,'snapshots':self.snap,
                        'fresh':[True]*6,'operation_status':'OK','code':None,'stage':None})

    def advance(self,req):
        op,args=req['op'],req['args']
        if op=='STEP':
            target,delta=args
            self.truth.advance(target,delta,self.charge)
            self.charge('A','exponent'); self.k[target]+=delta
            self.charge('A','product_exponent'); self.k[2]=sum(self.k[:2])
            self.charge('A','generation'); self.g+=1
            for cell in (target,2):
                self.charge('A','version'); self.v[cell]+=1
            self.snap[2]=self.v[:2]
            self.snap[target+3]=[self.v[target]]
            self.snap[5]=[self.v[2]]
        elif op=='SET':
            self.charge('K','scalar_changed')
            if self.u!=args[1]:
                self.u=args[1]
                self.charge('A','generation'); self.g+=1
                self.charge('A','u_version'); self.uv+=1

    def observation(self):
        pairs,norms,equal=self.truth.observe(self.charge)
        return {'pairs':decimal(pairs),'norms':decimal(norms),'equal':equal,
                'receipt':self.receipt()}


def inject(machine,fault,path):
    if fault!='bad_proof':
        raise ValueError('only the pre-request proof mutation is supported here')
    ledger=machine.l
    ledger.event('COPY',path+'.bad_proof','REFERENCE')
    before=machine.f['proof.3']
    machine.f['proof.3']=ledger.allocate('BAD',path,'tag',True)
    ledger.drop(before)


def reject_fault(expected,altered,fault):
    if fault not in FAULTS:
        raise ValueError('unregistered fault')
    if expected==altered:
        raise AssertionError('mutant survived: '+fault)
    return {'fault':fault,'rejected':True,'reason':'independent truth/state mismatch'}


def validate_result(machine,oracle,req,result,path,fault=None):
    """Return independent expected observation; do not reuse replay arithmetic."""
    op=req.get('op')
    if result['refused']:
        receipt=result['output']['receipt']
        oracle.charge('K','refusal_receipt')
        status='INVALID' if receipt['code']=='MALFORMED' else 'REFUSED'
        if receipt['fresh'] is not None or receipt['operation_status']!=status:
            raise AssertionError('invalid refusal receipt')
        if result['before']!=result['after']:
            raise AssertionError('non-atomic refusal')
        expected=oracle.receipt()
        if fault=='stale_snapshot':
            expected['snapshots'][2][0]='0'
        expected.update(fresh=None,operation_status=receipt['operation_status'],
                        code=receipt['code'],stage=receipt['stage'])
        oracle.charge('K','refusal_public_state')
        if receipt!=expected:
            raise AssertionError('refusal public state mismatch')
        return None
    expected_changed=(op=='STEP' or op=='SET' and req['args'][1]!=oracle.u)
    oracle.advance(req)
    if op in ('STEP','SET','SET_EQUAL'):
        oracle.charge('K','changed_match')
        if result['output']['changed']!=expected_changed:
            raise AssertionError('changed flag disagrees')
    if op=='OBSERVE':
        expected=oracle.observation()
        oracle.charge('K','observation_match')
        if fault in ('inverse_sign','product_exponent','old_key','equality_true'):
            reject_fault(expected,result['output'],fault)
            return expected
        if result['output']!=expected:
            raise AssertionError('observation disagrees with independent oracle')
        return expected
    if op in ('EXPAND','PAIR_MUL'):
        expected=decimal(coefficients(req['args'][0],oracle.charge) if op=='EXPAND' else
                         product(req['args'][:2],req['args'][2:],oracle.charge))
        if result['output']['pair']!=expected:
            raise AssertionError('isolated expansion disagrees')
    oracle.charge('K','receipt_match')
    if fault!='stale_snapshot' and result['output']['receipt']!=oracle.receipt():
        raise AssertionError('semantic receipt disagrees')
    if op in ('STEP','SET','SET_EQUAL'):
        return {'changed':expected_changed,'receipt':oracle.receipt()}
    return {'pair':expected,'receipt':oracle.receipt()}


def fault_for_request(case,index,req):
    fault=case['fault']
    if fault=='product_exponent' and index!=1:
        return None
    if fault=='inverse_sign' and req.get('op')!='STEP':
        return None
    if fault in ('old_key','stale_snapshot'):
        return fault
    if fault=='equality_true' and req.get('op')=='OBSERVE':
        return fault
    return fault if fault in ('inverse_sign','product_exponent') else None


def control_verdict(case,records,fault_records,charge=lambda kind,stage:None):
    cid=case['id']
    expected={4:'STALE',5:'OUT_OF_DOMAIN',14:'EXPONENT_LIMIT',15:'COEFFICIENT_LIMIT',
              16:'COEFFICIENT_LIMIT',17:'WORK_LIMIT',18:'MALFORMED',19:'ARITH_LIMIT',
              20:'INVALID_STATE'}
    refused=[row for row in records if row['refused']]
    charge('K','control.refusal')
    if cid in expected:
        if len(refused)!=1 or refused[0]['output']['receipt']['code']!=expected[cid]:
            raise AssertionError('control refusal mismatch')
    elif refused:
        raise AssertionError('unexpected control refusal')
    if cid in (1,2,3,6) and not fault_records:
        raise AssertionError('missing deliberate-fault rejection')
    if cid==8:
        charge('K','control.noop')
        event=records[2]
        if not event['unchanged'] or event['output']['changed']:
            raise AssertionError('SET_EQUAL changed state')
    if cid==7:
        charge('K','control.repeat')
        if records[0]['output']!=records[1]['output']:
            raise AssertionError('repeated observation changed output')
    if cid==9:
        charge('K','control.unrelated')
        if not records[1]['graph_unchanged'] or records[1]['cache_events']:
            raise AssertionError('unrelated SET changed graph/cache')
    if cid==11:
        charge('K','control.identity_ladder')
        if records[0]['ladder_extent']!=[0,0]:
            raise AssertionError('identity populated ladder')
    if cid==12:
        charge('K','control.warm_hit')
        if records[-1]['cache_events']!=[[i,'HIT'] for i in range(3)]:
            raise AssertionError('warm observation failed cache hits')
        charge('K','control.no_warm_powering')
        if any(key.endswith(('.M','.T')) and not key.startswith('REFERENCE.') and value
               for key,value in records[-1]['counts'].items()):
            raise AssertionError('warm observation repeated powering')
    if cid in (12,13):
        observed=[row for row in records if 'pairs' in row['output']]
        charge('K','control.power_applicability')
        arm=records[-1]['last_event'][2].split('.')[2]
        if arm in 'CD':
            charge('B','control.required_ladder_extent')
        expected_extent=(8).bit_length() if arm in 'CD' else 0
        if any(row['ladder_extent'][1]!=expected_extent for row in observed):
            raise AssertionError('unused/missing ladder square or A/B powering')
        if cid==13 and arm in 'CD':
            for row in observed:
                conjugations=[x for x in row['milestones'] if x[1]=='N']
                if len(conjugations)!=2:
                    raise AssertionError('negative factors did not conjugate')
                for number,_,path in conjugations:
                    root=path.rsplit('.conjugate',1)[0]
                    if not any(x[1]=='T' and x[0]<number and x[2].startswith(root+'.scan.')
                               for x in row['milestones']):
                        raise AssertionError('conjugation before positive powering')
    return {'id':cid,'verified':True,'refusals':len(refused)}
