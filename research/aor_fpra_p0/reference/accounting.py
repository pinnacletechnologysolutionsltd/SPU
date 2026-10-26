"""Reference primitive replay with typed storage and explicit owned results."""
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from itertools import chain
import json

CATEGORIES = frozenset('A M N K B T COPY READ VISIT PROBE INVALIDATE INSTALL EVAL PROOF COMMIT SERIAL ENTER BYTE32'.split())


class Refusal(Exception):
    def __init__(self, code, stage):
        self.code, self.stage = code, stage
        super().__init__(code, stage)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':'),
                       allow_nan=False) + '\n').encode('utf-8')


def storage(value, kind):
    if kind in ('id', 'key', 'ref'):
        if type(value) is not int or not 0 <= value < 2**64:
            raise ValueError('unsigned eight-byte field required')
        return 64
    if kind == 'status':
        if value not in ('OK', 'INVALID', 'REFUSED'):
            raise ValueError('invalid status')
        return 2
    if kind == 'bool':
        if type(value) is not bool:
            raise TypeError('Boolean required')
        return 1
    if kind == 'null':
        if value is not None:
            raise TypeError('null required')
        return 0
    if kind == 'tag':
        return len(value.encode('ascii')) * 8
    if kind != 'int' or type(value) is not int:
        raise TypeError('exact integer required')
    return 1 + max(1, abs(value).bit_length())


@dataclass(eq=False)
class Scalar:
    name: str
    value: object
    kind: str
    retained: bool = False


@dataclass(eq=False)
class Pair:
    a: Scalar
    b: Scalar
    identity: int

    def values(self):
        return self.a.value, self.b.value


class Budget:
    def __init__(self, maximum=4_000_000):
        self.maximum, self.used = maximum, 0


