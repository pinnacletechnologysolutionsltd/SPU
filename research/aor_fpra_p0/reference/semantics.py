"""Fixed six-cell reference execution; no candidate imports or dynamic graph."""
from accounting import Kernels, Refusal, encoded
from hashlib import sha256

PARENTS = ((), (), (0, 1), (0,), (1,), (2,))
TAGS = ('PELL', 'PELL', 'PRODUCT', 'NORM', 'NORM', 'NORM')


def decimal(value):
    if type(value) is int:
        return str(value)
    if isinstance(value, (list, tuple)):
        return [decimal(x) for x in value]
    if isinstance(value, dict):
        return {key: decimal(item) for key, item in value.items()}
    return value


def decode(request, ledger, path):
    ledger.event('ENTER', path+'.ENTER')
    ledger.event('K', path+'.shape')
    if type(request) is not dict or list(request) != ['op','args']:
        raise Refusal('MALFORMED',path+'.shape')
    op,args = request['op'],request['args']
    arities = {'STEP':2,'OBSERVE':0,'SET_EQUAL':2,'SET':2,'LOAD_PAIR':2,
               'EXPAND':1,'PAIR_MUL':4}
    ledger.event('K',path+'.arity')
    if type(op) is not str or op not in arities or type(args) is not list or len(args)!=arities[op]:
        raise Refusal('MALFORMED',path+'.arity')
    for index,value in enumerate(args):
        ledger.event('K',path+'.type.'+str(index))
        expected = str if op=='SET' and index==0 else int
        if type(value) is not expected:
            raise Refusal('MALFORMED',path+'.type.'+str(index))
    ledger.event('K',path+'.domain')
    if (op in ('STEP','SET_EQUAL') and args[0] not in (0,1)
            or op=='STEP' and args[1] not in (-1,1)
            or op=='SET' and args[0]!='u' or op=='LOAD_PAIR'):
        raise Refusal('OUT_OF_DOMAIN',path+'.domain')
    return op,args


