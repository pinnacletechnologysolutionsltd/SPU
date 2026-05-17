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
        .clk(clk), .rst_n(rst_n), .q_vector(q_vector), .q_rotated(q_rotated),
        .quadrance(quadrance), .ivm_quadrance(ivm_quadrance), .gasket_sum(gasket_sum),
        .audio_p(audio_p), .audio_q(audio_q)
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

    // Carbon vnorm/r_rom spans r=0x0000c51f..0x00024f5c in Q16.16.
    // Convert the radius into a 10-bit table address with a Q16 reciprocal
    // for 1023 / span, then clamp outside the calibrated table range.
    localparam signed [31:0] R_MIN_Q16 = 32'sh0000_c51f;
    localparam signed [31:0] R_MAX_Q16 = 32'sh0002_4f5c;
    localparam [31:0] R_MAX_Q12 = 32'h0000_24f5;
    localparam [15:0] R_ADDR_RECIP_Q16 = 16'd664;

    wire [31:0] radius_q16_clamped;
    wire signed [31:0] r_delta_q16;
    wire [47:0] r_addr_scaled;
    wire [15:0] r_addr_unclamped;
    wire [9:0] r_addr;
    assign radius_q16_clamped = (radius_q12 >= R_MAX_Q12) ? R_MAX_Q16[31:0] : (radius_q12 << 4);
    assign r_q16 = $signed(radius_q16_clamped);
    assign r_delta_q16 = r_q16 - R_MIN_Q16;
    assign r_addr_scaled = r_delta_q16[31:0] * R_ADDR_RECIP_Q16;
    assign r_addr_unclamped = r_addr_scaled[31:16];
    assign r_addr = (r_q16 <= R_MIN_Q16) ? 10'd0 :
                    (r_q16 >= R_MAX_Q16) ? 10'd1023 :
                    (r_addr_unclamped > 16'd1023) ? 10'd1023 :
                    r_addr_unclamped[9:0];

    reg r_start;
    reg [9:0] r_addr_reg;
    reg signed [31:0] r_q16_reg;
    reg [7:0] material_id_reg;
    assign r_addr_dbg = r_addr_reg;
    assign r_q16_dbg = r_q16_reg;

    rplu_exp u_rplu (.clk(clk), .rst_n(rst_n), .start(r_start), .addr(r_addr_reg), .material_id(material_id_reg), .r_q16(r_q16_reg), .wake(1'b0), .wake_addr(10'd0), .cfg_wr_en(cfg_wr_en), .cfg_wr_sel(cfg_wr_sel), .cfg_wr_material(cfg_wr_material), .cfg_wr_addr(cfg_wr_addr), .cfg_wr_data(cfg_wr_data), .v_q16(v_q16), .dissoc(dissoc), .done(done), .laminar_irq(), .ratio_cmp_res(ratio_cmp_res), .ratio_cmp_valid(ratio_cmp_valid));

    // simple control: when top start pulses, trigger rplu once after one cycle
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
