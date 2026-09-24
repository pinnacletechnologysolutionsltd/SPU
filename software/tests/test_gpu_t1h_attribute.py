#!/usr/bin/env python3
"""T1h four-lane scalar interpolation and scene-activation qualification."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software" / "lib"))
from gpu_depth_v2_oracle import full_reciprocal  # noqa: E402

RTL_FILES = [
    "hardware/rtl/gpu/spu_gpu_top.v",
    "hardware/rtl/gpu/spu_video_timing.v",
    "hardware/rtl/gpu/spu_scene_loader.v",
    "hardware/rtl/gpu/spu_scene_unpack.v",
    "hardware/rtl/gpu/spu_scene_profile_unpack.v",
    "hardware/rtl/gpu/spu_prepared_scene_control.v",
    "hardware/rtl/gpu/spu_prepared_scene_control4.v",
    "hardware/rtl/gpu/spu_dual_raster.v",
    "hardware/rtl/gpu/spu_quad_raster.v",
    "hardware/rtl/gpu/spu_raster_unit.v",
    "hardware/rtl/gpu/spu_edge_stepper.v",
    "hardware/rtl/gpu/spu_depth_dispatch.v",
    "hardware/rtl/gpu/spu_depth_dispatch4.v",
    "hardware/rtl/gpu/spu_prepared_scalar_attribute4.v",
    "hardware/rtl/gpu/spu_depth_math.v",
    "hardware/rtl/gpu/spu_reciprocal_core.v",
    "hardware/rtl/gpu/spu_shared_mult35.v",
    "hardware/rtl/gpu/spu_attr_stepper.v",
    "hardware/rtl/gpu/spu_depth_compare.v",
    "hardware/rtl/gpu/spu_depth_compare4.v",
    "hardware/rtl/hal/hal_vga.v",
    "hardware/rtl/hal/hal_hdmi.v",
    "hardware/rtl/hal/hal_hdmi_tmds.v",
    "hardware/rtl/hal/hal_hdmi_serdes_a7.v",
]

TB = r"""
`timescale 1ns/1ps
module t1h_attribute_tb;
    localparam integer H_ACTIVE=80, H_FP=2, H_SYNC=2, H_BP=2;
    localparam integer V_ACTIVE=100, V_FP=1, V_SYNC=1, V_BP=1;
    localparam integer HTOTAL=H_ACTIVE+H_FP+H_SYNC+H_BP;
    localparam integer FRAME_CYCLES=HTOTAL*(V_ACTIVE+V_FP+V_SYNC+V_BP);
    localparam [1199:0] SCENE_A=1200'h@@SCENE_A@@;
    localparam [1199:0] SCENE_B=1200'h@@SCENE_B@@;
    localparam [1199:0] SCENE_C=1200'h@@SCENE_C@@;
    reg clk=0, rst_n=0, rx_valid=0;
    reg [7:0] rx_byte=0;
    wire [3:0] vr,vg,vb;
    integer failures=0, cycles=0, pixels=0, scene_id=0;
    integer x,y,j, prior_activation=0;
    reg [1199:0] held_scene;
    reg [223:0] held_active_A;
    reg [27:0] held_active_frac;
    integer final_byte_cycle=0, ready_cycle=0, activation_cycle=0, clear_cycle=0;
    wire [223:0] active_scalar_A_bus={dut.u_t1h_scalar.active_A_attr3,
        dut.u_t1h_scalar.active_A_attr2,dut.u_t1h_scalar.active_A_attr1,
        dut.u_t1h_scalar.active_A_attr0};
    wire [27:0] active_scalar_frac_bus={dut.u_t1h_scalar.active_frac_attr3,
        dut.u_t1h_scalar.active_frac_attr2,dut.u_t1h_scalar.active_frac_attr1,
        dut.u_t1h_scalar.active_frac_attr0};

    spu_gpu_top #(.DEVICE("A7"),.ENABLE_HDMI(0),.PREPARED_SCENE(1),
        .FOUR_PRIMITIVE_SCENE(1),.T1H_SCALAR_SCENE(1),.T1H_SCALAR_DIAG(1),
        .H_ACTIVE(H_ACTIVE),.H_FP(H_FP),.H_SYNC(H_SYNC),.H_BP(H_BP),
        .V_ACTIVE(V_ACTIVE),.V_FP(V_FP),.V_SYNC(V_SYNC),.V_BP(V_BP)) dut (
        .clk_pixel(clk),.clk_tmds(clk),.rst_n(rst_n),
        .tri0_setup(1'b0),.tri0_a0(16'sd0),.tri0_b0(16'sd0),.tri0_c0(32'sd0),
        .tri0_a1(16'sd0),.tri0_b1(16'sd0),.tri0_c1(32'sd0),
        .tri0_a2(16'sd0),.tri0_b2(16'sd0),.tri0_c2(32'sd0),
        .tri0_r(4'd0),.tri0_g(4'd0),.tri0_b(4'd0),
        .tri0_z0(16'd0),.tri0_z1(16'd0),.tri0_z2(16'd0),
        .tri1_setup(1'b0),.tri1_a0(16'sd0),.tri1_b0(16'sd0),.tri1_c0(32'sd0),
        .tri1_a1(16'sd0),.tri1_b1(16'sd0),.tri1_c1(32'sd0),
        .tri1_a2(16'sd0),.tri1_b2(16'sd0),.tri1_c2(32'sd0),
        .tri1_r(4'd0),.tri1_g(4'd0),.tri1_b(4'd0),
        .tri1_z0(16'd0),.tri1_z1(16'd0),.tri1_z2(16'd0),
        .scene_rx_byte(rx_byte),.scene_rx_valid(rx_valid),
        .vga_r(vr),.vga_g(vg),.vga_b(vb),.vga_hsync(),.vga_vsync(),
        .tmds_clk_p(),.tmds_clk_n(),.tmds_d_p(),.tmds_d_n());

    always #1 clk=~clk;
    always @(posedge clk) if (rst_n) begin
        cycles=cycles+1;
        if (dut.ready0 !== dut.ready_attr0 || dut.ready1 !== dut.ready_attr1 ||
            dut.ready2 !== dut.ready_attr2 || dut.ready3 !== dut.ready_attr3) begin
            failures=failures+1;
            if (failures<8) $display("FAIL: depth/scalar setup result phase mismatch");
        end
        if (dut.prepared_generation_matches && ready_cycle==0) ready_cycle=cycles;
        if (dut.activate_scene) activation_cycle=cycles;
    end

    always @(negedge clk) if (rst_n) begin
        if (vr !== (dut.active_d ? dut.display_r : 4'h0) ||
            vg !== (dut.active_d ? dut.display_g : 4'h0) ||
            vb !== (dut.active_d ? dut.display_b : 4'h0)) begin
            failures=failures+1;
            if (failures<8) $display("FAIL: VGA RGB does not follow delayed active gate");
        end
        if (dut.vga_hsync !== dut.hsync_d || dut.vga_vsync !== dut.vsync_d) begin
            failures=failures+1;
            if (failures<8) $display("FAIL: VGA sync output does not follow delayed timing signals");
        end
    end

    function integer frame_phase;
        begin frame_phase=dut.u_timing.y*HTOTAL+dut.u_timing.x; end
    endfunction

    task send_byte(input [7:0] value);
        begin
            @(negedge clk); rx_byte=value; rx_valid=1;
            @(negedge clk); rx_byte=0; rx_valid=0;
        end
    endtask

    task emit_pixel(input integer sid, input integer px, input integer py);
        begin
            pixels=pixels+1;
            if (dut.active_scene !== (sid==0 ? SCENE_A : sid==1 ? SCENE_B : SCENE_C) &&
                !(sid==3 && dut.active_scene===SCENE_A)) begin
                failures=failures+1;
                if (failures<8) $display("FAIL: active scene mixed during sampled frame");
            end
            $display("PIX %0d %0d %0d %0d %0d %0d",sid,px,py,
                dut.fragment_scalar_valid,dut.raster_primitive_id,dut.fragment_scalar);
            $display("RGB %0d %0d %0d %0d %0d %0d",sid,px,py,
                dut.display_r,dut.display_g,dut.display_b);
            if (px>=35 && px<=45 && py>=87 && py<=99) begin
                $display("EDGE %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d",
                    sid,px,py,
                    dut.prepared_quad_raster.u_rast4.u0.u_e0.f,
                    dut.prepared_quad_raster.u_rast4.u0.u_e1.f,
                    dut.prepared_quad_raster.u_rast4.u0.u_e2.f,
                    dut.prepared_quad_raster.u_rast4.u1.u_e0.f,
                    dut.prepared_quad_raster.u_rast4.u1.u_e1.f,
                    dut.prepared_quad_raster.u_rast4.u1.u_e2.f,
                    dut.prepared_quad_raster.u_rast4.u2.u_e0.f,
                    dut.prepared_quad_raster.u_rast4.u2.u_e1.f,
                    dut.prepared_quad_raster.u_rast4.u2.u_e2.f,
                    dut.prepared_quad_raster.u_rast4.u3.u_e0.f,
                    dut.prepared_quad_raster.u_rast4.u3.u_e1.f,
                    dut.prepared_quad_raster.u_rast4.u3.u_e2.f,
                    dut.cov3,dut.cov2,dut.cov1,dut.cov0,
                    dut.cov3_armed,dut.cov2_armed,dut.cov1_armed,dut.cov0_armed,
                    dut.raster_primitive_valid,dut.raster_primitive_id,
                    dut.fragment_scalar_valid,dut.fragment_scalar,
                    dut.display_r,dut.display_g,dut.display_b,
                    vr,vg,vb,dut.active_d);
            end
        end
    endtask

    task scan_first_frame(input integer sid);
        integer target_phase;
        begin
            emit_pixel(sid,0,0);
            for (y=0;y<V_ACTIVE;y=y+1) begin
                for (x=0;x<H_ACTIVE;x=x+1) begin
                    if (!(x==0 && y==0)) begin
                        target_phase=y*HTOTAL+x;
                        while (frame_phase()!=target_phase) @(negedge clk);
                        @(posedge clk); #0.1;
                        emit_pixel(sid,x,y);
                    end
                end
            end
        end
    endtask

    task wait_for_next_frame;
        begin
            while (!dut.frame_start) @(negedge clk);
            @(posedge clk); #0.1;
        end
    endtask

    task transmit_and_scan(input [1199:0] scene, input integer sid);
        begin
            held_scene=dut.active_scene;
            held_active_A=active_scalar_A_bus;
            held_active_frac=active_scalar_frac_bus;
            final_byte_cycle=0; ready_cycle=0; activation_cycle=0; clear_cycle=0;
            send_byte(8'hA5);
            for (j=0;j<150;j=j+1) begin
                send_byte(scene[j*8 +: 8]);
                if (dut.active_scene !== held_scene || active_scalar_A_bus !== held_active_A ||
                    active_scalar_frac_bus !== held_active_frac) begin
                    failures=failures+1;
                    if (failures<8) $display("FAIL: candidate raw/derived scene leaked during receive");
                end
            end
            final_byte_cycle=cycles;
            while (!dut.activate_scene) begin
                @(negedge clk);
                if (dut.active_scene !== held_scene || active_scalar_A_bus !== held_active_A ||
                    active_scalar_frac_bus !== held_active_frac) begin
                    failures=failures+1;
                    if (failures<8) $display("FAIL: candidate scalar state leaked before activation");
                end
            end
            if (!dut.prepared_generation_matches || ready_cycle==0) begin
                failures=failures+1;
                $display("FAIL: activation did not wait for depth and scalar generation readiness");
            end
            @(posedge clk); #0.1;
            clear_cycle=cycles;
            if (dut.active_scene !== scene || dut.scene_commit_pending ||
                !dut.depth_armed0 || !dut.depth_armed1 || !dut.depth_armed2 || !dut.depth_armed3) begin
                failures=failures+1;
                $display("FAIL: T1h scene activation failed sid=%0d",sid);
            end
            if (active_scalar_A_bus !== {dut.u_t1h_scalar.candidate_A_attr3,
                    dut.u_t1h_scalar.candidate_A_attr2,dut.u_t1h_scalar.candidate_A_attr1,
                    dut.u_t1h_scalar.candidate_A_attr0} ||
                active_scalar_frac_bus !== {dut.u_t1h_scalar.candidate_frac_attr3,
                    dut.u_t1h_scalar.candidate_frac_attr2,dut.u_t1h_scalar.candidate_frac_attr1,
                    dut.u_t1h_scalar.candidate_frac_attr0}) begin
                failures=failures+1;
                $display("FAIL: scalar coefficient/fraction set did not commit atomically");
            end
            $display("MEASURE scene=%0d payload_to_ready=%0d ready_to_activation=%0d payload_to_clear=%0d",
                sid,ready_cycle-final_byte_cycle,activation_cycle-ready_cycle,clear_cycle-final_byte_cycle);
            scene_id=sid;
            scan_first_frame(sid);
        end
    endtask

    initial begin
        repeat(4) @(negedge clk); rst_n=1;
        repeat(3) @(negedge clk);
        transmit_and_scan(SCENE_A,0);
        wait_for_next_frame();
        scan_first_frame(0);
        transmit_and_scan(SCENE_B,1);
        transmit_and_scan(SCENE_C,2);
        transmit_and_scan(SCENE_A,3);
        if (!failures && pixels==5*H_ACTIVE*V_ACTIVE)
            $display("PASS: T1h full-frame scalar trace pixels=%0d",pixels);
        else
            $display("FAIL: T1h transition/setup failures=%0d pixels=%0d",failures,pixels);
        $finish;
    end
    initial begin #200000000; $display("FAIL: T1h simulation timeout"); $finish; end
endmodule
"""


def signed(value: int, width: int) -> int:
    return value - (1 << width) if value & (1 << (width - 1)) else value


def fixture(name: str) -> tuple[str, int]:
    wire = bytes.fromhex((ROOT / "fixtures" / name).read_text().strip())
    if len(wire) != 151 or wire[0] != 0xA5:
        raise AssertionError(f"{name}: expected 151 wire bytes beginning with A5")
    scene = int.from_bytes(wire[1:], "little")
    return f"{scene:0300x}", scene


def decode_scene(scene: int):
    planes = []
    records = []
    for lane in range(4):
        record = (scene >> (lane * 300)) & ((1 << 300) - 1)
        base = record & ((1 << 252) - 1)
        edges = []
        for edge in range(3):
            offset = edge * 64
            edges.append((signed((base >> offset) & 0xFFFF,16),
                          signed((base >> (offset+16)) & 0xFFFF,16),
                          signed((base >> (offset+32)) & 0xFFFFFFFF,32)))
        values = [(record >> (252 + vertex*16)) & 0xFFFF for vertex in range(3)]
        depths = [(base >> (204 + vertex*16)) & 0xFFFF for vertex in range(3)]
        denominator = sum(edge[2] for edge in edges)
        sign = 1 if denominator > 0 else -1
        recip, frac = full_reciprocal(abs(denominator))
        def setup(samples):
            terms = [sum(edges[i][axis]*samples[i] for i in range(3))
                     for axis in range(3)]
            return tuple(term*sign*recip for term in terms)+(frac,)
        planes.append((setup(values),setup(depths)))
        records.append((edges, values))
    return planes, records


def oracle_pixel(planes, records, x: int, y: int):
    winner = None
    winner_depth = None
    for lane, ((attr_plane, depth_plane), (edges, _)) in enumerate(zip(planes, records)):
        if not all(a*x+b*y+c >= 0 for a,b,c in edges):
            continue
        da,db,dc,df=depth_plane
        depth=(da*x+db*y+dc) >> df
        if winner is None or depth < winner_depth:
            winner, winner_depth = lane, depth
    if winner is None:
        return 0, 0, 0
    a,b,c,frac=planes[winner][0]
    return 1, winner, (a*x+b*y+c) >> frac


def depth_candidates(planes, x: int, y: int):
    return [((a*x+b*y+c) >> frac) for _,(a,b,c,frac) in planes]


def main() -> int:
    fixture_names = (
        "gpu_t1h_scene_a_wire_151b.hex",
        "gpu_t1h_scene_b_wire_151b.hex",
        "gpu_t1h_scene_c_wire_151b.hex",
    )
    fixture_data = [fixture(name) for name in fixture_names]
    values = {
        "SCENE_A": fixture_data[0][0],
        "SCENE_B": fixture_data[1][0],
        "SCENE_C": fixture_data[2][0],
    }
    tb_text=TB
    for key,value in values.items():
        tb_text=tb_text.replace(f"@@{key}@@",value)
    with tempfile.TemporaryDirectory(prefix="spu_t1h_attribute_") as temp_dir:
        temp=Path(temp_dir)
        tb=temp/"t1h_attribute_tb.v"
        out=temp/"t1h_attribute_tb.vvp"
        tb.write_text(tb_text)
        compile_result=subprocess.run(
            ["iverilog","-g2012","-s","t1h_attribute_tb","-o",str(out),str(tb),
             *[str(ROOT/source) for source in RTL_FILES]],
            cwd=ROOT,text=True,capture_output=True,check=False)
        if compile_result.returncode:
            print(compile_result.stderr)
            return 1
        invalid_tb=temp/"t1h_invalid_profile_tb.v"
        invalid_out=temp/"t1h_invalid_profile_tb.vvp"
        invalid_tb.write_text(r'''module t1h_invalid_profile_tb;
        spu_gpu_top #(.DEVICE("A7"),.ENABLE_HDMI(0),.PREPARED_SCENE(1),
            .FOUR_PRIMITIVE_SCENE(0),.T1H_SCALAR_SCENE(1)) dut();
    endmodule
''')
        invalid_compile=subprocess.run(
            ["iverilog","-g2012","-s","t1h_invalid_profile_tb","-o",str(invalid_out),
             str(invalid_tb),*[str(ROOT/source) for source in RTL_FILES]],
            cwd=ROOT,text=True,capture_output=True,check=False)
        if invalid_compile.returncode==0 or "T1H_requires_prepared_four_primitive_scene" not in invalid_compile.stderr:
            print("FAIL: illegal T1h selector combination did not fail elaboration")
            print(invalid_compile.stderr)
            return 1
        diag_guard_tb=temp/"t1h_invalid_diag_tb.v"
        diag_guard_out=temp/"t1h_invalid_diag_tb.vvp"
        diag_guard_tb.write_text(r'''module t1h_invalid_diag_tb;
        spu_gpu_top #(.DEVICE("A7"),.ENABLE_HDMI(0),.PREPARED_SCENE(0),
            .FOUR_PRIMITIVE_SCENE(0),.T1H_SCALAR_SCENE(0),.T1H_SCALAR_DIAG(1)) dut();
    endmodule
''')
        diag_guard_compile=subprocess.run(
            ["iverilog","-g2012","-s","t1h_invalid_diag_tb","-o",str(diag_guard_out),
             str(diag_guard_tb),*[str(ROOT/source) for source in RTL_FILES]],
            cwd=ROOT,text=True,capture_output=True,check=False)
        if diag_guard_compile.returncode==0 or "T1H_scalar_diag_requires_scalar_scene" not in diag_guard_compile.stderr:
            print("FAIL: scalar diagnostic without T1h profile did not fail elaboration")
            print(diag_guard_compile.stderr)
            return 1
        result=subprocess.run(["vvp",str(out)],cwd=ROOT,text=True,capture_output=True,
                              check=False,timeout=60)
    if result.returncode:
        print(result.stderr)
        return 1
    for line in result.stdout.splitlines():
        if line.startswith("MEASURE "):
            print(line)
    mismatches=0
    checked=[0,0,0,0]
    scalar_pixels={}
    planes_records=[decode_scene(scene) for _,scene in fixture_data]
    scene_a_planes,scene_a_records=planes_records[0]
    if any(edges!=scene_a_records[0][0] for edges,_ in scene_a_records[1:]):
        mismatches+=1
        print("FAIL: Scene A primitives are no longer fully coextensive")
    min_depth_ties=0
    for ty in range(100):
        for tx in range(80):
            covered=[lane for lane,(edges,_) in enumerate(scene_a_records)
                     if all(a*tx+b*ty+c>=0 for a,b,c in edges)]
            if covered:
                depths=depth_candidates(scene_a_planes,tx,ty)
                nearest=min(depths[lane] for lane in covered)
                if sum(depths[lane]==nearest for lane in covered)>1:
                    min_depth_ties+=1
    seam_expectations={
        (39,41):([59,61,57,59],[2],2),
        (40,41):([60,60,58,58],[2,3],2),
        (41,41):([61,59,59,57],[3],3),
        (40,40):([59,59,59,59],[0,1,2,3],0),
    }
    for (sx,sy),(expected_depths,expected_ties,expected_winner) in seam_expectations.items():
        observed_depths=depth_candidates(scene_a_planes,sx,sy)
        valid,winner,_=oracle_pixel(scene_a_planes,scene_a_records,sx,sy)
        covered=[lane for lane,(edges,_) in enumerate(scene_a_records)
                 if all(a*sx+b*sy+c>=0 for a,b,c in edges)]
        nearest=min(observed_depths[lane] for lane in covered) if covered else None
        observed_ties=[lane for lane in covered if observed_depths[lane]==nearest]
        if (observed_depths,observed_ties,winner if valid else None)!=(
                expected_depths,expected_ties,expected_winner):
            mismatches+=1
            print(f"DEPTH SEAM MISMATCH xy=({sx},{sy}) expected={(expected_depths,expected_ties,expected_winner)} got={(observed_depths,observed_ties,winner if valid else None)}")
    if min_depth_ties!=117:
        mismatches+=1
        print(f"DEPTH SEAM MISMATCH minimum-depth tie pixels expected=117 got={min_depth_ties}")
    print("DEPTH SEAM A: (39,41)->lane 2; (40,41)->depth tie lanes 2/3, lane 2 wins; (41,41)->lane 3; y=40 has a four-way tie; minimum-depth tie pixels=117")
    for line in result.stdout.splitlines():
        if not line.startswith("PIX "):
            continue
        _,sid_s,x_s,y_s,valid_s,lane_s,value_s=line.split()
        sid,x,y,valid,lane,value=map(int,(sid_s,x_s,y_s,valid_s,lane_s,value_s))
        oracle=oracle_pixel(*planes_records[sid if sid<3 else 0],x,y)
        checked[sid]+=1
        if oracle[0] and not 0 <= oracle[2] <= 0xFFFF:
            mismatches+=1
            if mismatches<=12:
                print(f"ORACLE RANGE ERROR scene={sid} xy=({x},{y}) value={oracle[2]}")
        if (valid,lane,value) != oracle:
            mismatches+=1
            if mismatches<=12:
                print(f"MISMATCH scene={sid} xy=({x},{y}) expected={oracle} got={(valid,lane,value)}")
        scalar_pixels[(sid,x,y)]=(oracle[0],oracle[2])
    rgb_checked=0
    edge_checked=0
    for line in result.stdout.splitlines():
        if not line.startswith("RGB "):
            continue
        _,sid_s,x_s,y_s,r_s,g_s,b_s=line.split()
        sid,x,y,r,g,b=map(int,(sid_s,x_s,y_s,r_s,g_s,b_s))
        valid,value=scalar_pixels[(sid,x,y)]
        expected_gray=((value >> 11) & 0xF) if valid else 0
        rgb_checked+=1
        if (r,g,b)!=(expected_gray,expected_gray,expected_gray):
            mismatches+=1
            if mismatches<=12:
                print(f"RGB DIAGNOSTIC MISMATCH scene={sid} xy=({x},{y}) expected={expected_gray} got={(r,g,b)}")
    for line in result.stdout.splitlines():
        if not line.startswith("EDGE "):
            continue
        fields=list(map(int,line.split()[1:]))
        sid,x,y=fields[:3]
        observed_edges=fields[3:15]
        cov_bits=fields[15:19]
        cov_armed_bits=fields[19:23]
        cov_mask=sum(bit<<lane for lane,bit in enumerate(reversed(cov_bits)))
        cov_armed_mask=sum(bit<<lane for lane,bit in enumerate(reversed(cov_armed_bits)))
        winner_valid,winner_lane,attr_valid,attr_value=fields[23:27]
        display_rgb=tuple(fields[27:30])
        vga_rgb=tuple(fields[30:33])
        active=fields[33]
        planes,records=planes_records[sid if sid<3 else 0]
        lane_edges=records
        expected_edges=[a*x+b*y+c for edges,_ in lane_edges for a,b,c in edges]
        expected_cov=sum((1<<lane) for lane in range(4)
                         if all(value>=0 for value in expected_edges[lane*3:lane*3+3]))
        oracle=oracle_pixel(planes,records,x,y)
        expected_gray=((oracle[2]>>11)&0xF) if oracle[0] else 0
        expected_edges_flat=[value for lane in range(4)
                             for value in expected_edges[lane*3:lane*3+3]]
        expected_lane=oracle[1] if oracle[0] else 0
        expected_attr_valid=oracle[0]
        expected_attr_value=oracle[2]
        edge_checked+=1
        if observed_edges!=expected_edges_flat:
            mismatches+=1
            if mismatches<=12:
                print(f"EDGE FUNCTION MISMATCH scene={sid} xy=({x},{y}) expected={expected_edges_flat} got={observed_edges}")
        if cov_mask!=expected_cov or cov_armed_mask!=expected_cov:
            mismatches+=1
            if mismatches<=12:
                print(f"COVERAGE MISMATCH scene={sid} xy=({x},{y}) expected_mask=0x{expected_cov:x} got_cov=0x{cov_mask:x} got_armed=0x{cov_armed_mask:x}")
        if (winner_valid,winner_lane,attr_valid,attr_value)!=(oracle[0],expected_lane,
                expected_attr_valid,expected_attr_value):
            mismatches+=1
            if mismatches<=12:
                print(f"WINNER MISMATCH scene={sid} xy=({x},{y}) expected={(oracle[0],expected_lane,expected_attr_valid,expected_attr_value)} got={(winner_valid,winner_lane,attr_valid,attr_value)}")
        expected_rgb=(expected_gray,)*3
        expected_vga=expected_rgb if active else (0,0,0)
        if display_rgb!=expected_rgb or vga_rgb!=expected_vga:
            mismatches+=1
            if mismatches<=12:
                print(f"EDGE RGB MISMATCH scene={sid} xy=({x},{y}) active={active} expected_display={expected_rgb} expected_vga={expected_vga} got_display={display_rgb} got_vga={vga_rgb}")
    if rgb_checked!=40000:
        mismatches+=1
        print(f"FAIL: scalar diagnostic sample count expected=40000 got={rgb_checked}")
    if edge_checked!=5*11*13:
        mismatches+=1
        print(f"FAIL: focused edge audit count expected=715 got={edge_checked}")
    for sid,count in enumerate(checked):
        expected_count=16000 if sid==0 else 8000
        if count != expected_count:
            mismatches+=1
            print(f"FAIL: scene sample count sid={sid} expected={expected_count} got={count}")
    if "PASS: T1h full-frame scalar trace pixels=40000" not in result.stdout:
        mismatches+=1
        print(result.stdout[-3000:])
    if mismatches:
        print(f"FAIL: T1h scalar interpolation mismatches={mismatches}")
        return 1
    print("PASS: T1h scalar interpolation, depth seam, edge coverage, winner/RGB gating, and A/A/B/C/A activation (40,000 pixels; 715 focused edge samples)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
