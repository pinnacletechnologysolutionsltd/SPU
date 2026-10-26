#!/usr/bin/env python3
"""Run the software-only IVM frontier experiment; prints durable JSON evidence.

Direct nonzero exit on any assertion/exception. No FPGA timing claims.
Run from repository root: python3 software/tools/run_ivm_frontier_experiment.py
"""
import hashlib
import json
import random
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lib import ivm_frontier_model as model
from lib.ivm_frontier_model import (Triangle,Meter,SITES,OUTPUT,render,adapt,
    make_adapter,exact_reference,prepare_triangle,prepare_scene,signed_bits,square_threshold_render)
from lib.ivm_frontier_protocol import Receiver,packet,tri_packet


def lift(u,v,k=0):
    return (3*k,u-k,v-k,-k-u-v)  # depth=12k, integer projected u,v


def triangle(ident, points, ks=(0,0,0), colour=None):
    return Triangle(ident,colour if colour is not None else (0xF00 if ident==0 else 0x0F0),
                    tuple(lift(u,v,k) for (u,v),k in zip(points,ks)))


def fixtures():
    cases = []
    shared = (triangle(0,[(-2,-2),(2,-2),(2,2)]),
              triangle(1,[(-2,-2),(2,2),(-2,2)]))
    cases.append(('shared',shared))
    cases.append(('winding',tuple(replace(t,vertices=tuple(reversed(t.vertices))) for t in shared)))
    cases.append(('rational_depth',tuple(triangle(i,[(0,0),(size,0),(0,size)],(0,1,0))
                                         for i,size in enumerate((7,8)))))
    cases.append(('tie',(shared[0],replace(shared[0],ident=1,colour=0x00F))))
    fractional = Triangle(0,0xF00,((1,0,0,-1),(1,2,0,-3),(1,0,2,-3)))
    cases.append(('fractional',(fractional,shared[1])))
    skinny = Triangle(0,0xF00,((0,0,0,0),(1,0,0,-1),(0,1,0,-1)))
    cases.append(('minimum_area',(skinny,shared[1])))
    extremes = (Triangle(0,0xF00,((9,9,-9,-9),(9,-9,9,-9),(-9,-9,9,9))),
                Triangle(1,0x0F0,((9,-9,-9,9),(9,9,-9,-9),(-9,-9,9,9))))
    cases.append(('range_extrema',extremes))
    rng = random.Random(46020260908)
    for n in range(48):
        ts = []
        while len(ts) < 2:
            vv = []
            for _ in range(3):
                abc = [rng.randint(-2,2) for _ in range(3)]
                vv.append((*abc,-sum(abc)))
            t = Triangle(len(ts),0xF00 if not ts else 0x0F0,tuple(vv))
            try:
                prepare_triangle(t,1,Meter())
            except ValueError:
                continue
            ts.append(t)
        cases.append((f'random_{n:02d}',tuple(ts)))
    return cases


def begin(rx,epoch,ts):
    stream = packet(1,epoch,b'\x01\x02')+b''.join(tri_packet(epoch,t) for t in ts)+packet(3,epoch)
    # Exercise byte parser across every possible packet-internal boundary.
    for byte in stream:
        rx.feed(bytes([byte]))
    return len(stream)


def activate(rx,epoch,ts):
    size = begin(rx,epoch,ts)
    for _ in range(3):
        rx.tick()
    assert rx.phase == 'READY',rx.events
    rx.feed(packet(4,epoch))
    assert rx.phase == 'QUEUED'
    scene = rx.tick(boundary=True)
    assert scene.epoch == epoch
    return scene,size+len(packet(4,epoch))


def must_raise(kind, fn):
    try:
        fn()
    except kind:
        return
    raise AssertionError(f'negative control did not raise {kind.__name__}')


