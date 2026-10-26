#!/usr/bin/env python3
"""Run exact Python Surd oracle cases through the RTL multiply/normalizer."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments.surd_wide_correctness_vectors import self_test, vectors


def hx(value, width):
    return f"{value & ((1 << width)-1):0{(width+3)//4}x}"


def write_vectors(path, rows, width):
    nbits = 2*width+2
    with path.open("w") as stream:
        for row in rows:
            a,b,d,c,e,f = row['operands']
            ex = row['expected']
            raw = ex['raw'] or (0,0,0)
            reduced = ex['reduced'] or (0,0,0)
            outa,outb,outd = ex['destination']
            fields = [
                hx(a,width),hx(b,width),hx(d,width),hx(c,width),hx(e,width),hx(f,width),
                hx(raw[0],nbits),hx(raw[1],nbits),hx(raw[2],2*width),
                hx(reduced[0],nbits),hx(reduced[1],nbits),hx(reduced[2],nbits),
                hx(outa,width),hx(outb,width),hx(outd,width),
                str(int(ex['request_normalization'])),str(int(ex['invalid'])),
                str(int(ex['overflow']))]
            stream.write(" ".join(fields)+"\n")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--widths',type=int,nargs='+',default=[32,64])
    parser.add_argument('--lanes',type=int,nargs='+',default=[1,2,5])
    parser.add_argument('--limit',type=int,default=0,
                        help='debug only: run the first N vectors per width')
    args=parser.parse_args()
    out=args.output_dir if args.output_dir.is_absolute() else ROOT/args.output_dir
    out.mkdir(parents=True,exist_ok=True)
    reference_rows=[row for width in (32,64) for row in vectors(width)]
    self_test(reference_rows)
    tb=ROOT/'hardware/tests/math/surd_mul_normalizer_vectors_harness.v'
    rtl=[ROOT/'hardware/rtl/math/surd_smul_unit.v',
         ROOT/'hardware/rtl/math/surd_binary_gcd3.v',
         ROOT/'hardware/rtl/math/surd_exact_quotient.v',
         ROOT/'hardware/rtl/math/surd_normalize_unit.v',tb]
    for width in args.widths:
        rows=list(vectors(width))
        if args.limit:
            rows=rows[:args.limit]
        vecfile=out/f'w{width}.vectors.txt'
        write_vectors(vecfile,rows,width)
        for lanes in args.lanes:
            image=out/f'w{width}_lanes_{lanes}.vvp'
            compile_cmd=['iverilog','-g2012','-s','surd_mul_normalizer_vectors_tb',
                         '-P',f'surd_mul_normalizer_vectors_tb.W={width}',
                         '-P',f'surd_mul_normalizer_vectors_tb.LANES={lanes}',
                         '-o',str(image),*map(str,rtl)]
            subprocess.run(compile_cmd,cwd=ROOT,check=True)
            run=subprocess.run(['vvp',str(image),f'+VECTORS={vecfile}'],
                               cwd=ROOT,check=True,text=True,capture_output=True)
            sys.stdout.write(run.stdout)
    print('PASS Python oracle consistency and RTL vector campaigns')


if __name__=='__main__':
    main()
