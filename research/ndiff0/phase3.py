import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fractions import Fraction as F
from field import *
from curve import *
from closure import *
import cost

H = S3(F(1, 2)); R = S3(0, F(1, 2))  # 1/2, sqrt3/2
ANGLES = {"0": (ONE, ZERO), "30": (R, H), "60": (H, R), "90": (ZERO, ONE), "120": (S3(F(-1, 2)), R), "180": (S3(-1), ZERO),
          "pell u=2+r3 (cos=(2+r3)/... skip)": None}
LAMS = {"2": S3(2), "3": S3(3), "r3": S3(0, 1), "2+r3 (Pell u)": S3(2, 1), "7+4r3 (u^2)": S3(7, 4), "1/4": S3(F(1, 4))}


def main():
    c = sample_curve()
    rows = []
    for k, v in ANGLES.items():
        if v is None:
            continue
        r, _ = rotation(c, *v)
        rows.append(("rotate " + k + "deg", r))
    for k, lam in LAMS.items():
        r, _ = scaling(c, lam)
        rows.append(("scale " + k, r))
    r, g = reparam_t2(c)
    rows.append(("t -> t^2", r))
    print(f"{'transform':22s} PH-property  primitive(h=1)  general(h,a,b)")
    for n, r in rows:
        print(f"{n:22s} {str(r['ph_property']):12s} {str(r['primitive']):15s} {str(r['general'])}   {({k: v for k, v in r.items() if k not in ('ph_property', 'primitive', 'general')} or '')}")
    # cost of evaluating the t^2-reparametrised curve: general-h PH path vs polynomial baselines
    t = S3(F(2, 5))
    for name, fn in cost.STRATEGIES.items():
        _, s = cost.run_counted(fn, g, t, 1)
        print("t^2 curve", name, {k: s[k] for k in ("surd_mul", "surd_add", "rat_mul", "rat_add")})
    return rows


if __name__ == "__main__":
    main()
