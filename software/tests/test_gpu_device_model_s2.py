#!/usr/bin/env python3
"""T1d packet, finite-width model, loader, and scoped RTL parity checks."""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from software.spu_gpu_eval.device_arithmetic import prepare_depth
from software.spu_gpu_eval.device_loader import PreparedSceneControl, RawSceneLoader
from software.spu_gpu_eval.device_model import pixel_decision, prepare_scene
from software.spu_gpu_eval.device_packet import DeviceTriangle, decode_packet
from software.spu_gpu_eval.device_preview import (
    HEADER, MODULES, PROFILE, build_artifacts, write_device_preview,
)
from software.spu_gpu_eval.packet import compile_packet
from software.spu_gpu_eval.scene import parse_scene_bytes


FIXTURE = ROOT / "fixtures/gpu_t1d_scene_wire_64b.bin"
SCENE_JSON = ROOT / "examples/gpu/t1d_two_triangle.json"
def _scene_variant(raw: bytes, edit) -> tuple[bytes, object]:
    data = json.loads(raw)
    edit(data)
    encoded = (json.dumps(data, sort_keys=True) + "\n").encode()
    return encoded, parse_scene_bytes(encoded)


def _rtl_depth_vectors(vectors: list[tuple[str, DeviceTriangle]]) -> None:
    declarations = "\n".join(
        f"reg signed [15:0] {name};" for name in ("a0", "b0", "a1", "b1", "a2", "b2")
    ) + "\n" + "\n".join(f"reg signed [31:0] c{i};" for i in range(3)) + "\n" + "\n".join(
        f"reg [15:0] z{i};" for i in range(3)
    )
    ports = ",\n".join(f".{field}({field})" for field in ("a0", "b0", "a1", "b1", "a2", "b2", "c0", "c1", "c2", "z0", "z1", "z2"))
    input_names = ("a0", "b0", "c0", "a1", "b1", "c1", "a2", "b2", "c2", "z0", "z1", "z2")
    assignments = []
    for index, (_label, tri) in enumerate(vectors):
        values = [component for edge in tri.edges for component in edge] + list(tri.z)
        statements = [f"{name} = {width}'h{(value & ((1 << width) - 1)):0{width // 4}x};"
                      for name, value, width in zip(input_names, values,
                          (16, 16, 32, 16, 16, 32, 16, 16, 32, 16, 16, 16))]
        assignments.append("\n".join(statements) + f"\nrun_case({index});")
    tb = f"""`timescale 1ns/1ps
module s2_depth_tb;
reg clk=0, rst_n=0, start=0;
{declarations}
wire signed [55:0] A_z, B_z, C_z;
wire [6:0] frac_bits;
wire done;
always #5 clk=~clk;
spu_depth_math dut(.clk(clk), .rst_n(rst_n), .start(start), {ports},
    .A_z(A_z), .B_z(B_z), .C_z(C_z), .frac_bits(frac_bits), .done(done));
task run_case(input integer tag);
begin
    @(negedge clk); start=1;
    @(negedge clk); start=0;
    wait(done === 1'b1); #1;
    $display("DEPTH %0d %0d %0d %0d %0d", tag, $signed(A_z), $signed(B_z), $signed(C_z), frac_bits);
    @(negedge clk);
end
endtask
initial begin
    repeat(3) @(negedge clk); rst_n=1;
    {' '.join(assignments)}
    $finish;
end
endmodule
"""
    with tempfile.TemporaryDirectory(prefix="spu_gpu_s2_depth_") as directory:
        temp = Path(directory)
        source, image = temp / "depth_tb.v", temp / "depth_tb.vvp"
        source.write_text(tb)
        command = ["iverilog", "-g2012", "-s", "s2_depth_tb", "-o", str(image), str(source),
                   str(ROOT / "hardware/rtl/gpu/spu_depth_math.v"),
                   str(ROOT / "hardware/rtl/gpu/spu_reciprocal_core.v"),
                   str(ROOT / "hardware/rtl/gpu/spu_shared_mult35.v")]
        compiled = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=15)
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        run = subprocess.run(["vvp", str(image)], cwd=ROOT, text=True, capture_output=True, timeout=15)
        assert run.returncode == 0, run.stdout + run.stderr
    actual = {}
    for line in run.stdout.splitlines():
        if line.startswith("DEPTH "):
            _, tag, a, b, c, frac = line.split()
            actual[int(tag)] = (int(a), int(b), int(c), int(frac))
    assert len(actual) == len(vectors), run.stdout
    for index, (_label, triangle) in enumerate(vectors):
        prepared = prepare_depth(triangle)
        expected = (prepared.a_z, prepared.b_z, prepared.c_z, prepared.frac_bits)
        assert actual[index] == expected, (_label, expected, actual[index])
    print(f"PASS: depth setup matched Icarus RTL for {len(vectors)} vectors")