class Ledger:
    def __init__(self, shared=None, cap=100_000, phase='CONTROL'):
        self.shared = shared if shared is not None else Budget()
        self.cap, self.used, self.phase = cap, 0, phase
        self.counts, self.diagnostics = Counter(), Counter()
        self.digest, self.previous, self.denied = sha256(), None, None
        self.slots, self.pairs = {}, {}
        self.peak, self.pair_peak, self.serial_bytes = 0, 0, 0
        self.attempted_serial_bytes,self.published_serial_bytes=0,0
        self.sequence, self.pair_sequence = 0, 0
        self.last_failed = None
        self.before_previous = None
        self.modeled_used, self.modeled_cap = 0, cap
        self.milestones=[]
        self.live_bits = 0
        self.buffer_bytes = 0

    def event(self, kind, path, phase=None):
        if kind not in CATEGORIES:
            raise ValueError('unknown primitive: ' + kind)
        item = [phase or self.phase, kind, path]
        modeled=item[0]!='REFERENCE'
        if (self.used >= self.cap or self.shared.used >= self.shared.maximum
                or modeled and self.modeled_used >= self.modeled_cap):
            self.denied = {'event': item, 'previous': self.previous}
            raise Refusal('WORK_LIMIT', path)
        self.used += 1
        self.modeled_used += int(modeled)
        self.shared.used += 1
        self.counts[item[0] + '.' + kind] += 1
        self.digest.update(encoded(item))
        self.before_previous,self.previous = self.previous,item
        if (item[0]!='REFERENCE' and (kind in ('T','COMMIT','INSTALL')
                or kind=='N' and path.endswith('.conjugate')
                or kind=='PROBE' and '.ladder.' in path)):
            self.milestones.append([self.used,kind,path])
            self.milestones=self.milestones[-64:]
        self.measure()

    def measure(self):
        self.peak = max(self.peak, self.live_bits + 8*self.buffer_bytes)
        self.pair_peak = max(self.pair_peak, len(self.pairs))

    def allocate(self, value, path, kind='int', retained=False):
        if len(self.slots) >= 512:
            raise Refusal('CAPACITY', path)
        storage(value, kind)
        self.sequence += 1
        item = Scalar(str(self.sequence), value, kind, retained)
        self.slots[item.name] = item
        self.live_bits += storage(value, kind)
        self.measure()
        return item

    def copy(self, source, path):
        if source.name not in self.slots:
            raise AssertionError('read after release')
        if source.retained:
            self.event('READ', path + '.read')
        self.event('COPY', path + '.copy')
        return self.allocate(source.value, path, source.kind)

    def drop(self, *items):
        for item in items:
            if item is not None:
                removed = self.slots.pop(item.name, None)
                if removed is not None:
                    self.live_bits -= storage(removed.value, removed.kind)

    def pair(self, a, b, path):
        if len(self.pairs) >= 64:
            raise Refusal('CAPACITY', path)
        self.pair_sequence += 1
        item = Pair(a, b, self.pair_sequence)
        self.pairs[item.identity] = item
        self.measure()
        return item

    def drop_pair(self, pair):
        self.drop(pair.a, pair.b)
        self.pairs.pop(pair.identity, None)

    def guard(self, item, limit, path, code='ARITH_LIMIT'):
        borrowed = item if not item.retained else self.copy(item, path + '.operand')
        temps = []
        try:
            bound = self.copy(limit, path + '.limit'); temps.append(bound)
            self.event('B', path + '.bits')
            size = self.allocate(max(1, abs(borrowed.value).bit_length()), path); temps.append(size)
            self.event('K', path + '.test')
            test = self.allocate(size.value <= bound.value, path, 'bool'); temps.append(test)
            if not test.value:
                self.last_failed = {'event': self.previous, 'previous':self.before_previous,'code': code}
                raise Refusal(code, path + '.test')
        finally:
            self.drop(*reversed(temps))
            if borrowed is not item:
                self.drop(borrowed)

    def arithmetic(self, kind, operands, calculate, path, raw, coefficient=None):
        self.event(kind, path)
        result = self.allocate(calculate(*(x.value for x in operands)), path)
        try:
            self.guard(result, raw, path + '.R')
            if coefficient is not None:
                self.guard(result, coefficient, path + '.P')
        except BaseException:
            self.drop(result)
            raise
        return result

    def serialize(self, value, path):
        self.event('SERIAL', path)
        buffer = bytearray()
        encoder = json.JSONEncoder(ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        for chunk in chain(encoder.iterencode(value), ('\n',)):
            data = chunk.encode('utf-8')
            offset=0
            while offset<len(data):
                count=min(32-len(buffer)%32,len(data)-offset)
                if len(buffer)+count>65536:
                    raise Refusal('OUTPUT_LIMIT',path)
                if len(buffer)%32==0:
                    self.event('BYTE32',path+'.'+str(len(buffer)//32))
                buffer.extend(data[offset:offset+count])
                self.attempted_serial_bytes+=count
                offset+=count
                self.buffer_bytes=len(buffer)
                self.measure()
        self.serial_bytes += len(buffer)
        return bytes(buffer)

    def private_cleanup(self):
        self.buffer_bytes=0
        for item in list(self.slots.values()):
            if not item.retained:
                self.drop(item)
        for key, pair in list(self.pairs.items()):
            if pair.a.name not in self.slots or pair.b.name not in self.slots:
                del self.pairs[key]

    def summary(self):
        return {'counts': dict(sorted(self.counts.items())), 'used': self.used,
                'modeled_used':self.modeled_used,
                'digest': self.digest.hexdigest(), 'denied': self.denied,
                'first_failure': self.last_failed, 'peak_bits': self.peak,
                'normalization_count':0,
                'pair_peak': self.pair_peak, 'serial_bytes': self.serial_bytes,
                'attempted_serial_bytes':self.attempted_serial_bytes,
                'published_serial_bytes':self.published_serial_bytes,
                'discarded_serial_bytes':self.attempted_serial_bytes-self.published_serial_bytes,
                'diagnostics': dict(self.diagnostics)}


class Kernels:
    def __init__(self, ledger, constants):
        self.l, self.c = ledger, constants

    def pair(self, operands, path, delta=None):
        l, c, local, result = self.l, self.c, [], None
        def copy(item, suffix):
            out = l.copy(item, path + '.' + suffix); local.append(out)
            return out
        try:
            l.event('ENTER', path + '.ENTER')
            v = {name: copy(value, name) for name, value in zip('abcd', operands)}
            if delta is None:
                v['3'] = copy(c['3'], '3')
                schedule = [('ac','M','a','c'), ('bd','M','b','d'),
                            ('3bd','M','3','bd'), ('ad','M','a','d'),
                            ('bc','M','b','c'), ('new_a','A','ac','3bd'), ('new_b','A','ad','bc')]
                release = {'3bd': ('bd','3'), 'ad': ('a','d'), 'bc': ('b','c'),
                           'new_a': ('ac','3bd'), 'new_b': ('ad','bc')}
                positive = True
            else:
                v['delta'] = copy(delta, 'delta')
                for key in ('1','2','3'):
                    v[key] = copy(c[key], key)
                l.event('K', path + '.sign')
                positive = v['delta'].value == 1
                l.drop(v['delta'], v['1'])
                schedule = [('2a','M','2','a'), ('3b','M','3','b'),
                            ('new_a','A','2a','3b'), ('2b','M','2','b'), ('new_b','A','2b','a')]
                release = {'3b': ('3',), 'new_a': ('2a','3b'),
                           '2b': ('b','2'), 'new_b': ('a','2b')}
            for name, kind, left, right in schedule:
                fn = (lambda a,b: a*b) if kind == 'M' else (
                     (lambda a,b: a+b) if positive else (lambda a,b: a-b))
                v[name] = l.arithmetic(kind, [v[left],v[right]], fn, path + '.' + name,
                                       c['R'], c['P'] if name.startswith('new_') else None)
                local.append(v[name])
                l.drop(*(v[x] for x in release.get(name, ())))
            result = l.pair(v['new_a'], v['new_b'], path)
            return result
        finally:
            keep = () if result is None else (result.a, result.b)
            l.drop(*(x for x in local if x not in keep))

    def expand(self, exponent, directory, path):
        """directory is a private overlay; caller owns publication or rollback."""
        l, c, local, answer, acc = self.l, self.c, [], None, None
        def copy(value, suffix):
            item = l.copy(value, path + '.' + suffix); local.append(item)
            return item
        try:
            l.event('ENTER', path + '.ENTER')
            k, zero, one = copy(exponent,'k'), copy(c['0'],'0'), copy(c['1'],'1')
            l.event('K', path + '.zero')
            if k.value == 0:
                answer = l.pair(copy(one,'identity.a'),copy(zero,'identity.b'),path)
                return answer
            n = l.arithmetic('N',[k],abs,path+'.n',c['R']); local.append(n)
            l.event('B', path+'.bits')
            bits = l.allocate(n.value.bit_length(),path); local.append(bits)
            m = l.arithmetic('A',[bits,one],lambda a,b:a-b,path+'.m',c['R']); local.append(m)
            l.drop(bits)
            for index in range(m.value+1):
                at = path+'.ladder.'+str(index)
                l.event('PROBE',at)
                valid,key = copy(directory[index]['valid'],'valid.'+str(index)),copy(directory[index]['key'],'key.'+str(index))
                missing = not valid.value
                l.drop(valid,key)
                if missing:
                    if index == 0:
                        pair = l.pair(copy(c['2'],'L0.a'),copy(c['1'],'L0.b'),at)
                    else:
                        prior = directory[index-1]['pair']
                        pair = self.pair((prior.a,prior.b,prior.a,prior.b),at+'.square')
                    staged = {}
                    for name,value,kind in (('valid',True,'bool'),('key',index,'key'),
                                            ('ref',pair.identity,'ref')):
                        l.event('COPY',at+'.journal.'+name)
                        staged[name] = l.allocate(value,at,kind)
                    directory[index] = dict(staged,pair=pair)
            acc = l.pair(copy(one,'acc.a'),copy(zero,'acc.b'),path)
            for index in range(m.value+1):
                at = path+'.scan.'+str(index)
                l.event('T',at+'.BIT_TEST')
                if (n.value >> index) & 1:
                    rung = directory[index]['pair']
                    new = self.pair((acc.a,acc.b,rung.a,rung.b),at+'.multiply')
                    l.drop_pair(acc)
                    acc = new
            l.drop(n,m)
            l.event('K',path+'.negative')
            if k.value < 0:
                new_b = l.arithmetic('N',[acc.b],lambda x:-x,path+'.conjugate',c['R'],c['P'])
                l.drop(acc.b)
                acc.b = new_b
            l.drop(k)
            answer = acc
            return answer
        finally:
            if acc is not None and acc is not answer:
                l.drop_pair(acc)
            live_pairs = [entry['pair'] for entry in directory if entry['pair'] is not None]
            if answer is not None:
                live_pairs.append(answer)
            keep = {id(x) for pair in live_pairs for x in (pair.a,pair.b)}
            l.drop(*(x for x in local if id(x) not in keep))