def protocol_checks(a,b,native_map):
    checks = 0
    # Commit at each prep phase and before/after each frame boundary.
    for ticks in range(4):
        for boundary_first in (False,True):
            rx = Receiver()
            old,_ = activate(rx,1,a)
            begin(rx,2,b)
            for _ in range(ticks):
                rx.tick()
            if boundary_first:
                rx.tick(boundary=True)
            ready = rx.phase == 'READY'
            rx.feed(packet(4,2))
            assert rx.active is old
            now = rx.tick(boundary=True)
            assert now.epoch == (2 if ready else 1)
            for scene in (old,now):
                samples,_ = render(scene)
                assert all(p[0] == scene.epoch for p in adapt(samples,native_map,scene.epoch))
            checks += 1
    rx = Receiver()
    old,_ = activate(rx,1,a)
    # Truncate at every byte, then expire: active state must not change.
    msg = tri_packet(2,b[0])
    for stop in range(len(msg)):
        r = Receiver(); r.active = old
        r.feed(packet(1,2,b'\x01\x02')+msg[:stop]); r.expire(); r.tick(True)
        assert r.active is old and r.phase == 'IDLE'
        checks += 1
    for mutate in ('crc','version','length','sum','range','id','colour','profile','missing','duplicate','degenerate','stale','wrong_epoch','busy','opcode'):
        r = Receiver(); r.active = old
        r.feed(packet(1,2,b'\x01\x02'))
        p = tri_packet(2,b[0])
        if mutate == 'crc': p = p[:-1]+bytes([p[-1]^1])
        elif mutate == 'version':
            p = bytearray(p); p[2]=2
            import binascii
            p[-2:] = binascii.crc_hqx(p[:-2],0xffff).to_bytes(2,'little')
        elif mutate == 'length': p = b'IV\x01\x02\x02\x00\xff'
        elif mutate in ('sum','range'):
            v = (1,0,0,0) if mutate == 'sum' else (10,-10,0,0)
            p = tri_packet(2,replace(b[0],vertices=(v,*b[0].vertices[1:])))
        elif mutate == 'id': p = tri_packet(2,replace(b[0],ident=3))
        elif mutate == 'colour': p = tri_packet(2,replace(b[0],colour=4096))
        elif mutate == 'profile':
            r.expire(); p=packet(1,2,b'\x02\x02')
        elif mutate == 'missing': p=packet(3,2)
        elif mutate == 'duplicate': p+=p
        elif mutate == 'degenerate':
            t=replace(b[0],vertices=(b[0].vertices[0],)*3)
            p=tri_packet(2,t)+tri_packet(2,b[1])+packet(3,2)
        elif mutate == 'stale':
            r.expire(); p=packet(1,1,b'\x01\x02')
        elif mutate == 'wrong_epoch': p=tri_packet(3,b[0])
        elif mutate == 'busy': p=packet(1,3,b'\x01\x02')
        elif mutate == 'opcode': p=packet(99,2)
        r.feed(p)
        for _ in range(4): r.tick(True)
        assert r.active is old and any(e[0]=='REJECT' for e in r.events),mutate
        checks+=1
    # Wrong commit policy must be distinguishable from correct delayed activation.
    r=Receiver(unsafe_commit=True); activate(r,1,a); begin(r,2,b); r.tick()
    r.feed(packet(4,2)); mixed=r.tick(True)
    must_raise(ValueError,lambda:render(mixed)); checks+=1
    # Entire frame snapshot remains usable even after activation of a new scene.
    new,_=activate(rx,2,b)
    old_pixels,_=render(old); new_pixels,_=render(new)
    assert adapt(old_pixels,native_map,1)
    mixed_pixels=list(new_pixels); mixed_pixels[native_map[0]]=old_pixels[native_map[0]]
    must_raise(ValueError,lambda:adapt(mixed_pixels,native_map,2)); checks+=1
    begin(rx,3,a); rx.tick(); rx.reset()
    assert rx.active is None and rx.pending is None and not rx.buffer; checks+=1
    return checks


