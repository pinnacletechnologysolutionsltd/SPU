#!/usr/bin/env python3
"""Generate vnorm_<material>.mem using the exact hardware mapping (exp LUT + integer arithmetic)
Reads:
 - hardware/common/rtl/gpu/r_rom_<material>.mem (Q16.16)
 - hardware/common/rtl/gpu/exp_lut_256.mem (Q16.16)
 - hardware/common/rtl/gpu/params_<material>.hex (a_q16,re_q16,De_q16)
Writes:
 - hardware/common/rtl/gpu/vnorm_<material>.mem
 - hardware/common/rtl/gpu/vnorm_dissoc_<material>.mem
"""
import os

SCALE = 1 << 16
XMAX_SCALED = 262144

materials = ['carbon','iron']

# read exp lut
exp = []
if os.path.exists('hardware/common/rtl/gpu/exp_lut_256.mem'):
    with open('hardware/common/rtl/gpu/exp_lut_256.mem','r') as f:
        for line in f:
            exp.append(int(line.strip(),16))
# read Padé Q32 coeffs if present
pade_num_q32 = None
pade_den_q32 = None
if os.path.exists('hardware/common/rtl/gpu/pade_num_4_4_q32.mem') and os.path.exists('hardware/common/rtl/gpu/pade_den_4_4_q32.mem'):
    pade_num_q32 = []
    pade_den_q32 = []
    with open('hardware/common/rtl/gpu/pade_num_4_4_q32.mem','r') as f:
        for line in f:
            pade_num_q32.append(int(line.strip(),16))
    with open('hardware/common/rtl/gpu/pade_den_4_4_q32.mem','r') as f:
        for line in f:
            pade_den_q32.append(int(line.strip(),16))

for name in materials:
    rpath = f'hardware/common/rtl/gpu/r_rom_{name}.mem'
    ppath = f'hardware/common/rtl/gpu/params_{name}.hex'
    out_v = f'hardware/common/rtl/gpu/vnorm_{name}.mem'
    out_d = f'hardware/common/rtl/gpu/vnorm_dissoc_{name}.mem'
    if not os.path.exists(rpath) or not os.path.exists(ppath):
        print('Missing files for', name); continue
    # read params
    with open(ppath,'r') as f:
        lines = [l.strip() for l in f if l.strip()]
    a_q16 = int(lines[0],16)
    re_q16 = int(lines[1],16)
    De_q16 = int(lines[2],16)
    # read r values
    r_vals = []
    with open(rpath,'r') as f:
        for line in f:
            v = int(line.strip(),16)
            if v & 0x80000000:
                v -= 1<<32
            r_vals.append(v)
    with open(out_v,'w') as fv, open(out_d,'w') as fd:
        for r_q in r_vals:
            # delta = re - r (signed)
            delta = re_q16 - r_q
            # x_q32 = a_q16 * delta  (signed 64)
            x_q32 = a_q16 * delta
            # if Padé Q32 coeffs are available, evaluate Padé like the hardware does
            if pade_num_q32 is not None:
                x_q32 = a_q16 * delta  # Q32
                # Horner numerator/denominator (Q32 arithmetic)
                acc_num = pade_num_q32[4]
                # acc_num is Python int representing signed 64-bit Q32 value; sign-correct
                def to_signed(v, bits):
                    if v & (1 << (bits-1)):
                        return v - (1 << bits)
                    return v
                acc_num = to_signed(acc_num, 64)
                acc_den = to_signed(pade_den_q32[4], 64)
                for coeff in [pade_num_q32[3], pade_num_q32[2], pade_num_q32[1], pade_num_q32[0]]:
                    coeff_s = to_signed(coeff,64)
                    mult = acc_num * x_q32
                    acc_num = (mult >> 32) + coeff_s
                for coeff in [pade_den_q32[3], pade_den_q32[2], pade_den_q32[1], pade_den_q32[0]]:
                    coeff_s = to_signed(coeff,64)
                    mult = acc_den * x_q32
                    acc_den = (mult >> 32) + coeff_s
                # division: (acc_num << 16) / acc_den -> Q16.16
                if acc_den == 0:
                    exp_q16 = 0
                else:
                    numer = (acc_num << 16)
                    quot = int(numer // acc_den)
                    # wrap to 32-bit two's complement
                    vq = quot & 0xffffffff
                    exp_q16 = vq
                t_q16 = (SCALE - exp_q16) & 0xffffffff
                t2_q32 = ( (t_q16 * t_q16) >> 16 ) & 0xffffffffffffffff
                v_q32 = ( (De_q16 * t2_q32) >> 16 ) & 0xffffffffffffffff
                v_q16 = v_q32 & 0xffffffff
                fd.write('{}\n'.format(1 if v_q16 >= SCALE else 0))
                fv.write('{:08x}\n'.format(v_q16))
            else:
                # fallback to exp LUT
                x_q16 = x_q32 >> 16
                idx_temp = (x_q16 * 255) // XMAX_SCALED
                if idx_temp < 0: idx = 0
                elif idx_temp > 255: idx = 255
                else: idx = idx_temp
                exp_q16 = exp[idx]
                t_q16 = SCALE - exp_q16
                t2_q32 = (t_q16 * t_q16) >> 16
                v_q32 = (De_q16 * t2_q32) >> 16
                v_q16 = v_q32 & 0xffffffff
                fd.write('{}\n'.format(1 if v_q16 >= SCALE else 0))
                fv.write('{:08x}\n'.format(v_q16))
    print('Wrote vnorm for', name)
print('Done')
