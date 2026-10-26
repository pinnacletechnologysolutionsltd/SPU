"""Structural op counts vs generator degree d (curve degree 2d+1), h=1, order 1."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fractions import Fraction as F
from field import *
from curve import PH
import cost


def curve(d):
    a = tuple(S3(k + 1, (-1) ** k) for k in range(d + 1))
    b = tuple(S3(F(1, k + 2), k % 3) for k in range(d + 1))
    return PH(a, b)


def main():
    t = S3(F(2, 5), F(1, 3))
    print("d  curve_deg |  PH surd_mul  poly surd_mul | PH mul+add  poly mul+add | stored coeffs PH / poly")
    for d in range(1, 7):
        c = curve(d)
        s = {n: cost.run_counted(fn, c, t, 1)[1] for n, fn in cost.STRATEGIES.items() if n != "jet_horner"}
        p, q = s["PH"], s["poly_horner"]
        print(f"{d}  {2*d+1:9d} | {p['surd_mul']:12d} {q['surd_mul']:14d} | {p['surd_mul']+p['surd_add']:10d} {q['surd_mul']+q['surd_add']:12d} |"
              f" {2*(2*d+2)+2*(d+1):4d} / {2*(2*d+2)+2*(2*d+1):4d}")


if __name__ == "__main__":
    main()
