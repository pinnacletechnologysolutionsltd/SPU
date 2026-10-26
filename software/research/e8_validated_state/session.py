"""Trusted private registry binds admitted state to one immutable context/session."""
from contextlib import contextmanager
from ..e8_root_images.tables import context,storage_inventory
from ..e8_root_images.reference import check_context
from ..e8_root_images.wire import HEADER
from ..lattice_drycount.meter import Meter
from .handles import StateKey,BufferKey,Export


class Session:
    def __init__(self,trace=False):
        self._ctx=context()
        self._setup_check=check_context(self._ctx)  # executed, cost NOT instrumented
        self._prefix=HEADER+bytes.fromhex(self._ctx.root_hash)+bytes.fromhex(self._ctx.basis_hash)
        self._m=Meter(trace)
        self._m.stage='resident_ownership'
        self._m.allocate('context',storage_inventory(self._ctx)['static_total_bits'])
        self._m.allocate('session',32+64+64+32+32)
        self._states,self._buffers,self._next={}, {},1
        self._failures=[]

    @contextmanager
    def _operation(self,name):
        m=self._m
        m.stage=name
        before=set(m.live)
        try:
            with m.frame(16,8):
                yield
        except Exception as error:
            m.stage=name+'/refusal_cleanup'
            for allocation in list(m.live):
                if allocation not in before:
                    m.release(allocation)
            self._failures.append(dict(operation=name,reason=str(error)))
            raise

    def _state(self,key):
        m=self._m
        m.test(type(key) is StateKey,'STATE_HANDLE_TYPE','type_check')
        m.test(key in self._states,'UNKNOWN_FOREIGN_OR_RETIRED_STATE')
        record=m.read(self._states,key)
        return m.read(record,0),m.read(record,1)

    def _ticket(self):
        self._m.charge('indexed_read')
        return self._m.scalar(self._next,committed=True)

    def _mint(self,images):
        m=self._m
        m.test(len(self._states)<8,'STATE_CAPACITY','range_compare')
        uid=self._ticket()
        nxt=m.scalar(m.op('add',uid,m.constant(1)),committed=True)
        m.allocate('state/'+str(uid),384)  # state256 + registry entry128
        m.charge('move',5); m.charge('indexed_write',2)
        key=StateKey()
        self._states[key]=(uid,tuple(images)); self._next=nxt
        return key

    def _publish(self,name,payload):
        m=self._m
        m.test(len(self._buffers)<8,'EXPORT_CAPACITY','range_compare')
        nxt=m.scalar(m.op('add',self._next,m.constant(1)),committed=True)
        m.charge('move',4); m.charge('indexed_write',2)
        key=BufferKey(); result=Export(payload,key)
        self._buffers[key]=(result,name); self._next=nxt
        return result

    def import_wire(self,packet):
        from .packet import import_wire
        with self._operation('import'):
            return import_wire(self,packet)

    def transform(self,key,j,side='left'):
        from .transform import transform
        with self._operation('transform'):
            return transform(self,key,j,side)

    def export_wire(self,key):
        from .packet import export_wire
        with self._operation('export_wire'):
            return export_wire(self,key)

    def materialize(self,key,vector):
        from .materialize import materialize
        with self._operation('export_vector'):
            return materialize(self,key,vector)

    def retire(self,key):
        with self._operation('retire'):
            uid,_=self._state(key)
            self._m.release('state/'+str(uid))
            self._m.charge('indexed_write'); del self._states[key]

    def release_export(self,result):
        with self._operation('release_export'):
            m=self._m
            m.test(type(result) is Export,'EXPORT_TYPE','type_check')
            m.test(result.key in self._buffers,'UNKNOWN_FOREIGN_OR_RELEASED_EXPORT')
            original,name=m.read(self._buffers,result.key)
            m.test(original is result,'EXPORT_RECORD_IDENTITY')
            m.release(name); m.charge('indexed_write'); del self._buffers[result.key]

    def report(self):
        return dict(self._m.report(),setup_validation='EXECUTED UNMETERED',
                    setup_construction='UNMETERED; existing cached context',
                    scope='single serial session; modeled registry/buffers; observer copies excluded',
                    permitted_internal_operations=['LEFT simple reflection'],
                    live_states=len(self._states),live_exports=len(self._buffers),
                    failures=list(self._failures),status='PREPARATION_NOT_QUALIFIED')

    def events(self):
        return list(self._m.events) if self._m.events is not None else None
