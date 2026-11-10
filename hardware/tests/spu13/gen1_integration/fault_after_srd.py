"""Directed case FA (fault after SRD) on the frozen Gen-1 RTL; separate from the seven frozen cases.

usage: fault_after_srd.py OUT_DIR [--freeze FIXTURE_JSON]
The golden program with word 10 (SRD S0,2) given a nonzero reserved byte: the frontend rejects it at fetch
after SRDs at PC 8 and 9 have read slices 0 and 1. The bench is generated into OUT_DIR (no .v file enters
the tree); the RTL is compiled from the frozen portable filelist after the same 17-source hash check as the
seven-case runner. The RTL frame is the reference. It is also compared with the contract prediction
(docs/GEN1_ARCHITECTURAL_CONTRACT.md section 9: slices already read are sent). A no-override control must
produce the golden success frame. Exit 0 only if every check holds; --freeze then writes the fixture."""
import hashlib, json, re, subprocess, sys, zlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FILELIST = ROOT / 'hardware/boards/artix7/wukong_v3/cpu_v02/filelists/candidate_portable.f'
GOLDEN_SRC = HERE / 'fixtures/source_hashes.sha256'
SEVEN = HERE / 'fixtures/expected_records.json'
WORD, BAD = 10, 0x7200020000000001
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
BENCH = """`timescale 1ns/1ps
module fault_after_srd_sim;
  reg clk = 0, rn = 0; wire tx; integer nbytes = 0; real last_t = 0.0; reg [7:0] b; reg [3:0] pst = 0;
  always #10 clk = ~clk;
  cpu_board_2r_top u(.sys_clk(clk), .raw_rst_n(rn), .uart_tx(tx));
  localparam real BIT_NS = 217 * 40.0;
  initial begin
    #1; if (!$test$plusargs("NO_OVERRIDE")) u.cpu.f.rom[%d] = 64'h%016x;
    $display("ROMWORD %%016h", u.cpu.f.rom[%d]); #199 rn = 1;
  end
  always @(posedge u.cpu_clk) begin
    if (u.cpu.retire) $display("RETIRE %%0d %%0d", u.cpu.f.pc, u.cpu.status);
    if (u.cpu.f.state == 4'd7 && pst != 4'd7) $display("FAULT_ENTER %%0d %%0d", pst, u.cpu.f.pc);
    pst <= u.cpu.f.state;
  end
  always @(negedge tx) if (rn) begin : rx
    integer i; #(BIT_NS * 1.5);
    for (i = 0; i < 8; i = i + 1) begin b[i] = tx; if (i < 7) #(BIT_NS); end
    #(BIT_NS); if (tx !== 1'b1) $display("FRAME_ERROR"); $display("RX %%02h", b); nbytes = nbytes + 1; last_t = $realtime;
  end
  initial begin #200; forever begin #100000;
    if ((nbytes > 0 && $realtime - last_t > 1.0e6) || $realtime > 5.2e6) begin $display("END %%0d", nbytes); $finish; end
  end end
endmodule
""" % (WORD, BAD, WORD)

def main(out, freeze=None):
    out = Path(out).resolve(); out.mkdir(parents=True)
    checks, res = [], {'script_sha256': sha(__file__), 'filelist_sha256': sha(FILELIST)}
    ok = lambda n, c, o: checks.append({'name': n, 'ok': bool(c), 'observed': repr(o)[:400]})
    gs = subprocess.run(['sha256sum', '-c', str(GOLDEN_SRC)], capture_output=True, text=True, cwd=ROOT)
    ok('17 shared RTL sources match golden', gs.returncode == 0 and gs.stdout.count(': OK') == 17, gs.stdout[-200:])
    seven = json.loads(SEVEN.read_text()); rom = [int(w, 16) for w in seven['0']['rom']]; rom[WORD] = BAD
    (out / 'bench.v').write_text(BENCH); res['bench_sha256'] = sha(out / 'bench.v')
    res['icarus'] = subprocess.run(['iverilog', '-V'], capture_output=True, text=True).stdout.splitlines()[0]
    files = [l.split()[1] for l in FILELIST.read_text().splitlines() if l.startswith('sv ')]
    c = subprocess.run(['iverilog', '-g2012', '-Ihardware/rtl/arch', '-Ihardware/rtl/core/spu13', '-o', str(out / 'sim.vvp'),
                        str(out / 'bench.v')] + files, capture_output=True, text=True, cwd=ROOT)
    (out / 'compile.log').write_text(c.stdout + c.stderr); ok('compile', c.returncode == 0, c.stderr[-300:])
    def run(tag, extra):
        r = subprocess.run(['vvp', '-n', str(out / 'sim.vvp')] + extra, capture_output=True, text=True, timeout=300, cwd=ROOT)
        (out / f'{tag}.log').write_text(r.stdout + r.stderr)
        rx = bytes(int(x, 16) for x in re.findall(r'^RX ([0-9a-f]{2})$', r.stdout, re.M))
        return rx, [list(map(int, t)) for t in re.findall(r'^RETIRE (\d+) (\d+)$', r.stdout, re.M)], r.stdout
    frame, retires, log = run('case_FA', [])
    ok('override applied', f'ROMWORD {BAD:016x}' in log, log[:60])
    ok('exactly 33 bytes, no framing error', len(frame) == 33 and 'FRAME_ERROR' not in log, len(frame))
    ok('CRC-32 valid', zlib.crc32(frame[:29]).to_bytes(4, 'little') == frame[29:], frame.hex())
    body = bytes([0xA5, 1, 2, 0x03, WORD]) + (13).to_bytes(4, 'little') + bytes(20)    # contract section 9 prediction
    ok('RTL equals contract prediction (slices 0,1 kept)', frame == body + zlib.crc32(body).to_bytes(4, 'little'), frame.hex())
    ok('fault entered at fetch for PC 10', re.search(r'^FAULT_ENTER 2 10$', log, re.M) is not None, '')
    ctrl, _, _ = run('control_no_override', ['+NO_OVERRIDE'])
    ok('negative control: no override gives golden frame', ctrl.hex() == seven['0']['frame'], ctrl.hex())
    res.update(checks=checks, rom=['%016x' % w for w in rom], frame=frame.hex(), retires=retires,
               verdict='PASS' if all(x['ok'] for x in checks) else 'FAIL')
    (out / 'results.json').write_text(json.dumps(res, indent=1) + '\n')
    print(res['verdict'], sum(x['ok'] for x in checks), '/', len(checks))
    if freeze and res['verdict'] == 'PASS':
        fx = {'name': 'FA', 'description': 'fault after SRD: word 10 rejected at fetch after slices 0,1 were read',
              'reference': 'frozen Gen-1 RTL simulation (not the seven-case oracle)', 'rom': res['rom'],
              'fault': True, 'pc': WORD, 'mask': 3, 'cause': 'fetch_reject', 'retires': retires, 'frame': res['frame'],
              'provenance': {k: res[k] for k in ('script_sha256', 'bench_sha256', 'filelist_sha256', 'icarus')}}
        Path(freeze).write_text(json.dumps(fx, indent=1) + '\n'); print('frozen', freeze, sha(freeze))
    return 0 if res['verdict'] == 'PASS' else 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == '--freeze' else None))
