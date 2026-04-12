// Thin wrapper: davis_gate_dsp -> rplu_exp integration for verification
// - Takes q_vector, material_id, and routes quadrance -> r_q16 (normalization)
// - Starts rplu_exp and exposes v_q16/dissoc/done

module davis_to_rplu(
    input  wire clk,
    input  wire rst_n,
    input  wire start,
    input  wire [63:0] q_vector,
    input  wire material_id,
    // runtime config inputs (piped from top-level rplu_cfg bus)
    input  wire cfg_wr_en,
    input  wire [2:0] cfg_wr_sel,
    input  wire cfg_wr_material,
    input  wire [9:0] cfg_wr_addr,
    input  wire [63:0] cfg_wr_data,
    output wire signed [31:0] v_q16,
    output wire dissoc,
    output wire done
);
    wire [63:0] q_rotated;
    wire [31:0] quadrance;
    wire [31:0] ivm_quadrance;
    wire [15:0] gasket_sum;
    wire signed [31:0] audio_p, audio_q;

    davis_gate_dsp #(.DEVICE("SIM")) u_davis (
        .clk(clk), .rst_n(rst_n), .q_vector(q_vector), .q_rotated(q_rotated),
        .quadrance(quadrance), .ivm_quadrance(ivm_quadrance), .gasket_sum(gasket_sum),
        .audio_p(audio_p), .audio_q(audio_q)
    );

    // normalization: map quadrance (u32) to r_q16 domain. For now use simple scaling
    // quadrance is roughly proportional to squared displacement; map by sqrt approximation
    // Here: treat quadrance[31:16] as Q16 value for r (coarse mapping). Replace with proper mapping later.
    wire signed [31:0] r_q16;
    assign r_q16 = { quadrance[31:16] };

    reg r_start;
    rplu_exp u_rplu (.clk(clk), .rst_n(rst_n), .start(r_start), .addr(10'd0), .material_id(material_id), .r_q16(r_q16), .cfg_wr_en(cfg_wr_en), .cfg_wr_sel(cfg_wr_sel), .cfg_wr_material(cfg_wr_material), .cfg_wr_addr(cfg_wr_addr), .cfg_wr_data(cfg_wr_data), .v_q16(v_q16), .dissoc(dissoc), .done(done));

    // simple control: when top start pulses, trigger rplu once after one cycle
    reg started;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            started <= 1'b0; r_start <= 1'b0;
        end else begin
            r_start <= 1'b0;
            if (start && !started) begin
                // start after one cycle to allow davis to compute
                r_start <= 1'b1;
                started <= 1'b1;
                $display("DAVIS2RPLU: start pulse time=%0t quadrance=%0d", $time, quadrance);
            end
            if (done) begin
                started <= 1'b0;
                $display("DAVIS2RPLU: rplu done time=%0t v=%0d dissoc=%b", $time, v_q16, dissoc);
            end
        end
    end
endmodule
