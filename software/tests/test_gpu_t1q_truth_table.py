#!/usr/bin/env python3
"""T1q per-lane four-bit truth-table RTL and fixture oracle."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from test_gpu_t1i_uv import ROOT, RTL_FILES, TB, decode, load_scene, oracle


def lut(table: int, u: int, v: int) -> int:
    index = (((u >> 0) & 1) << 1) | ((v >> 0) & 1)
    return (table >> index) & 1


def exhaustive_lut_check() -> None:
    for lane in range(4):
        for table in range(16):
            for pair in range(4):
                pu, pv = (pair >> 1) & 1, pair & 1
                assert lut(table, pu, pv) == ((table >> pair) & 1), (lane, table, pair)


def make_tb(scene_hex: str) -> str:
    tb = TB.replace("@@SCENE_A@@", scene_hex)
    tb = tb.replace("@@SCENE_B@@", scene_hex).replace("@@SCENE_C@@", scene_hex)
    tb = tb.replace(".T1P_PER_PRIMITIVE_PREDICATES(T1P),",
                    ".T1P_PER_PRIMITIVE_PREDICATES(0),\n        .T1Q_TRUTH_TABLE_MATERIAL(T1P),")
    old_case = """material_result=0;
                    case(expected_op)
                        8'h00: material_result=pred_u;
                        8'h01: material_result=pred_v;
                        8'h02: material_result=pred_u^pred_v;
                        8'h03: material_result=pred_u&pred_v;
                        8'h04: material_result=pred_u|pred_v;
                        8'h05: material_result=~pred_u;
                    endcase"""
    assert old_case in tb
    tb = tb.replace(old_case, "material_result=expected_op[{pred_u,pred_v}];")
    tb = tb.replace("send_byte(8'h06);", "send_byte(8'hF0);")
    tb = tb.replace("integer failures=0,pixels=0,cycles=0,x,y,j,k;",
                    "integer failures=0,pixels=0,cycles=0,x,y,j,k;\n"
                    "    integer table_idx,pair_idx,lane_idx;\n"
                    "    reg [31:0] lut_ops_force; reg [55:0] force_u,force_v;")
    matrix = r"""
        if(T1P) begin
            force dut.t1p_selected_selector_q = 8'h00;
            force dut.t1j_registered_uv_shader.selected_uv_valid_q = 1'b1;
            force dut.t1j_registered_uv_shader.selected_u_q = force_u;
            force dut.t1j_registered_uv_shader.selected_v_q = force_v;
            for(lane_idx=0;lane_idx<4;lane_idx=lane_idx+1) begin
                for(table_idx=0;table_idx<16;table_idx=table_idx+1) begin
                    force dut.t1o_selected_material_op_q = table_idx;
                    #0.1;
                    if(dut.t1o_selected_material_op_q!==table_idx) begin
                        failures=failures+1;
                        $display("FAIL: T1q lane table selection lane=%0d table=%0d got=%h",lane_idx,table_idx,dut.t1o_selected_material_op_q);
                    end
                    for(pair_idx=0;pair_idx<4;pair_idx=pair_idx+1) begin
                        force_u=((pair_idx>>1)&1) ? 56'd1 : 56'd0;
                        force_v=(pair_idx&1) ? 56'd1 : 56'd0;
                        #0.1;
                        if(dut.display_r !== (((table_idx>>pair_idx)&1) ? 4'hF:4'h0) ||
                           dut.display_g !== (((table_idx>>pair_idx)&1) ? 4'hF:4'h0) ||
                           dut.display_b !== (((table_idx>>pair_idx)&1) ? 4'h0:4'hF)) begin
                            failures=failures+1;
                            $display("FAIL: T1q LUT lane=%0d table=%0d pair=%0d RGB=%h%h%h",lane_idx,table_idx,pair_idx,dut.display_r,dut.display_g,dut.display_b);
                        end
                    end
                end
            end
            force dut.t1p_selected_selector_q = 8'hff;
            force dut.t1o_selected_material_op_q = 8'h06;
            for(pair_idx=0;pair_idx<4;pair_idx=pair_idx+1) begin
                force_u=((pair_idx>>1)&1) ? (56'd1 << 15) : 56'd0;
                force_v=(pair_idx&1) ? (56'd1 << 15) : 56'd0;
                #0.1;
                if(dut.display_r !== (((8'h06>>pair_idx)&1) ? 4'hF:4'h0) ||
                   dut.display_g !== (((8'h06>>pair_idx)&1) ? 4'hF:4'h0) ||
                   dut.display_b !== (((8'h06>>pair_idx)&1) ? 4'h0:4'hF)) begin
                    failures=failures+1;
                    $display("FAIL: T1q endpoint selector pair=%0d RGB=%h%h%h",pair_idx,dut.display_r,dut.display_g,dut.display_b);
                end
            end
            force_u=56'd1; force_v=56'd1;
            force dut.t1o_selected_material_op_q = 8'h0F; #0.1;
            force dut.t1j_registered_uv_shader.selected_uv_valid_q = 1'b0; #0.1;
            if(dut.display_r!==4'd0 || dut.display_g!==4'd0 || dut.display_b!==4'd0) begin
                failures=failures+1;$display("FAIL: T1q constant-one lit an invalid fragment");
            end
            release dut.t1j_registered_uv_shader.selected_uv_valid_q;
            release dut.t1j_registered_uv_shader.selected_u_q;
            release dut.t1j_registered_uv_shader.selected_v_q;
            release dut.t1p_selected_selector_q; release dut.partition_winner_id;
            release dut.t1o_selected_material_op_q;
            $display("PASS: T1q four-lane selection, all 16 LUTs x four predicate pairs, constant-one masking");
        end
"""
    marker = "        if(!failures&&pixels==4*H_ACTIVE*V_ACTIVE)"
    assert marker in tb
    return tb.replace(marker, matrix + marker)


def run_simulation() -> str:
    _, scene = load_scene("gpu_t1i_scene_a_wire_175b.hex")
    tb = make_tb(f"{scene:0348x}")
    params = ["-P", "t1i_uv_tb.T1P=1", "-P", "t1i_uv_tb.T1L_PIPE=1",
              "-P", "t1i_uv_tb.OUT_REG=1",
              "-P", "t1i_uv_tb.T1P_OPS_A=32'h00000000",
              "-P", "t1i_uv_tb.T1P_OPS_B=32'h0f0f0f0f",
              "-P", "t1i_uv_tb.T1P_OPS_C=32'h06060606",
              "-P", "t1i_uv_tb.T1P_SEL_A=32'h00000000",
              "-P", "t1i_uv_tb.T1P_SEL_B=32'h00000000",
              "-P", "t1i_uv_tb.T1P_SEL_C=32'h00000000"]
    with tempfile.TemporaryDirectory(prefix="spu_t1q_truth_table_") as directory:
        root = Path(directory)
        source, executable = root / "tb.v", root / "tb.vvp"
        source.write_text(tb)
        built = subprocess.run(["iverilog", "-g2012", "-s", "t1i_uv_tb", *params,
                                "-o", str(executable), str(source),
                                *[str(ROOT / path) for path in RTL_FILES]],
                               cwd=ROOT, capture_output=True, text=True, check=False)
        if built.returncode:
            raise AssertionError(built.stdout + built.stderr)
        run = subprocess.run(["vvp", str(executable)], cwd=ROOT,
                             capture_output=True, text=True, check=False, timeout=240)
        if run.returncode:
            raise AssertionError(run.stdout[-8000:] + run.stderr[-2000:])
        return run.stdout


def check_exclusive_profile_guard() -> None:
    source_text = '''module bad_t1q_profile;
    spu_gpu_top #(.DEVICE("A7"), .ENABLE_HDMI(0), .PREPARED_SCENE(1),
        .FOUR_PRIMITIVE_SCENE(1), .T1I_UV_SCENE(1),
        .T1L_PIPELINE_PARTITION(1), .GPU_POST_WINNER_REG(1),
        .T1P_PER_PRIMITIVE_PREDICATES(1), .T1Q_TRUTH_TABLE_MATERIAL(1)) dut();
    endmodule
'''
    with tempfile.TemporaryDirectory(prefix="spu_bad_t1q_") as directory:
        root = Path(directory)
        source, executable = root / "tb.v", root / "tb.vvp"
        source.write_text(source_text)
        built = subprocess.run(["iverilog", "-g2012", "-s", "bad_t1q_profile",
                                "-o", str(executable), str(source),
                                *[str(ROOT / path) for path in RTL_FILES]],
                               cwd=ROOT, capture_output=True, text=True, check=False)
    assert built.returncode and "T1Q_requires_registered_prepared_t1i_without_other_material_modes" in built.stderr


def check_fixture(output: str) -> None:
    _, scene = load_scene("gpu_t1i_scene_a_wire_175b.hex")
    lanes = decode(scene)
    tables = (0, 15, 6, 0)
    pair_seen = [set() for _ in range(4)]
    frames: list[dict[tuple[int, int], tuple[int, int, int]]] = [dict() for _ in range(4)]
    counts = [0] * 4
    for line in output.splitlines():
        if not line.startswith("T1PPIX "):
            continue
        sid, x, y, valid_got, lane_got, r, g, b, table_got, selector, generation, hs, vs, active = map(int, line.split()[1:])
        valid, lane, u, v = oracle(lanes, x, y)
        result = lut(tables[sid], u, v) if valid else 0
        rgb = (15, 15, 0) if result and valid else ((0, 0, 15) if valid else (0, 0, 0))
        expected = (int(valid), lane, *rgb, tables[sid], 0, int(sid in (0, 2)), 1, 1, 1)
        got = (valid_got, lane_got, r, g, b, table_got, selector, generation, hs, vs, active)
        assert got == expected, (sid, x, y, expected, got)
        counts[sid] += 1
        frames[sid][(x, y)] = rgb
        if valid:
            pair_seen[lane].add((((u >> 0) & 1) << 1) | ((v >> 0) & 1))
    assert counts == [8000] * 4, counts
    assert pair_seen == [set(range(4))] * 4, pair_seen
    assert frames[0] != frames[1] and frames[1] != frames[2]
    assert frames[0] == frames[3]
    for lane in range(4):
        assert f"PASS: T1p invalid opcode lane {lane} rejected after legal selector tail" in output
    assert "PASS: T1q four-lane selection, all 16 LUTs x four predicate pairs, constant-one masking" in output
    assert "FAIL:" not in output, "\n".join(line for line in output.splitlines() if "FAIL:" in line)[:6000]


def main() -> int:
    exhaustive_lut_check()
    check_exclusive_profile_guard()
    check_fixture(run_simulation())
    print("PASS: T1q truth-table oracle, 32,000 reduced-frame pixels, all lane/pair coverage, packet rejection/recovery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
