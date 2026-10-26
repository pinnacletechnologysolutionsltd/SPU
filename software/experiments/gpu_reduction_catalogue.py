"""GCR-1 nine-scene catalogue; full comparisons require authorized detached job."""
import argparse,copy,hashlib,json,sys
from dataclasses import asdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from software.spu_gpu_eval.device_model import pixel_decision
from software.spu_gpu_eval.packet import compile_packet
from software.spu_gpu_eval.scene import parse_scene_data,parse_scene_bytes
from software.experiments.gpu_reduction_candidates import prepare
from software.experiments.gpu_reduction_oracle import (
    observe,MissingObservation,plane_identity,exact_original,expression)


def identity():
    rom = ROOT/'hardware/rtl/arch/gpu_reciprocal_lut_q15.mem'
    names = ('device_arithmetic.py','device_packet.py','device_model.py','scene.py')
    dependencies = {n:hashlib.sha256((ROOT/'software/spu_gpu_eval'/n).read_bytes()).hexdigest() for n in names}
    return dict(rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),
                preparation_sha256=hashlib.sha256(json.dumps(dependencies,sort_keys=True).encode()).hexdigest())


def corpus(directory):
    directory.mkdir(parents=True,exist_ok=False)
    base = json.loads((ROOT/'examples/gpu/t1d_two_triangle.json').read_text())
    rows = [('baseline',base),('vertex_b',json.loads((ROOT/'examples/gpu/t1d_two_triangle_vertex_b.json').read_text()))]
    for variant in range(1,8):
        data = copy.deepcopy(base)
        triangles = data['triangles']
        if variant == 1:
            for triangle in triangles:triangle['vertices'].reverse()
        if variant in (2,3,6,7):
            for index,triangle in enumerate(triangles):
                depth = {2:0,3:1000,6:1000+index,7:65535}[variant]
                for vertex in triangle['vertices']:vertex[2]=depth
        if variant in (4,5):
            triangles[1]['vertices']=copy.deepcopy(triangles[0]['vertices'])
            if variant==5:
                for vertex in triangles[1]['vertices']:vertex[2]+=1
        rows.append((f'variant{variant}',data))
    if compile_packet(parse_scene_data(base)) != (ROOT/'fixtures/gpu_t1d_scene_wire_64b.bin').read_bytes():
        raise ValueError('Baseline packet identity differs')
    hashes = {}
    for name,data in rows:
        parse_scene_data(data)
        raw = (json.dumps(data,sort_keys=True,indent=2)+'\n').encode()
        (directory/(name+'.json')).write_bytes(raw)
        hashes[name]=hashlib.sha256(raw).hexdigest()
    (directory/'manifest.json').write_text(json.dumps(hashes,indent=2)+'\n')
    return rows


def compare(data,candidate,identities,points=None,original_frame=None):
    scene,original,_ = prepare(data,'ORIGINAL',identities)
    _,reduced,details = prepare(data,candidate,identities)
    details['original_prepared'] = [asdict(p) for p in original.depth]
    details['candidate_prepared'] = [asdict(p) for p in reduced.depth]
    details['candidate_edges'] = [t.edges for t in reduced.decoded.triangles]
    if not details['eligible']:
        return dict(verdict='UNSUPPORTED',reason='INELIGIBLE',planned=0,evaluated=0,missing=0,
                    mismatches=0,depth_pairs=0,diagnostics=details)
    coordinates = points if points is not None else ((x,y) for y in range(480) for x in range(640))
    mismatch = exact_mismatch = discrepancy = depth_pairs = evaluated = 0
    first = None
    identities_match = plane_identity(scene,reduced)
    for x,y in coordinates:
        before = pixel_decision(original,x,y)
        after = pixel_decision(reduced,x,y)
        try:
            a = original_frame[y*640+x] if original_frame is not None else observe(before)
            b = observe(after)
        except MissingObservation as error:
            return dict(verdict='UNSUPPORTED',reason=str(error),coordinate=[x,y],evaluated=evaluated,
                        missing=1,planned=307200 if points is None else len(points),
                        mismatches=mismatch,depth_pairs=depth_pairs,diagnostics=details)
        exact_a,exact_b = exact_original(scene,x,y),expression(reduced,x,y)
        bad = a != b
        bad_exact = exact_a != exact_b
        # Existing device approximation is diagnostic, independent of candidate verdict.
        device_values = tuple((i,value) for i,value in a[2])
        discrepancy += int(device_values != exact_a[1])
        mismatch += int(bad);exact_mismatch += int(bad_exact);evaluated += 1
        depth_pairs += len(a[2])
        if first is None and (bad or bad_exact):
            first=dict(coordinate=[x,y],original=before,candidate=after,
                       exact_original=str(exact_a),exact_candidate=str(exact_b))
    if candidate=='C3' and original.depth != reduced.depth:
        identities_match = False
    return dict(verdict='REJECTED' if mismatch or exact_mismatch or not identities_match else 'ACCEPTED',
                planned=307200 if points is None else len(points),evaluated=evaluated,missing=0,
                mismatches=mismatch,exact_mismatches=exact_mismatch,depth_pairs=depth_pairs,
                original_exact_device_discrepancies=discrepancy,plane_identity=identities_match,
                first_counterexample=first,diagnostics=details,lifecycle='UNSUPPORTED')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-corpus',type=Path)
    parser.add_argument('--corpus',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.prepare_corpus:
        if args.corpus or args.output:parser.error('Preparation is a separate command')
        corpus(args.prepare_corpus);return
    if not args.corpus or not args.output:parser.error('Require frozen corpus and new output')
    args.output.mkdir(parents=True,exist_ok=False)
    hashes=json.loads((args.corpus/'manifest.json').read_text())
    if set(hashes)!={'baseline','vertex_b',*(f'variant{i}' for i in range(1,8))}:
        raise ValueError('Nine-scene inventory mismatch')
    rows=[];identities=identity()
    for name,digest in hashes.items():
        raw=(args.corpus/(name+'.json')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Corpus drift')
        data=json.loads(raw);_,original,_=prepare(data,'ORIGINAL',identities)
        frame=[observe(pixel_decision(original,x,y)) for y in range(480) for x in range(640)]
        for candidate in ('C1','C2','C3'):
            result=compare(data,candidate,identities,original_frame=frame)
            if result['verdict']!='UNSUPPORTED' and result['evaluated']!=307200:
                raise ValueError('Incomplete acceptance-capable comparison')
            rows.append(dict(scene=name,candidate=candidate,result=result))
            (args.output/'catalogue.json').write_text(json.dumps(rows,indent=2)+'\n')
            if result.get('missing',0):raise ValueError('Missing evidence prevents integrity PASS')
    (args.output/'stage_pass.json').write_text(json.dumps(dict(status='PASS_CATALOGUE_INTEGRITY',
        applications=len(rows),scope='Nine T1d scenes only; candidate rejections are findings'))+'\n')


if __name__=='__main__':main()
