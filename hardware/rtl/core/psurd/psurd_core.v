// psurd_core.v — v0.3 programmable-surd execution core (RTL-0A; frozen contract §2-§9, §12.2).
// Sequential multicycle FSM, one instruction in flight. Step order (§7): BUDGET, then PC_OVERRUN, fetch,
// decode, operand check, execute, retire. BR order: encoding, target, CV, condition. Gen-1 shared-unit
// status codes are translated by name: OVERFLOW is recoverable (R, RS); INVALID/ENGINE_FAULT are terminal.
module psurd_core (
    input  wire clk, rst, start,
    input  wire [31:0] budget,
    input  wire [8:0]  img_len,                 // L, 1..256 (RTL-0B loader supplies it; RTL-0A bench drives it)
    input  wire imem_we,                        // image write port (RTL-0B loader; RTL-0S synthesis top)
    input  wire [7:0]  imem_waddr,
    input  wire [63:0] imem_wdata,
    input  wire [2:0]  dump_ra,                 // RTL-0B D4: while done, bank read port A serves the record builder
    output wire [191:0] dump_q,
    output wire dump_valid,
    output reg  done,                           // level: run ended, record state valid
    output reg  [2:0] cause,                    // 0 HALT 1 BAD_ENCODING 2 INVALID 3 ENGINE_FAULT 4 BAD_TARGET 5 PC_OVERRUN 6 BUDGET
    output reg  [8:0] pc,
    output reg  [31:0] retired,
    output reg  Z, N, P, CV, R, RS,
    output reg  [1:0] status                    // last arithmetic status: 0 OK, 2 OVERFLOW
);
    localparam S_IDLE = 3'd0, S_RESET = 3'd1, S_CHECK = 3'd2, S_FETCH = 3'd3, S_EXEC = 3'd4, S_WAIT = 3'd5, S_END = 3'd6;
    reg [2:0] state;
    wire [63:0] word;
    wire [2:0] cls, aop, rd, ra, rb, slc; wire [31:0] pay; wire [3:0] cc; wire [15:0] tgt;
    wire [191:0] qa; wire va, vb, slice_ok, commit_ok, adone; wire [3:0] astat;
    wire szero, sneg, spos;
    wire ex = state == S_EXEC;
    wire sli_go  = ex && cls == 3'd1 && slice_ok;
    wire sld_go  = ex && cls == 3'd2 && commit_ok;
    wire ar_go   = ex && cls == 3'd3 && va && (aop == 3'd6 || vb);
    wire slik_go = ex && cls == 3'd4;
    psurd_imem imem (.clk(clk), .raddr(pc[7:0]), .rdata(word), .we(imem_we), .waddr(imem_waddr), .wdata(imem_wdata));
    psurd_decode dec (.w(word), .cls(cls), .arith_op(aop), .rd(rd), .ra(ra), .rb(rb), .slice(slc),
        .payload(pay), .cc(cc), .target(tgt));
    assign dump_q = qa; assign dump_valid = va;
    psurd_exec exu (.clk(clk), .rst(rst || state == S_RESET), .ra(done ? dump_ra : ra), .rb(rb), .qa(qa),
        .valid_a(va), .valid_b(vb), .sli_en(sli_go), .sld_en(sld_go), .st_target(rd), .st_slice(slc),
        .st_payload(pay), .slice_ok(slice_ok), .commit_ok(commit_ok), .slik_we(slik_go), .slik_rd(rd),
        .slik_imm(pay), .arith_start(ar_go), .arith_op(aop), .arith_rd(rd), .arith_done(adone), .arith_status(astat));
    psurd_sign sgn (.t(qa), .zero(szero), .neg(sneg), .pos(spos));
    wire sign_cc = cc >= 4'd1 && cc <= 4'd6;
    reg take;
    always @* case (cc)
        4'd0: take = 1'b1;  4'd1: take = Z;   4'd2: take = !Z;  4'd3: take = N;  4'd4: take = !N;
        4'd5: take = P;     4'd6: take = !P;  4'd7: take = R;   4'd8: take = !R; default: take = RS;
    endcase
    task finish(input [2:0] c); begin cause <= c; done <= 1'b1; state <= S_END; end endtask
    task retire(input [8:0] nxt); begin retired <= retired + 32'd1; pc <= nxt; state <= S_CHECK; end endtask
    always @(posedge clk) begin
        if (rst) begin
            state <= S_IDLE; done <= 1'b0; cause <= 3'd0; pc <= 9'd0; retired <= 32'd0;
            {Z, N, P, CV, R, RS} <= 6'd0; status <= 2'd0;
        end else case (state)
            S_IDLE, S_END: if (start) begin                     // §9 clean start
                state <= S_RESET; done <= 1'b0; cause <= 3'd0; pc <= 9'd0; retired <= 32'd0;
                {Z, N, P, CV, R, RS} <= 6'd0; status <= 2'd0;
            end
            S_RESET: state <= S_CHECK;                           // exu held in reset for this cycle
            S_CHECK: if (retired == budget) finish(3'd6);
                     else if (pc >= img_len) finish(3'd5);
                     else state <= S_FETCH;
            S_FETCH: state <= S_EXEC;                            // synchronous imem read
            S_EXEC: case (cls)
                3'd0: finish(3'd1);
                3'd1: if (slice_ok) retire(pc + 9'd1); else finish(3'd2);
                3'd2: if (commit_ok) retire(pc + 9'd1); else finish(3'd2);
                3'd3: if (va && (aop == 3'd6 || vb)) state <= S_WAIT; else finish(3'd2);
                3'd4: retire(pc + 9'd1);
                3'd5: if (!va) finish(3'd2);
                      else begin Z <= szero; N <= sneg; P <= spos; CV <= 1'b1; retire(pc + 9'd1); end
                3'd6: if ({1'b0, tgt} >= {8'd0, img_len}) finish(3'd4);
                      else if (sign_cc && !CV) finish(3'd2);
                      else retire(take ? tgt[8:0] : pc + 9'd1);
                default: begin retired <= retired + 32'd1; finish(3'd0); end   // HALT retires
            endcase
            S_WAIT: if (adone) case (astat)
                4'd0: begin R <= 1'b0; status <= 2'd0; retire(pc + 9'd1); end
                4'd2: begin R <= 1'b1; RS <= 1'b1; status <= 2'd2; retire(pc + 9'd1); end
                4'd1: finish(3'd2);
                default: finish(3'd3);
            endcase
            default: state <= S_IDLE;
        endcase
    end
endmodule