def main():
    nm,dist,nmap_ops=make_adapter()
    sm,_,_=make_adapter(True)
    # Every nearest-site choice verified over a much larger lattice and an
    # independent rational interval distance reference, including tie order.
    from fractions import Fraction as F
    lo=F(17320508075688772935274463415058723,10**34); hi=lo+F(1,10**34)
    assert lo*lo<3<hi*hi
    for (x,y),index in zip(OUTPUT,nm):
        i,j=SITES[index]
        ba=x*x+y*y+i*i+i*j+j*j-2*x*i-x*j; bb=-y*j
        for v in range(-8,9):
            for u in range(-8,9):
                da=x*x+y*y+u*u+u*v+v*v-2*x*u-x*v-ba; db=-y*v-bb
                assert da==db==0 or min(da+db*lo,da+db*hi)>0
                if da==db==0: assert (v,u)>=(j,i)
    assert max(max(abs(i),abs(j)) for i,j in (SITES[k] for k in nm))==3
    cases=fixtures(); rx=Receiver(); rows=[]; maxbits=Counter(); ops=Counter()
    native_ops=Counter(); square_ops=Counter(); threshold_ops=Counter(); samples_checked=0
    for epoch,(name,ts) in enumerate(cases,1):
        scene,wire_bytes=activate(rx,epoch,ts)
        np,nc=render(scene); sp,sc=render(scene,True)
        tp,tc,threshold_work=square_threshold_render(scene)
        assert tp==sp,('square threshold compilation',name)
        threshold_ops.update(tc.ops)
        for site,n,s in zip(SITES,np,sp):
            assert n==exact_reference(scene,site),('native',name,site)
            assert s==exact_reference(scene,site,True),('square',name,site)
            samples_checked+=2
        native=adapt(np,nm,epoch); square=adapt(sp,sm,epoch)
        truth=tuple(exact_reference(scene,p,True) for p in OUTPUT)
        assert square==truth
        mismatches=sum(n[1:]!=s[1:] for n,s in zip(native,truth))
        coverage=sum((n[1] is None)!=(s[1] is None) for n,s in zip(native,truth))
        occlusion=sum(n[1] is not None and s[1] is not None and n[1]!=s[1] for n,s in zip(native,truth))
        channel_error=sum(abs(((n[2]>>shift)&15)-((s[2]>>shift)&15)) for n,s in zip(native,truth) for shift in (0,4,8))
        rows.append(dict(scene=name,mismatched_pixels=mismatches,coverage_changes=coverage,
                         winner_changes=occlusion,rgb_absolute_error=channel_error,rgb_mae=channel_error/75,wire_bytes=wire_bytes))
        native_ops.update(nc.ops); square_ops.update(sc.ops)
        for meter in (rx.meter,nc,sc):
            for tag,bits in meter.bits.items(): maxbits[tag]=max(maxbits[tag],bits)
    checks=protocol_checks(cases[0][1],cases[4][1],nm)
    # Exact tie, fractional-site and min-area witnesses are actually exercised.
    s,_=activate(Receiver(),1,cases[2][1]); p,_=render(s)
    assert p[SITES.index((1,1))][1]==1
    n0,d0=s.triangles[0].numerator,s.triangles[0].denominator
    n1,d1=s.triangles[1].numerator,s.triangles[1].denominator
    z=[F(A*3+B*3+C,D) for (A,B,C),D in ((n0,d0),(n1,d1))]
    assert z==[F(12,7),F(3,2)] and int(z[0])==int(z[1])
    bad=replace(s,order_field=tuple(-x for x in s.order_field))
    bp,_=render(bad); assert bp[SITES.index((1,1))]!=p[SITES.index((1,1))]
    narrow=model.CAPS['H']; model.CAPS['H']=32767
    try:
        must_raise(OverflowError,lambda:activate(Receiver(),1,cases[6][1]))
    finally: model.CAPS['H']=narrow
    # Reference failure is fatal instead of interpreting precision exhaustion as success.
    minimum=prepare_triangle(cases[5][1][0],1,Meter()); assert minimum.denominator==3
    frac=prepare_triangle(cases[4][1][0],1,Meter()); assert any(U%3 or V%3 for U,V in frac.uv)
    shared,_=activate(Receiver(),1,cases[0][1])
    double_hits=0
    for u in (-1,0,1):
        for v in (-1,0,1):
            owners=[]
            for t in shared.triangles:
                owners.append(all((f:=A*3*u+B*3*v+C)>0 or (f==0 and model.ownership((A,B,C)))
                                  for A,B,C in t.edges))
            assert sum(owners)==1
    for i in (-1,0,1):
        counts=[]
        for t in shared.triangles:
            counts.append(all(A*3*i+B*3*i+C>=0 for A,B,C in t.edges))
        double_hits+=all(counts)
    assert double_hits==3
    # Prove wire-range endpoints and reject one unit beyond; semantic width is five bits.
    assert signed_bits(9)==5 and signed_bits(-9)==5
    widths={'quadray':5,'projected_UVh':signed_bits(36),'edge_AB':signed_bits(72),
            'edge_C':signed_bits(2*model.R**2),'D_unsigned':model.DMAX.bit_length(),
            'N_AB':signed_bits(model.NAB),'N_C':signed_bits(model.NC),
            'H_AB':signed_bits(model.HAB),'H_C':signed_bits(model.HC),
            'native_accumulator':signed_bits(model.ACC),
            'square_real':signed_bits(model.SQUARE_REAL),'square_surd':signed_bits(model.SQUARE_IMAG),
            'square_sign_intermediate':signed_bits(model.CAPS['sign_gap'])}
    # Stored prepared state: six edges, six ownership bits, H, RGB, IDs and metadata.
    scene_bits=6*(2*widths['edge_AB']+widths['edge_C'])+6+2*widths['H_AB']+widths['H_C']+24+2+16+8
    # Fractions only converted to decimal for reporting the already-exact distances.
    maxdist=max(float(a+b*lo) for a,b in dist)
    root=Path(__file__).resolve().parents[2]
    files=['software/lib/ivm_frontier_model.py','software/lib/ivm_frontier_protocol.py',
           'software/tools/run_ivm_frontier_experiment.py']
    evidence=dict(status='PASS',scope='software-only; no FPGA speed/energy claim',
        profile=dict(q_bound=9,triangles=2,native_sites=len(SITES),square_sites=len(SITES),output_pixels=25,
                     pitch=1,seed=46020260908,guard_note='equal allocated patches, different exterior footprints; not area-density optimal'),
        sources={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files},
        scene_count=len(cases),exact_sample_checks=samples_checked,protocol_checks=checks,
        negative_controls=['premature commit mixed prepared epoch','stale adapter sample',
                           'all-inclusive edges: 3 double hits','reversed H winner','undersized 16-bit H bound'],
        widths=widths,observed_signed_bits=dict(maxbits),
        operations=dict(scene_preparation_total=dict(rx.meter.ops),native_total=dict(native_ops),
                        square_total=dict(square_ops),native_map_total_once=dict(nmap_ops.ops),
                        square_threshold_compilation_total=dict(threshold_ops),
                        square_threshold_per_frame=threshold_work,
                        adapter_per_frame=dict(sample_reads=25,arithmetic=0)),
        storage=dict(prepared_scene_bits=scene_bits,prepared_double_bank_bytes=(2*scene_bits+7)//8,
                     packet_buffer_bytes=24,staging_geometry_payload_bytes=30,
                     sample_buffer_bits=len(SITES)*14+16,double_sample_buffer_bytes=(2*(len(SITES)*14+16)+7)//8,
                     native_map_bits=25*(len(SITES)-1).bit_length(),native_map_unique_sites=len(set(nm)),
                     square_threshold_table_bits=7*len(model.AXIS)*len(model.AXIS).bit_length()+7,
                     setup_N_D_scratch_bits=2*(2*widths['N_AB']+widths['N_C']+widths['D_unsigned']),
                     native_scan_register_bits=2*(6*signed_bits(12*model.SITE_RADIUS*model.R+2*model.R**2)+widths['native_accumulator'])+2*(6*signed_bits(6*model.R)+signed_bits(3*model.HAB)),
                     excluded='control flops, Python objects, intermediate pipeline registers, FIFO sizing; estimates not synthesis'),
        reconstruction=dict(max_site_displacement_squared_upper=str(max(a+b*hi if b>=0 else a+b*lo for a,b in dist)),
                            max_site_displacement_approx=maxdist**0.5,
                            mismatched_pixels=sum(r['mismatched_pixels'] for r in rows),
                            coverage_changes=sum(r['coverage_changes'] for r in rows),
                            winner_changes=sum(r['winner_changes'] for r in rows),
                            rgb_absolute_error=sum(r['rgb_absolute_error'] for r in rows),
                            rgb_mae=sum(r['rgb_absolute_error'] for r in rows)/(75*len(rows)),
                            total_pixels=25*len(rows),worst_scene_mismatches=max(r['mismatched_pixels'] for r in rows),
                            rows=rows))
    print(json.dumps(evidence,indent=2))


if __name__=='__main__':
    main()
