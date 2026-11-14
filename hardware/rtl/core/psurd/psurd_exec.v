// psurd_exec.v — v0.3 execute wrapper (RTL-0A). Instantiates the UNCHANGED shared Gen-1 modules
// spu13_surd_load and spu13_surd_arith, and the v0.3 LUTRAM bank psurd_bank_lutram (RF-B, adopted 2026-11-11;
// the shared spu13_surd_bank is the qualified fallback RF-A). Adds what the Gen-1 wrapper lacked:
// a direct SLIK write path and the A read port exposed for STST. The bank is written only for
// SLD commit, SLIK, or arith completion with status OK: a refused (OVERFLOW) result is never written,
// including when the destination aliases a source (operands are latched by the arith unit at start).
module psurd_exec (
    input  wire clk, rst,                       // rst: execution reset at START (clears mask and staging)
    input  wire [2:0] ra, rb,                   // bank read ports (combinational)
    output wire [191:0] qa,
    output wire valid_a, valid_b,
    input  wire sli_en, sld_en,                 // staging write / commit (core checks slice_ok / commit_ok)
    input  wire [2:0] st_target, st_slice,
    input  wire [31:0] st_payload,
    output wire slice_ok, commit_ok,
    input  wire slik_we,
    input  wire [2:0] slik_rd,
    input  wire [31:0] slik_imm,
    input  wire arith_start,
    input  wire [2:0] arith_op, arith_rd,
    output wire arith_done,
    output wire [3:0] arith_status             // shared-unit numbering: 0 OK, 1 INVALID, 2 OVERFLOW, 3 ENGINE_FAULT
);
    wire [191:0] qb, staged, arith_result;
    wire [3:0] phase;
    wire rescue_request, normalization_start;
    reg  [2:0] held_rd;
    reg  busy;
    wire arith_ok = arith_done && busy && arith_status == 4'd0;
    wire [191:0] slik_tuple = {64'd1, 64'd0, {{32{slik_imm[31]}}, slik_imm}};
    wire we = arith_ok || (sld_en && commit_ok) || slik_we;
    wire [2:0] wa = arith_ok ? held_rd : (sld_en ? st_target : slik_rd);
    wire [191:0] wd = arith_ok ? arith_result : (sld_en ? staged : slik_tuple);
    psurd_bank_lutram bank (.clk(clk), .rst(rst), .ra(ra), .rb(rb), .qa(qa), .qb(qb),
        .valid_a(valid_a), .valid_b(valid_b), .we(we), .wa(wa), .wd(wd));
    spu13_surd_load loader (.clk(clk), .rst(rst), .slice_en(sli_en), .commit_en(sld_en),
        .target(st_target), .slice(st_slice), .payload(st_payload),
        .slice_ok(slice_ok), .commit_ok(commit_ok), .tuple(staged));
    spu13_surd_arith arith (.clk(clk), .rst(rst), .start(arith_start), .op(arith_op), .lhs(qa), .rhs(qb),
        .done(arith_done), .status(arith_status), .result(arith_result), .phase(phase),
        .rescue_request(rescue_request), .normalization_start(normalization_start));
    always @(posedge clk) begin
        if (rst) begin busy <= 1'b0; held_rd <= 3'd0; end
        else if (arith_start) begin busy <= 1'b1; held_rd <= arith_rd; end
        else if (arith_done) busy <= 1'b0;
    end
endmodule