def _rtl_packet_datapath(packet: bytes, expected: dict[tuple[int, int], tuple[int, int, int]]) -> None:
    scene = decode_packet(packet)
    lines = []
    depth_inst = []
    for ti, triangle in enumerate(scene.triangles):
        for ei, edge in enumerate(triangle.edges):
            a, b, c = edge
            packed = (((a & 0xFFFF) << 48) | ((b & 0xFFFF) << 32) | (c & 0xFFFFFFFF))
            lines.append(f"wire [63:0] edge_coef_{ti}_{ei}=64'h{packed:016x};")
            lines.append(f"wire edge_inside_{ti}_{ei};")
            lines.append(f"spu_edge_stepper e_{ti}_{ei}(.clk(clk),.rst_n(rst_n),.setup(edge_setup),"
                         f".coef_pack(edge_coef_{ti}_{ei}),.step_x(step_x),.step_y(step_y),"
                         f".inside_out(edge_inside_{ti}_{ei}));")
        for edge_no, edge in enumerate(triangle.edges):
            for field, value, width in zip(("a", "b", "c"), edge, (16, 16, 32)):
                lines.append(f"wire signed [{width-1}:0] t{ti}_{field}{edge_no}={width}'h{value & ((1 << width)-1):0{width//4}x};")
        for zi, value in enumerate(triangle.z):
            lines.append(f"wire [15:0] t{ti}_z{zi}=16'h{value:04x};")
        pin_values = []
        for edge_no in range(3):
            pin_values.extend((f".a{edge_no}(t{ti}_a{edge_no})", f".b{edge_no}(t{ti}_b{edge_no})"))
        pin_values.extend(f".c{i}(t{ti}_c{i})" for i in range(3))
        pin_values.extend(f".z{i}(t{ti}_z{i})" for i in range(3))
        lines.extend((f"wire signed [55:0] A_z{ti},B_z{ti},C_z{ti};",
                      f"wire [6:0] frac{ti}; wire done{ti};",
                      f"spu_depth_math d{ti}(.clk(clk),.rst_n(rst_n),.start(start),{','.join(pin_values)},"
                      f".A_z(A_z{ti}),.B_z(B_z{ti}),.C_z(C_z{ti}),.frac_bits(frac{ti}),.done(done{ti}));",
                      f"wire signed [55:0] depth{ti};",
                      f"spu_attr_stepper a{ti}(.clk(clk),.rst_n(rst_n),.setup(attr_setup),.a_coef(A_z{ti}),"
                      f".b_coef(B_z{ti}),.c_coef(C_z{ti}),.step_x(step_x),.step_y(step_y),"
                      f".frac_bits(frac{ti}),.value_out(depth{ti}));"))
    edge_wires = []
    for ti in range(2):
        edge_wires.append("(" + " && ".join(f"edge_inside_{ti}_{ei}" for ei in range(3)) + ")")
    colors = ["".join(f"4'h{c:x}" for c in tri.rgb) for tri in scene.triangles]
    point_calls = []
    for (x, y), rgb in expected.items():
        value = "".join(f"{c:x}" for c in rgb)
        point_calls.append(f"check_point({x},{y},12'h{value});")
    tb = f"""`timescale 1ns/1ps
module s2_changed_datapath_tb;
reg clk=0,rst_n=0,start=0,edge_setup=0,attr_setup=0,step_x=0,step_y=0;
always #5 clk=~clk;
{chr(10).join(lines)}
wire cov0={edge_wires[0]}, cov1={edge_wires[1]};
wire [3:0] pixel_r,pixel_g,pixel_b;
spu_depth_compare cmp(.cov0(cov0),.cov1(cov1),.depth0(depth0),.depth1(depth1),
 .r0({colors[0][0:4]}),.g0({colors[0][4:8]}),.b0({colors[0][8:12]}),
 .r1({colors[1][0:4]}),.g1({colors[1][4:8]}),.b1({colors[1][8:12]}),
 .pixel_r(pixel_r),.pixel_g(pixel_g),.pixel_b(pixel_b));
integer failures=0;
task check_point(input integer px,input integer py,input [11:0] expected); integer k; begin
 @(negedge clk); edge_setup=1; attr_setup=1; @(negedge clk); edge_setup=0; attr_setup=0;
 for(k=0;k<py;k=k+1) begin step_y=1; @(negedge clk); step_y=0; @(negedge clk); end
 for(k=0;k<px;k=k+1) begin step_x=1; @(negedge clk); step_x=0; @(negedge clk); end
 #1;
 if({{pixel_r,pixel_g,pixel_b}} !== expected) begin
   failures=failures+1; $display("FAIL pixel %0d,%0d expected %h got %h cov=%b%b edges=%b%b%b%b%b%b depth=%0d,%0d",
       px,py,expected,{{pixel_r,pixel_g,pixel_b}},cov0,cov1,
       edge_inside_0_0,edge_inside_0_1,edge_inside_0_2,edge_inside_1_0,edge_inside_1_1,edge_inside_1_2,depth0,depth1);
 end else $display("PIXEL %0d %0d %h",px,py,{{pixel_r,pixel_g,pixel_b}});
end endtask
initial begin
 repeat(4) @(negedge clk); rst_n=1;
 @(negedge clk); start=1; @(negedge clk); start=0;
 wait(done0 && done1);
 {' '.join(point_calls)}
 if(failures==0) $display("PASS changed T1d datapath RTL");
 else $display("FAIL changed T1d datapath failures=%0d",failures);
 $finish;
end
endmodule
"""
    with tempfile.TemporaryDirectory(prefix="spu_gpu_s2_datapath_") as directory:
        temp = Path(directory)
        source, image = temp / "datapath_tb.v", temp / "datapath_tb.vvp"
        source.write_text(tb)
        sources = ("spu_edge_stepper.v", "spu_depth_math.v", "spu_reciprocal_core.v",
                   "spu_shared_mult35.v", "spu_attr_stepper.v", "spu_depth_compare.v")
        command = ["iverilog", "-g2012", "-s", "s2_changed_datapath_tb", "-o", str(image), str(source),
                   *[str(ROOT / "hardware/rtl/gpu" / name) for name in sources]]
        compiled = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=15)
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        run = subprocess.run(["vvp", str(image)], cwd=ROOT, text=True, capture_output=True, timeout=15)
        assert run.returncode == 0, run.stdout + run.stderr
    assert "PASS changed T1d datapath RTL" in run.stdout, run.stdout + run.stderr
    assert "FAIL" not in run.stdout, run.stdout
    print("PASS: packet selected pixels matched T1d depth, raster, attribute, and compare RTL")