class State:
    def __init__(self, ledger, arm, limits=None):
        if arm not in ('A','B','C','D'):
            raise ValueError('arm')
        self.l,self.arm = ledger,arm
        self.f,self.cache,self.primary,self.directory = {},[],[None]*3,[]
        self.limits = dict(E=64,P=256,R=512,O=256)
        self.limits.update(limits or {})
        l = ledger
        l.phase = 'SETUP'
        l.event('ENTER','reset.ENTER')
        def seed(name,value,kind='int'):
            l.event('COPY','reset.'+name)
            item=l.allocate(value,'reset.'+name,kind,True)
            self.f[name]=item
            return item
        self.c={str(n):seed('constant.'+str(n),n) for n in (-1,0,1,2,3)}
        self.c.update({name:seed('limit.'+name,self.limits[name]) for name in ('E','P','R','O')})
        seed('g',0); seed('u',0); seed('uv',0)
        for node in range(6):
            seed('id.'+str(node),node,'id')
            seed('v.'+str(node),0)
            seed('tag.'+str(node),TAGS[node],'tag')
            seed('valid.'+str(node),True,'bool')
            if node<3:
                seed('k.'+str(node),0)
            else:
                seed('norm.'+str(node),1)
                l.event('PROOF','reset.proof.'+str(node))
                seed('proof.'+str(node),'UNIT','tag')
            for index,parent in enumerate(PARENTS[node]):
                seed('parent.'+str(node)+'.'+str(index),parent,'id')
                seed('snapshot.'+str(node)+'.'+str(index),0)
        for node in range(3):
            at='cache.'+str(node)
            entry={'id':seed(at+'.id',node,'id'), 'valid':seed(at+'.valid',False,'bool'),
                   'key':seed(at+'.key',0,'key'), 'ref':seed(at+'.ref',None,'null'),'pair':None}
            if arm in 'AB':
                pair=l.pair(l.copy(self.c['1'],at+'.a'),l.copy(self.c['0'],at+'.b'),at)
                pair.a.retained=pair.b.retained=True
                self.primary[node]=pair
                seed('primary.ref.'+str(node),pair.identity,'ref')
                for key,value,kind in (('valid',True,'bool'),('ref',pair.identity,'ref')):
                    l.drop(entry[key]); entry[key]=seed(at+'.'+key,value,kind)
                entry['pair']=pair
                l.event('INSTALL',at)
            self.cache.append(entry)
        # A fixed directory makes absent-rung valid/key reads concrete. No pairs
        # are precomputed. All arms pay the same initialization, including helpers.
        for index in range(64):
            at='ladder.'+str(index)
            self.directory.append({'valid':seed(at+'.valid',False,'bool'),
                                   'key':seed(at+'.key',index,'key'),
                                   'ref':seed(at+'.ref',None,'null'),'pair':None})
        self.kernels=Kernels(l,self.c)
        # Directory/header slots belong to their containers, not a second map.
        self.f={key:value for key,value in self.f.items()
                if not key.startswith(('cache.','ladder.'))}

    def value(self,name):
        return self.f[name].value

    def receipt(self, fields=None, status='OK',code=None,stage=None):
        f=fields if fields is not None else self.f
        return decimal({'g':f['g'].value,'versions':[f['v.'+str(i)].value for i in range(6)],
                        'snapshots':[[f['snapshot.'+str(i)+'.'+str(j)].value
                                      for j in range(len(PARENTS[i]))] for i in range(6)],
                        'fresh':[True]*6 if status=='OK' else None,
                        'operation_status':status,'code':code,'stage':stage})

    def identity(self):
        def entries(items,ladder=False):
            return [{'valid':x['valid'].value,'key':x['key'].value if ladder else str(x['key'].value),
                     'ref':x['ref'].value,'id':None if ladder else x['id'].value,
                     'pair':None if x['pair'] is None else decimal(x['pair'].values())}
                    for x in items]
        return {'fields':{key:decimal(item.value) if item.kind=='int' else item.value for key,item in self.f.items()},
                'primary':[None if x is None else decimal(x.values()) for x in self.primary],
                'cache':entries(self.cache),'ladder':entries(self.directory,True)}

    def validate(self,path):
        l,visited,entries=self.l,set(),[]
        def visit(node):
            at=path+'.'+str(node)
            l.event('VISIT',at); l.event('PROBE',at+'.visited')
            if node in visited:
                return
            local=[]
            try:
                tag=l.copy(self.f['tag.'+str(node)],at+'.tag'); local.append(tag)
                valid=l.copy(self.f['valid.'+str(node)],at+'.valid'); local.append(valid)
                l.event('K',at+'.tag')
                if tag.value!=TAGS[node]:
                    raise Refusal('INVALID_STATE',at+'.tag')
                l.event('K',at+'.valid')
                if not valid.value:
                    raise Refusal('INVALID_STATE',at+'.valid')
                if node>=3:
                    proof=l.copy(self.f['proof.'+str(node)],at+'.proof'); local.append(proof)
                    l.event('PROOF',at+'.proof'); l.event('K',at+'.proof_test')
                    if proof.value!='UNIT':
                        raise Refusal('INVALID_STATE',at+'.proof_test')
                for index,parent in enumerate(PARENTS[node]):
                    snap=l.copy(self.f['snapshot.'+str(node)+'.'+str(index)],at+'.snapshot.'+str(index))
                    version=None
                    try:
                        version=l.copy(self.f['v.'+str(parent)],at+'.parent.'+str(index))
                        l.event('K',at+'.compare.'+str(index))
                        if snap.value!=version.value:
                            raise Refusal('STALE',at+'.compare.'+str(index))
                    finally:
                        l.drop(snap,version)
                    visit(parent)
                entries.append(l.copy(self.f['id.'+str(node)],at+'.visited_insert'))
                visited.add(node)
            finally:
                l.drop(*reversed(local))
        try:
            for root in range(6):
                visit(root)
        finally:
            l.drop(*entries)
            visited.clear()

    def stage_receipt(self,fields,path):
        l=self.l
        copied={}
        order=['g']+['v.'+str(i) for i in range(6)]
        order += ['snapshot.'+str(i)+'.'+str(j) for i in range(6) for j in range(len(PARENTS[i]))]
        for name in order:
            copied[name]=l.copy(fields[name],path+'.'+name)
        for node in range(6):
            l.event('COPY',path+'.fresh.'+str(node))
            l.allocate(True,path,'bool')
        for name,value,kind in (('operation_status','OK','status'),('code',None,'null'),('stage',None,'null')):
            l.event('COPY',path+'.'+name)
            l.allocate(value,path,kind)
        return self.receipt(copied)

    def execute(self,request,path,fault=None):
        l=self.l
        before=self.identity()
        fields=dict(self.f)
        cache=[dict(x) for x in self.cache]
        directory=[dict(x) for x in self.directory]
        primary=list(self.primary)
        cache_events=[]
        wire=None
        pending={}
        journal_inputs=[]
        cache_dirty=set()
        l.phase=('OBSERVE' if request.get('op')=='OBSERVE' else 'EVENT') if type(request) is dict else 'CONTROL'
        def put(name,source):
            fields[name]=source
            pending[name]=source
        def scalar(value,kind='int'):
            return l.allocate(value,path,kind)
        def change_entry(entry,key,source,at):
            prior=entry[key]
            entry[key]=source
            cache_dirty.add((int(at.rsplit('.',1)[1]),key))
            if not prior.retained:
                l.drop(prior)
        def flush():
            journal_inputs.extend(x for x in pending.values() if not x.retained)
            order=['g','u','uv']
            for node in range(6):
                suffix=str(node)
                order += ['id.'+suffix,'v.'+suffix,'tag.'+suffix,'valid.'+suffix]
                order += ['k.'+suffix] if node<3 else ['norm.'+suffix,'proof.'+suffix]
                order += [part+'.'+suffix+'.'+str(index)
                          for index in range(len(PARENTS[node])) for part in ('parent','snapshot')]
                order += ['primary.ref.'+suffix]
                for name in order:
                    if name in pending:
                        fields[name]=l.copy(pending.pop(name),path+'.journal.'+name)
                if node<3:
                    for key in ('valid','key','ref'):
                        if (node,key) in cache_dirty:
                            if not cache[node][key].retained:
                                journal_inputs.append(cache[node][key])
                            cache[node][key]=l.copy(cache[node][key],path+'.journal.cache.'+suffix+'.'+key)
            if pending:
                raise AssertionError('unregistered journal field')
        try:
            op,args=decode(request,l,path)
            decoded=[scalar(x,'tag' if type(x) is str else 'int') for x in args]
            if op in ('STEP','SET_EQUAL','OBSERVE'):
                self.validate(path+'.validate')
            changed=False
            if op in ('STEP','SET_EQUAL','SET'):
                names=['g']
                if op=='STEP':
                    target=args[0]
                    names += ['k.0','k.1','v.'+str(target),'v.2',
                              'norm.'+str(target+3),'norm.5']
                elif op=='SET_EQUAL':
                    names += ['k.'+str(args[0])]
                else:
                    names += ['u','uv']
                plan={name:l.copy(self.f[name],path+'.plan.'+name) for name in names}
                one=l.copy(self.c['1'],path+'.plan.1')
                argv=[l.copy(x,path+'.plan.arg.'+str(i)) for i,x in enumerate(decoded)]
                if op=='STEP':
                    target,delta=args
                    l.event('A',path+'.exponent')
                    k=l.allocate(plan['k.'+str(target)].value+delta,path)
                    if fault=='inverse_sign' and self.arm in 'CD':
                        l.drop(k)
                        k=scalar(plan['k.'+str(target)].value-delta)
                    for node in (target,2):
                        if node==2:
                            other=plan['k.'+str(1-target)]
                            l.event('A',path+'.product_exponent')
                            kr=scalar(k.value-other.value if fault=='product_exponent' and self.arm in 'CD' else k.value+other.value)
                        item=k if node==target else kr
                        bound=l.copy(self.c['E'],path+'.E.'+str(node)+'.bound')
                        try:
                            l.event('K',path+'.E.'+str(node))
                            if abs(item.value)>bound.value:
                                raise Refusal('EXPONENT_LIMIT',path+'.E.'+str(node))
                        finally:
                            l.drop(bound)
                        l.guard(item,self.c['R'],path+'.k.'+str(node)+'.R')
                        l.guard(item,self.c['P'],path+'.k.'+str(node)+'.P')
                        put('k.'+str(node),item)
                    for name in ('g','v.'+str(target),'v.2'):
                        value=l.arithmetic('A',[plan[name],one],lambda a,b:a+b,path+'.'+name,self.c['R'],self.c['P'])
                        put(name,value)
                    for node in (target,2,target+3,5):
                        at=path+'.dependency.'+str(node)
                        l.event('VISIT',at)
                        if node!=target:
                            l.event('EVAL',at)
                        if node<3:
                            if self.arm in 'AB':
                                sign=argv[1]
                                if (fault=='inverse_sign' and node==1 or fault=='product_exponent' and node==2):
                                    sign=scalar(-sign.value)
                                pair=primary[node]
                                primary[node]=self.kernels.pair((pair.a,pair.b),at,sign)
                                put('primary.ref.'+str(node),scalar(primary[node].identity,'ref'))
                        else:
                            proof=l.copy(self.f['proof.'+str(node)],at+'.proof')
                            l.event('PROOF',at); l.event('K',at+'.proof_test')
                            if proof.value!='UNIT':
                                raise Refusal('INVALID_STATE',at+'.proof_test')
                            l.drop(proof)
                            l.event('K',at+'.early_cutoff')
                            if plan['norm.'+str(node)].value!=one.value:
                                raise AssertionError('reference norm certificate/value inconsistency')
                    for node in (2,target+3,5):
                        for index,parent in enumerate(PARENTS[node]):
                            name='snapshot.'+str(node)+'.'+str(index)
                            if not (fault=='stale_snapshot' and node==2 and index==0):
                                put(name,fields['v.'+str(parent)])
                    for node in (target,2):
                        at=path+'.cache.'+str(node)
                        if fault=='old_key' and node==target:
                            continue
                        l.event('INVALIDATE',at)
                        cache_events.append([node,'INVALIDATE'])
                        change_entry(cache[node],'valid',scalar(False,'bool'),at)
                        change_entry(cache[node],'ref',scalar(None,'null'),at)
                        cache[node]['pair']=None
                        if self.arm in 'AB':
                            l.event('INSTALL',at)
                            cache_events.append([node,'INSTALL'])
                            change_entry(cache[node],'valid',scalar(True,'bool'),at)
                            change_entry(cache[node],'key',scalar(fields['v.'+str(node)].value,'key'),at)
                            change_entry(cache[node],'ref',scalar(primary[node].identity,'ref'),at)
                            cache[node]['pair']=primary[node]
                    changed=True
                elif op=='SET_EQUAL':
                    l.event('K',path+'.same_exponent')
                    if argv[1].value!=plan['k.'+str(args[0])].value:
                        raise Refusal('OUT_OF_DOMAIN',path+'.same_exponent')
                else:
                    l.event('K',path+'.same_scalar')
                    changed=argv[1].value!=plan['u'].value
                    if changed:
                        put('u',argv[1])
                        l.guard(fields['u'],self.c['R'],path+'.u.R')
                        l.guard(fields['u'],self.c['P'],path+'.u.P')
                        for name in ('g','uv'):
                            out=l.arithmetic('A',[plan[name],one],lambda a,b:a+b,path+'.'+name,self.c['R'],self.c['P'])
                            put(name,out)
                flush()
                l.event('COPY',path+'.output.changed')
                changed_slot=scalar(changed,'bool')
                receipt=self.stage_receipt(fields,path+'.receipt')
                l.drop(*plan.values(),one,*argv)
                l.drop(*journal_inputs)
                output={'changed':changed_slot.value,'receipt':receipt}
            elif op=='OBSERVE':
                pairs=[]
                for node in range(3):
                    at=path+'.cell.'+str(node)
                    l.event('PROBE',at+'.cache')
                    valid=l.copy(cache[node]['valid'],at+'.valid')
                    key=l.copy(cache[node]['key'],at+'.key')
                    version=l.copy(fields['v.'+str(node)],at+'.version')
                    l.event('K',at+'.hit')
                    hit=valid.value and key.value==version.value
                    if fault=='old_key' and cache[node]['pair'] is not None:
                        hit=True
                    cache_events.append([node,'HIT' if hit else 'MISS'])
                    l.drop(valid,key,version)
                    if not hit:
                        pair=self.kernels.expand(fields['k.'+str(node)],directory,at+'.expand')
                        entry={'id':cache[node]['id'],'pair':pair}
                        key_version=l.copy(fields['v.'+str(node)],at+'.key_version')
                        for name,value,kind in (('valid',True,'bool'),
                                               ('key',key_version.value,'key'),
                                               ('ref',pair.identity,'ref')):
                            l.event('COPY',at+'.journal.'+name)
                            entry[name]=scalar(value,kind)
                        l.drop(key_version)
                        cache[node]=entry
                    pair=cache[node]['pair']
                    for suffix,item in (('a',pair.a),('b',pair.b)):
                        l.guard(item,self.c['O'],at+'.export.'+suffix,'COEFFICIENT_LIMIT')
                    pairs.append(pair.values())
                    l.event('COPY',at+'.output_view')
                    l.allocate(pair.identity,at,'ref')
                norms=[]
                for node in (3,4,5):
                    l.event('PROOF',path+'.norm.'+str(node))
                    norm=l.copy(fields['norm.'+str(node)],path+'.norm.'+str(node))
                    norms.append(norm.value)
                ka=l.copy(fields['k.0'],path+'.equal.k0')
                kb=l.copy(fields['k.1'],path+'.equal.k1')
                l.event('K',path+'.equal')
                equal=scalar(True if fault=='equality_true' else ka.value==kb.value,'bool')
                l.drop(ka,kb)
                output={'pairs':decimal(pairs),'norms':decimal(norms),
                        'equal':equal.value,
                        'receipt':self.stage_receipt(fields,path+'.receipt')}
                wire=l.serialize(output,path+'.serialize')
            elif op in ('EXPAND','PAIR_MUL'):
                if op=='EXPAND':
                    pair=self.kernels.expand(decoded[0],directory,path+'.helper')
                else:
                    pair=self.kernels.pair(decoded,path+'.helper')
                l.event('COPY',path+'.helper.output_view')
                l.allocate(pair.identity,path,'ref')
                output={'pair':decimal(pair.values()),'receipt':self.stage_receipt(fields,path+'.receipt')}
            # Reserve all publication work before making any retained changes.
            for index,(old,new) in enumerate(zip(self.directory,directory)):
                if old['pair'] is not new['pair']:
                    l.event('INSTALL',path+'.ladder.'+str(index))
            if op=='OBSERVE':
                for index,(old,new) in enumerate(zip(self.cache,cache)):
                    if old['pair'] is not new['pair']:
                        l.event('INSTALL',path+'.cache.'+str(index))
            l.event('COMMIT',path+'.COMMIT')
            l.published_serial_bytes+=0 if wire is None else len(wire)
            self.f,self.cache,self.directory,self.primary=fields,cache,directory,primary
            self.retain_reachable()
            l.private_cleanup()
            return {'output':output,'before':before,'after':self.identity(),'refused':False,
                    'cache_events':cache_events,'wire_sha256':None if wire is None else sha256(wire).hexdigest(),
                    'discarded_wire_bytes':0}
        except Refusal as error:
            if error.code!='WORK_LIMIT':
                l.last_failed={'event':l.previous,'previous':l.before_previous,'code':error.code}
            discarded=l.buffer_bytes
            l.private_cleanup()
            if self.identity()!=before:
                raise AssertionError('refusal mutated committed state')
            status='INVALID' if error.code=='MALFORMED' else 'REFUSED'
            receipt=self.receipt(status=status,code=error.code,stage=error.stage)
            diagnostic=encoded({'receipt':receipt})
            if len(diagnostic)>1024:
                raise AssertionError('diagnostic budget')
            l.diagnostics['bytes']+=len(diagnostic)
            l.diagnostics['READ']+=12
            l.diagnostics['COPY']+=16
            return {'output':{'receipt':receipt},'before':before,'after':before,'refused':True,
                    'cache_events':cache_events,'wire_sha256':None,'discarded_wire_bytes':discarded}

    def retain_reachable(self):
        l=self.l
        reachable=list(self.f.values())
        pairs=[x for x in self.primary if x is not None]
        for entry in self.cache+self.directory:
            reachable += [entry[key] for key in ('valid','key','ref')]
            if 'id' in entry:
                reachable.append(entry['id'])
            if entry['pair'] is not None:
                pairs.append(entry['pair'])
        for pair in pairs:
            reachable += [pair.a,pair.b]
        names={x.name for x in reachable}
        for value in list(l.slots.values()):
            if value.name in names:
                value.retained=True
            elif value.retained:
                l.drop(value)
        pair_ids={x.identity for x in pairs}
        for key in list(l.pairs):
            if key not in pair_ids:
                del l.pairs[key]
