// Thin wrapper: davis_gate_dsp -> rplu_exp integration for verification
// - Takes q_vector, material_id, and routes the SPU-13 axis radius into RPLU
// - Starts rplu_exp and exposes v_q16/dissoc/done

module davis_to_rplu(
    input  wire clk,
    input  wire rst_n,
    input  wire start,
    input  wire [63:0] q_vector,
    input  wire [7:0] material_id,
    // runtime config inputs (piped from top-level rplu_cfg bus)
    input  wire cfg_wr_en,
    input  wire [2:0] cfg_wr_sel,
    input  wire [7:0] cfg_wr_material,
    input  wire [9:0] cfg_wr_addr,
    input  wire [63:0] cfg_wr_data,
    output wire signed [31:0] v_q16,
    output wire dissoc,
    output wire done,
    output wire [31:0] quadrance,
    output wire [31:0] ivm_quadrance,
    output wire [15:0] gasket_sum,
    output wire signed [31:0] audio_p,
    output wire signed [31:0] audio_q,
    output wire signed [2:0] ratio_cmp_res,
    output wire ratio_cmp_valid,
    output wire [9:0] r_addr_dbg,
    output wire signed [31:0] r_q16_dbg
);
    wire [63:0] q_rotated;

    davis_gate_dsp #(.DEVICE("SIM")) u_davis (
        .clk(clk),
        .rst_n(rst_n),
        .q_vector(q_vector),
        .q_rotated(q_rotated),
        .quadrance(quadrance),
        .ivm_quadrance(ivm_quadrance),
        .gasket_sum(gasket_sum),
        .audio_p(audio_p),
        .audio_q(audio_q)
    );

    // SPU-13 passes a 64-bit axis as {P[31:0], Q[31:0]} in Q12. Convert
    // the dominant component to a coarse Q16.16 scalar radius for the RPLU.
    wire signed [31:0] axis_p_q12;
    wire signed [31:0] axis_q_q12;
    wire [31:0] abs_p_q12;
    wire [31:0] abs_q_q12;
    wire [31:0] radius_q12;
    wire signed [31:0] r_q16;
    assign axis_p_q12 = q_vector[63:32];
    assign axis_q_q12 = q_vector[31:0];
    assign abs_p_q12 = axis_p_q12[31] ? (~axis_p_q12 + 1'b1) : axis_p_q12;
    assign abs_q_q12 = axis_q_q12[31] ? (~axis_q_q12 + 1'b1) : axis_q_q12;
    assign radius_q12 = (abs_p_q12 > abs_q_q12) ? abs_p_q12 : abs_q_q12;

    // Per-material radius calibration.
    // Each Morse table samples r from 0.5*re to 1.5*re in 1024 steps.
    // R_MIN/R_MAX in Q16.16, R_ADDR_RECIP = int(1023 * 65536 / re).
    //
    // Material re (Angstrom): C=1.54, Fe=2.48, Al=2.86, Si=2.35,
    //                         Ti=2.93, Ni=2.49, Cu=2.56, W=2.74
    wire signed [31:0] calib_R_MIN_Q16;
    wire signed [31:0] calib_R_MAX_Q16;
    wire [15:0]        calib_R_ADDR_RECIP_Q16;

    reg signed [31:0] r_min_lut;
    reg signed [31:0] r_max_lut;
    reg [15:0]        recip_lut;
    always @(*) begin
        case (material_id)
            8'd0: begin r_min_lut = 32'sh0000_C51F; r_max_lut = 32'sh0002_4F5C; recip_lut = 16'd664; end
            8'd1: begin r_min_lut = 32'sh0001_3D71; r_max_lut = 32'sh0003_B852; recip_lut = 16'd413; end
            8'd2: begin r_min_lut = 32'sh0001_6E14; r_max_lut = 32'sh0004_4A3D; recip_lut = 16'd358; end
            8'd3: begin r_min_lut = 32'sh0001_2CD1; r_max_lut = 32'sh0003_8666; recip_lut = 16'd435; end
            8'd4: begin r_min_lut = 32'sh0001_770A; r_max_lut = 32'sh0004_651F; recip_lut = 16'd349; end
            8'd5: begin r_min_lut = 32'sh0001_3EB8; r_max_lut = 32'sh0003_BC29; recip_lut = 16'd411; end
            8'd6: begin r_min_lut = 32'sh0001_47AE; r_max_lut = 32'sh0003_D70A; recip_lut = 16'd400; end
            8'd7: begin r_min_lut = 32'sh0001_5EB8; r_max_lut = 32'sh0004_1C29; recip_lut = 16'd373; end
            default: begin r_min_lut = 32'sh0000_C51F; r_max_lut = 32'sh0002_4F5C; recip_lut = 16'd664; end
        endcase
    end

    assign calib_R_MIN_Q16 = r_min_lut;
    assign calib_R_MAX_Q16 = r_max_lut;
    assign calib_R_ADDR_RECIP_Q16 = recip_lut;

    wire [31:0] radius_q16_clamped;
    wire [35:0] radius_q16_wide;
    wire signed [31:0] r_delta_q16;
    wire [47:0] r_addr_scaled;
    wire [15:0] r_addr_unclamped;
    wire [9:0] r_addr;
    assign radius_q16_wide = {4'd0, radius_q12} << 4;
    assign radius_q16_clamped = (radius_q16_wide >= {4'd0, calib_R_MAX_Q16[31:0]}) ?
        calib_R_MAX_Q16[31:0] : radius_q16_wide[31:0];
    assign r_q16 = $signed(radius_q16_clamped);
    assign r_delta_q16 = r_q16 - calib_R_MIN_Q16;
    assign r_addr_scaled = r_delta_q16[31:0] * calib_R_ADDR_RECIP_Q16;
    assign r_addr_unclamped = r_addr_scaled[31:16];
    assign r_addr = (r_q16 <= calib_R_MIN_Q16) ? 10'd0 :
                    (r_q16 >= calib_R_MAX_Q16) ? 10'd1023 :
                    (r_addr_unclamped > 16'd1023) ? 10'd1023 :
                    r_addr_unclamped[9:0];

    reg r_start;
    reg [9:0] r_addr_reg;
    reg signed [31:0] r_q16_reg;
    reg [7:0] material_id_reg;
    assign r_addr_dbg = r_addr_reg;
    assign r_q16_dbg = r_q16_reg;

    rplu_exp u_rplu (
        .clk(clk),
        .rst_n(rst_n),
        .start(r_start),
        .addr(r_addr_reg),
        .material_id(material_id_reg),
        .r_q16(r_q16_reg),
        .wake(1'b0),
        .wake_addr(10'd0),
        .cfg_wr_en(cfg_wr_en),
        .cfg_wr_sel(cfg_wr_sel),
        .cfg_wr_material(cfg_wr_material),
        .cfg_wr_addr(cfg_wr_addr),
        .cfg_wr_data(cfg_wr_data),
        .v_q16(v_q16),
        .dissoc(dissoc),
        .done(done),
        .laminar_irq(),
        .ratio_cmp_res(ratio_cmp_res),
        .ratio_cmp_valid(ratio_cmp_valid)
    );

    reg started;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            started <= 1'b0;
            r_start <= 1'b0;
            r_addr_reg <= 10'd0;
            r_q16_reg <= 32'sd0;
            material_id_reg <= 8'd0;
        end else begin
            r_start <= 1'b0;
            if (start && !started) begin
                // Capture the axis while start is asserted; rplu_exp sees
                // r_start one cycle later after the SPU axis pointer advances.
                r_addr_reg <= r_addr;
                r_q16_reg <= r_q16;
                material_id_reg <= material_id;
                r_start <= 1'b1;
                started <= 1'b1;
                `ifdef SIM
                $display("DAVIS2RPLU: start pulse time=%0t quadrance=%0d", $time, quadrance);
                `endif
            end
            if (done) begin
                started <= 1'b0;
                `ifdef SIM
                $display("DAVIS2RPLU: rplu done time=%0t v=%0d dissoc=%b", $time, v_q16, dissoc);
                `endif
            end
        end
    end
endmodule