def _rtl_loader_control() -> None:
    payload = bytearray(range(63))
    payload[17] = 0xA5
    payload_hex = f"{int.from_bytes(payload, 'little'):0126x}"
    tb = f"""`timescale 1ns/1ps
module s2_loader_control_tb;
localparam [503:0] PAYLOAD=504'h{payload_hex};
reg clk=0,rst_n=0,rx_valid=0,activate=0; reg [7:0] rx_byte=0;
wire [503:0] active_scene,candidate_scene; wire commit_pending;
always #5 clk=~clk;
spu_scene_loader #(.SCENE_BITS(504),.PAYLOAD_BYTES(63)) loader(
 .clk(clk),.rst_n(rst_n),.rx_byte(rx_byte),.rx_valid(rx_valid),
 .activate_raw_bank(activate),.active_scene(active_scene),
 .candidate_scene(candidate_scene),.commit_pending(commit_pending));
reg control_commit=0,frame_start=0,ready0=0,ready1=0;
wire prepare0,prepare1,control_activate,ready0_seen,ready1_seen,generation_matches;
wire signed [55:0] active_A_z0,active_B_z0,active_C_z0,active_A_z1,active_B_z1,active_C_z1;
wire [6:0] active_frac_bits0,active_frac_bits1;
spu_prepared_scene_control control(
 .clk(clk),.rst_n(rst_n),.commit_pending(control_commit),.frame_start(frame_start),
 .ready0(ready0),.ready1(ready1),.candidate_A_z0(56'sd11),.candidate_B_z0(-56'sd2),
 .candidate_C_z0(56'sd33),.candidate_frac_bits0(7'd4),.candidate_A_z1(56'sd44),
 .candidate_B_z1(56'sd5),.candidate_C_z1(56'sd66),.candidate_frac_bits1(7'd6),
 .prepare0(prepare0),.prepare1(prepare1),.activate_scene(control_activate),
 .ready0_seen(ready0_seen),.ready1_seen(ready1_seen),.generation_matches(generation_matches),
 .active_A_z0(active_A_z0),.active_B_z0(active_B_z0),.active_C_z0(active_C_z0),
 .active_frac_bits0(active_frac_bits0),.active_A_z1(active_A_z1),.active_B_z1(active_B_z1),
 .active_C_z1(active_C_z1),.active_frac_bits1(active_frac_bits1));
integer i,failures=0;
task send_byte(input [7:0] value); begin
 @(negedge clk); rx_byte=value; rx_valid=1; @(negedge clk); rx_valid=0; rx_byte=0;
end endtask
initial begin
 repeat(3) @(negedge clk); rst_n=1;
 send_byte(8'hA4);
 if(loader.receiving !== 1'b0) begin failures=failures+1; $display("FAIL invalid start"); end
 send_byte(8'hA5);
 for(i=0;i<63;i=i+1) send_byte(PAYLOAD[i*8 +: 8]);
 if(!commit_pending || candidate_scene !== PAYLOAD || active_scene !== 504'd0) begin
   failures=failures+1; $display("FAIL complete raw packet state");
 end
 send_byte(8'hA5);
 if(!commit_pending || candidate_scene !== PAYLOAD) begin failures=failures+1; $display("FAIL pending-byte ignore"); end
 @(negedge clk); activate=1; rx_valid=1; rx_byte=8'hEE;
 @(negedge clk); activate=0; rx_valid=0; rx_byte=0;
 if(commit_pending || active_scene !== PAYLOAD) begin failures=failures+1; $display("FAIL raw bank activation edge"); end
 send_byte(8'hA5);
 for(i=0;i<10;i=i+1) send_byte(PAYLOAD[i*8 +: 8]);
 if(!loader.receiving || loader.payload_count !== 8'd10 || commit_pending) begin
   failures=failures+1; $display("FAIL incomplete packet state");
 end

 control_commit=1; @(posedge clk); #1;
 if(!prepare0 || !prepare1) begin failures=failures+1; $display("FAIL prepare pulse"); end
 @(negedge clk); frame_start=1; ready0=1; ready1=0;
 @(posedge clk); #1;
 if(control_activate || !ready0_seen || generation_matches) begin failures=failures+1; $display("FAIL one-ready gate"); end
 @(negedge clk); frame_start=0; ready0=0; ready1=1;
 @(posedge clk); #1;
 if(!generation_matches || control_activate) begin failures=failures+1; $display("FAIL ready generation match without frame"); end
 @(negedge clk); ready1=0; frame_start=1;
 @(posedge clk); #1;
 if(active_A_z0 !== 56'sd11 || active_B_z0 !== -56'sd2 || active_frac_bits1 !== 7'd6) begin
   failures=failures+1; $display("FAIL qualified activation data");
 end
 @(negedge clk); frame_start=0; control_commit=0;
 if(failures==0) $display("PASS loader and prepared-control RTL events");
 else $display("FAIL loader/control failures=%0d",failures);
 $finish;
end
endmodule
"""
    with tempfile.TemporaryDirectory(prefix="spu_gpu_s2_loader_") as directory:
        temp = Path(directory)
        source, image = temp / "loader_tb.v", temp / "loader_tb.vvp"
        source.write_text(tb)
        command = ["iverilog", "-g2012", "-s", "s2_loader_control_tb", "-o", str(image), str(source),
                   str(ROOT / "hardware/rtl/gpu/spu_scene_loader.v"),
                   str(ROOT / "hardware/rtl/gpu/spu_prepared_scene_control.v")]
        compiled = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=15)
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        run = subprocess.run(["vvp", str(image)], cwd=ROOT, text=True, capture_output=True, timeout=15)
        assert run.returncode == 0, run.stdout + run.stderr
    assert "PASS loader and prepared-control RTL events" in run.stdout, run.stdout + run.stderr
    assert "FAIL" not in run.stdout, run.stdout
    print("PASS: raw loader and prepared-control models matched RTL event behavior")


