// spu_quadray_regfile_ecc.v — Quadray Register File with ECC Wrapper (v2.0)
//
// Wraps spu_quadray_regfile with Hamming(72,64) SECDED.
// Single-bit errors corrected inline (combinational, zero-cycle).
// Double-bit errors assert ecc_double_err.
//
// Copyright 2026 John Curley — CC0 1.0 Universal

module spu_quadray_regfile_ecc #(
    parameter AXES = 13,
    parameter LANE_BITS = 64,
    parameter LANE_AW = 4
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [LANE_AW-1:0]  rd_lane,
    output wire [LANE_BITS-1:0] rd_A, rd_B, rd_C, rd_D,
    input  wire                 wr_en,
    input  wire [LANE_AW-1:0]   wr_lane,
    input  wire [LANE_BITS-1:0] wr_A, wr_B, wr_C, wr_D,
    input  wire                 init_en,
    input  wire [LANE_AW-1:0]   init_lane,
    input  wire [LANE_BITS-1:0] init_A, init_B, init_C, init_D,
    output wire [LANE_BITS-1:0] dbg_A, dbg_B, dbg_C, dbg_D,
    output wire                 ecc_single_err,
    output wire                 ecc_double_err
);

    wire [LANE_BITS-1:0] raw_A, raw_B, raw_C, raw_D;

    spu_quadray_regfile #(.AXES(AXES), .LANE_BITS(LANE_BITS), .LANE_AW(LANE_AW))
    u_regfile (
        .clk(clk), .rst_n(rst_n),
        .rd_lane(rd_lane),
        .rd_A(raw_A), .rd_B(raw_B), .rd_C(raw_C), .rd_D(raw_D),
        .wr_en(wr_en), .wr_lane(wr_lane),
        .wr_A(wr_A), .wr_B(wr_B), .wr_C(wr_C), .wr_D(wr_D),
        .init_en(init_en), .init_lane(init_lane),
        .init_A(init_A), .init_B(init_B), .init_C(init_C), .init_D(init_D),
        .dbg_A(dbg_A), .dbg_B(dbg_B), .dbg_C(dbg_C), .dbg_D(dbg_D)
    );

    reg [7:0] par_A [0:AXES-1];
    reg [7:0] par_B [0:AXES-1];
    reg [7:0] par_C [0:AXES-1];
    reg [7:0] par_D [0:AXES-1];

    localparam [7:0] RESET_PAR_A = 8'hA7;  // ECC for 64'h0000_0001_0000_0000
    localparam [7:0] RESET_PAR_ZERO = 8'h00;

    wire [63:0] enc_in_A, enc_in_B, enc_in_C, enc_in_D;
    assign enc_in_A = init_en ? init_A : wr_A;
    assign enc_in_B = init_en ? init_B : wr_B;
    assign enc_in_C = init_en ? init_C : wr_C;
    assign enc_in_D = init_en ? init_D : wr_D;

    wire [7:0] enc_A, enc_B, enc_C, enc_D;
    spu_hamming_72_64 u_enc_A (.data_in(enc_in_A), .parity_out(enc_A),
        .data_check(64'd0), .parity_in(8'd0), .data_corrected(), .single_err(), .double_err());
    spu_hamming_72_64 u_enc_B (.data_in(enc_in_B), .parity_out(enc_B),
        .data_check(64'd0), .parity_in(8'd0), .data_corrected(), .single_err(), .double_err());
    spu_hamming_72_64 u_enc_C (.data_in(enc_in_C), .parity_out(enc_C),
        .data_check(64'd0), .parity_in(8'd0), .data_corrected(), .single_err(), .double_err());
    spu_hamming_72_64 u_enc_D (.data_in(enc_in_D), .parity_out(enc_D),
        .data_check(64'd0), .parity_in(8'd0), .data_corrected(), .single_err(), .double_err());

    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < AXES; i = i + 1) begin
                par_A[i] <= RESET_PAR_A;    par_B[i] <= RESET_PAR_ZERO;
                par_C[i] <= RESET_PAR_ZERO; par_D[i] <= RESET_PAR_ZERO;
            end
        end else begin
            if (init_en) begin
                par_A[init_lane] <= enc_A; par_B[init_lane] <= enc_B;
                par_C[init_lane] <= enc_C; par_D[init_lane] <= enc_D;
            end else if (wr_en) begin
                par_A[wr_lane] <= enc_A; par_B[wr_lane] <= enc_B;
                par_C[wr_lane] <= enc_C; par_D[wr_lane] <= enc_D;
            end
        end
    end

    wire esA, esB, esC, esD, edA, edB, edC, edD;

    spu_hamming_72_64 u_dec_A (.data_in(64'd0), .parity_out(),
        .data_check(raw_A), .parity_in(par_A[rd_lane]),
        .data_corrected(rd_A), .single_err(esA), .double_err(edA));
    spu_hamming_72_64 u_dec_B (.data_in(64'd0), .parity_out(),
        .data_check(raw_B), .parity_in(par_B[rd_lane]),
        .data_corrected(rd_B), .single_err(esB), .double_err(edB));
    spu_hamming_72_64 u_dec_C (.data_in(64'd0), .parity_out(),
        .data_check(raw_C), .parity_in(par_C[rd_lane]),
        .data_corrected(rd_C), .single_err(esC), .double_err(edC));
    spu_hamming_72_64 u_dec_D (.data_in(64'd0), .parity_out(),
        .data_check(raw_D), .parity_in(par_D[rd_lane]),
        .data_corrected(rd_D), .single_err(esD), .double_err(edD));

    assign ecc_single_err = esA | esB | esC | esD;
    assign ecc_double_err = edA | edB | edC | edD;

endmodule