def _rtl_stepper_boundaries() -> None:
    tb = """`timescale 1ns/1ps
module s2_stepper_tb;
reg clk=0,rst_n=0,edge_setup=0,attr_setup=0,step_x=0,step_y=0;
reg signed [55:0] attr_a=0,attr_b=0,attr_c=0; reg [6:0] frac=0;
wire edge_inside; wire signed [55:0] attr_value;
always #5 clk=~clk;
spu_edge_stepper edge_unit(.clk(clk),.rst_n(rst_n),.setup(edge_setup),
 .coef_pack({16'h0001,16'h0000,32'h7fffffff}),.step_x(step_x),.step_y(step_y),.inside_out(edge_inside));
spu_attr_stepper attr_unit(.clk(clk),.rst_n(rst_n),.setup(attr_setup),
 .a_coef(attr_a),.b_coef(attr_b),.c_coef(attr_c),.step_x(step_x),.step_y(step_y),
 .frac_bits(frac),.value_out(attr_value));
integer failures=0;
initial begin
 repeat(3) @(negedge clk); rst_n=1;
 @(negedge clk); edge_setup=1; attr_setup=1; attr_a=-56'sd3; attr_b=-56'sd5; attr_c=-56'sd7; frac=1;
 @(negedge clk); edge_setup=0; attr_setup=0;
 if(!edge_inside || attr_value !== -56'sd4) begin failures=failures+1; $display("FAIL negative setup readout"); end
 step_x=1; @(negedge clk); step_x=0;
 if(attr_value !== -56'sd5) begin failures=failures+1; $display("FAIL negative arithmetic shift"); end
 step_y=1; @(negedge clk); step_y=0;
 if(attr_value !== -56'sd6) begin failures=failures+1; $display("FAIL row reanchor"); end
 @(negedge clk); edge_setup=1; attr_setup=1; attr_a=56'sd1; attr_b=0; attr_c=56'h7fffffffffffff; frac=0;
 @(negedge clk); edge_setup=0; attr_setup=0; step_x=1; @(negedge clk); step_x=0;
 if(edge_inside || attr_value !== -56'sh80000000000000) begin
   failures=failures+1; $display("FAIL signed accumulator wrap");
 end
 if(failures==0) $display("PASS edge and attribute width boundaries");
 else $display("FAIL stepper boundary failures=%0d",failures);
 $finish;
end
endmodule
"""
    with tempfile.TemporaryDirectory(prefix="spu_gpu_s2_stepper_") as directory:
        temp = Path(directory)
        source, image = temp / "stepper_tb.v", temp / "stepper_tb.vvp"
        source.write_text(tb)
        command = ["iverilog", "-g2012", "-s", "s2_stepper_tb", "-o", str(image), str(source),
                   str(ROOT / "hardware/rtl/gpu/spu_edge_stepper.v"),
                   str(ROOT / "hardware/rtl/gpu/spu_attr_stepper.v")]
        compiled = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=15)
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        run = subprocess.run(["vvp", str(image)], cwd=ROOT, text=True, capture_output=True, timeout=15)
        assert run.returncode == 0, run.stdout + run.stderr
    assert "PASS edge and attribute width boundaries" in run.stdout, run.stdout + run.stderr
    assert "FAIL" not in run.stdout, run.stdout
    print("PASS: edge/depth signed wrap and arithmetic shift matched RTL")


def main() -> int:
    wire = FIXTURE.read_bytes()
    baseline_raw = SCENE_JSON.read_bytes()
    baseline = parse_scene_bytes(baseline_raw)
    assert compile_packet(baseline) == wire
    decoded = decode_packet(wire)
    assert decoded.triangles[0].rgb == (15, 0, 0)
    assert decoded.triangles[0].z == (700, 3600, 400)
    assert decoded.triangles[1].rgb == (0, 15, 0)
    assert decoded.triangles[1].z == (700, 400, 3600)
    for malformed in (wire[:-1], wire + b"\x00", b"\x00" + wire[1:]):
        try:
            decode_packet(malformed)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed packet accepted")

    changed_raw, changed = _scene_variant(
        baseline_raw, lambda data: data["triangles"][0]["vertices"].__setitem__(2, [120, 240, 700]))
    approx_data = json.loads(baseline_raw)
    approx_data["triangles"][0]["vertices"] = [[0, 0, 3600], [639, 1, 400], [1, 478, 700]]
    approx_raw = (json.dumps(approx_data, sort_keys=True) + "\n").encode()
    approx_scene = parse_scene_bytes(approx_raw)
    approx_packet = compile_packet(approx_scene)
    approx_tri = decode_packet(approx_packet).triangles[0]
    approx_depth = prepare_depth(approx_tri)
    assert abs(approx_depth.denominator) == 305441
    assert approx_depth.normalization_shift == 3 and (abs(approx_depth.denominator) & 7) == 1

    zero = DeviceTriangle(((0, 0, 0),) * 3, (0, 0, 0), (0, 65535, 32768))
    extreme = DeviceTriangle(
        ((-32768, 32767, -(1 << 31)), (32767, -32768, (1 << 31) - 1),
         (-1, -1, (1 << 31) - 1)), (15, 15, 15), (65535, 1, 32768))
    vectors = [(f"baseline_{i}", tri) for i, tri in enumerate(decoded.triangles)]
    vectors.extend((f"changed_{i}", tri) for i, tri in enumerate(decode_packet(compile_packet(changed)).triangles))
    vectors.extend((f"approx_{i}", tri) for i, tri in enumerate(decode_packet(approx_packet).triangles[:1]))
    vectors.extend((("zero_denominator", zero), ("signed_extrema", extreme)))
    _rtl_depth_vectors(vectors)
    _rtl_loader_control()
    _rtl_stepper_boundaries()

    model = prepare_scene(wire)
    fixture = json.loads((ROOT / "fixtures/gpu_t1d_scene_reference.json").read_text())
    for point in fixture["diagnostic_pixels"]:
        result = pixel_decision(model, point["x"], point["y"])
        assert result["rgb"] == point["rgb"], (point, result)
    tie = pixel_decision(model, 320, 0)
    assert tie["covered_by"] == [0, 1] and tie["winner"] == 0
    baseline_points = {
        (point["x"], point["y"]): tuple(point["rgb"])
        for point in fixture["diagnostic_pixels"]
    }
    baseline_points[(320, 0)] = tuple(pixel_decision(model, 320, 0)["rgb"])
    _rtl_packet_datapath(wire, baseline_points)

    loader = RawSceneLoader()
    payload = bytearray(range(63))
    payload[17] = 0xA5
    assert loader.tick(True, 0xA5).start_accepted
    for byte in payload[:-1]:
        event = loader.tick(True, byte)
        assert event.payload_accepted and not event.packet_complete
    loader.tick()
    assert loader.receiving and loader.payload_count == 62 and not loader.commit_pending
    complete = loader.tick(True, payload[-1])
    assert complete.packet_complete and loader.commit_pending and not loader.receiving
    loader.tick(True, 0xA5)
    activated = loader.tick(True, 0xEE, activate_raw_bank=True)
    assert activated.bank_activated and loader.active_packet == b"\xA5" + bytes(payload)
    assert not loader.commit_pending and not loader.receiving
    incomplete = RawSceneLoader()
    incomplete.tick(True, 0xA5)
    for byte in payload[:11]:
        incomplete.tick(True, byte)
    assert incomplete.receiving and not incomplete.commit_pending

    control = PreparedSceneControl[int]()
    event = control.tick(True, False, candidate0=11, candidate1=22)
    assert event.prepare0 and event.prepare1 and control.candidate_generation == 1
    event = control.tick(True, True, ready0=True, ready1=True, candidate0=11, candidate1=22)
    assert not event.activate
    assert not control.tick(True, False, candidate0=11, candidate1=22).activate
    event = control.tick(True, True, candidate0=11, candidate1=22)
    assert event.activate and (event.active0, event.active1) == (11, 22)
    control.tick(True, False, candidate0=33, candidate1=44)
    assert not control.ready0_seen and not control.ready1_seen
    assert not control.tick(True, True, ready1=True, candidate0=33, candidate1=44).activate
    assert not control.tick(True, False, ready0=True, candidate0=33, candidate1=44).activate
    assert control.tick(True, True, candidate0=33, candidate1=44).activate

    artifacts_a = build_artifacts(baseline_raw, baseline)
    artifacts_b = build_artifacts(baseline_raw, baseline)
    assert artifacts_a == artifacts_b
    assert set(artifacts_a) == {"scene_packet.bin", "ideal_preview.ppm", "device_preview.ppm",
                                "pixel_comparison.json", "manifest.json"}
    assert artifacts_a["scene_packet.bin"] == wire
    assert len(artifacts_a["device_preview.ppm"]) == len(HEADER) + 640 * 480 * 3
    manifest = json.loads(artifacts_a["manifest.json"])
    assert manifest["device_model"] and not manifest["physical_observation"]
    assert not manifest["cycle_timing_model"]
    for field, paths in (("software_source_sha256", MODULES), ("profile_source_sha256", PROFILE)):
        assert set(manifest[field]) == set(paths)
        for path in paths:
            assert manifest[field][path] == hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    assert manifest["scene_packet_sha256"] == hashlib.sha256(wire).hexdigest()
    for field, filename in (("ideal_preview_sha256", "ideal_preview.ppm"),
                            ("device_preview_sha256", "device_preview.ppm"),
                            ("pixel_comparison_sha256", "pixel_comparison.json")):
        assert manifest[field] == hashlib.sha256(artifacts_a[filename]).hexdigest()
    comparison = json.loads(artifacts_a["pixel_comparison.json"])
    assert comparison["full_frame_rgb"]["pixels"] == 640 * 480
    assert comparison["full_frame_rgb"]["exact_match_pixels"] + comparison["full_frame_rgb"]["different_pixels"] == 640 * 480
    for sample in comparison["samples"]:
        if sample["baseline_fixture_expectation"]["x"] in (10, 100, 540, 200, 400, 320):
            assert sample["actual_device_decision"]["rgb"] == sample["actual_ideal_decision"]["rgb"]

    writer_target = ROOT / "build/gpu_evaluation" / f"s2_writer_test_{os.getpid()}"
    invalid_target = ROOT / "build/gpu_evaluation" / f"s2_writer_invalid_{os.getpid()}"
    assert not writer_target.exists() and not invalid_target.exists()
    try:
        write_device_preview(SCENE_JSON, writer_target)
        written = {item.name: item.read_bytes() for item in writer_target.iterdir()}
        try:
            write_device_preview(SCENE_JSON, writer_target)
        except ValueError:
            pass
        else:
            raise AssertionError("device-preview overwrote an existing output directory")
        assert {item.name: item.read_bytes() for item in writer_target.iterdir()} == written
        with tempfile.TemporaryDirectory(prefix="gpu_s2_invalid_") as directory:
            invalid_scene = Path(directory) / "invalid.json"
            invalid_scene.write_text("{}", encoding="utf-8")
            try:
                write_device_preview(invalid_scene, invalid_target)
            except ValueError:
                pass
            else:
                raise AssertionError("device-preview accepted an invalid scene")
        assert not invalid_target.exists()
    finally:
        shutil.rmtree(writer_target, ignore_errors=True)
        shutil.rmtree(invalid_target, ignore_errors=True)

    changed_packet = compile_packet(changed)
    changed_model = prepare_scene(changed_packet)
    points = {(100, 300): tuple(pixel_decision(changed_model, 100, 300)["rgb"]),
              (540, 300): tuple(pixel_decision(changed_model, 540, 300)["rgb"])}
    assert points[(100, 300)] == (0, 0, 0) and points[(540, 300)] == (0, 15, 0)
    _rtl_packet_datapath(changed_packet, points)
    print("PASS: packet decode, loader/control events, deterministic artifacts, and S2 model")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
