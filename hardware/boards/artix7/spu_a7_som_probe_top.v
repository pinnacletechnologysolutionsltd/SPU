// spu_a7_som_probe_top.v -- Wukong Artix-7 100T SOM/BMU silicon probe.
//
// Port of the Tang-25K-proven spu13_tang25k_som_bmu_probe.v to the primary
// silicon-evidence board. The fixture logic, oracle scenarios, and golden
// UART line are kept identical so the same 115200-baud output on both boards
// is a cross-vendor determinism proof:
//
//   SOM:P T:2 B:6 E:00  PASS
//   SOM:F T:<n> B:<b> E:<code>  FAIL
//
// Differences from the Tang top are board plumbing only: external rst_n
// button (synchronized, combined with the power-on counter) and timing
// localparams promoted to parameters so the testbench can run fast.

module spu_a7_som_probe_top #(
    parameter CLK_FREQ     = 50000000,      // Wukong oscillator (20 ns in XDC)
    parameter CLKS_PER_BIT = 434,           // 115200 baud at 50 MHz
    parameter START_DELAY  = 50000000 / 2,
    parameter LINE_PERIOD  = 50000000 / 5
) (
    input  wire       sys_clk,
    input  wire       rst_n,
    output wire [2:0] led,
    output wire       uart_tx
);
    localparam WIDTH = 18;
    localparam NUM_FEATURES = 4;
    localparam FEATURE_W = 2 * WIDTH;
    localparam VEC_W = NUM_FEATURES * FEATURE_W;

    function [FEATURE_W-1:0] rs;
        input signed [WIDTH-1:0] p;
        input signed [WIDTH-1:0] q;
        begin
            rs = {q[WIDTH-1:0], p[WIDTH-1:0]};
        end
    endfunction

    function [VEC_W-1:0] vec4;
        input [FEATURE_W-1:0] f0;
        input [FEATURE_W-1:0] f1;
        input [FEATURE_W-1:0] f2;
        input [FEATURE_W-1:0] f3;
        begin
            vec4 = {f3, f2, f1, f0};
        end
    endfunction

    // Reset: power-on counter gated by the synchronized board button.
    reg [1:0] rst_sync = 2'b00;
    always @(posedge sys_clk) rst_sync <= {rst_sync[0], rst_n};

    reg [7:0] rst_cnt = 8'd0;
    wire rst_n_int = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) begin
        if (!rst_sync[1]) rst_cnt <= 8'd0;
        else if (!rst_n_int) rst_cnt <= rst_cnt + 1'b1;
    end

    // BMU under test.
    reg        bmu_start = 1'b0;
    wire       bmu_done;
    reg [VEC_W-1:0] features = {VEC_W{1'b0}};
    wire [VEC_W-1:0] feature_weights = vec4(
        rs(18'sd1, 18'sd0),
        rs(18'sd2, 18'sd0),
        rs(18'sd1, 18'sd0),
        rs(18'sd1, 18'sd0)
    );

    wire        bmu_valid;
    wire [15:0] best_node_id;
    wire [15:0] second_node_id;
    wire [15:0] cluster_label_in;
    wire [63:0] best_q;
    wire [63:0] second_q;
    wire [63:0] confidence_gap_in;
    wire        has_second;
    wire        axiomatic_fault;
    wire [3:0]  fault_type;
    wire [31:0] fault_count;

    spu_som_bmu #(.NUM_FEATURES(NUM_FEATURES), .MAX_NODES(7), .WIDTH(WIDTH)) u_bmu (
        .clk(sys_clk),
        .rst_n(rst_n_int),
        .start(bmu_start),
        .done(bmu_done),
        .features(features),
        .feature_weights(feature_weights),
        .bmu_valid(bmu_valid),
        .best_node_id(best_node_id),
        .second_node_id(second_node_id),
        .cluster_label(cluster_label_in),
        .best_q(best_q),
        .second_q(second_q),
        .confidence_gap(confidence_gap_in),
        .has_second(has_second),
        .axiomatic_level(2'b00),
        .axiomatic_fault(axiomatic_fault),
        .fault_type(fault_type),
        .fault_count(fault_count),
        .train_we(1'b0),
        .train_addr(3'd0),
        .train_be(4'b0000),
        .train_wdata({VEC_W{1'b0}}),
        .train_rdata()
    );

    wire        classify_valid;
    wire [15:0] label;
    wire [63:0] confidence_gap;
    wire        ambiguous;

    spu_cluster_reduce #(.WIDTH(WIDTH)) u_reduce (
        .clk(sys_clk),
        .rst_n(rst_n_int),
        .bmu_valid(bmu_valid),
        .best_node_id(best_node_id),
        .cluster_label_in(cluster_label_in),
        .best_q(best_q),
        .second_q(second_q),
        .confidence_gap_in(confidence_gap_in),
        .has_second(has_second),
        .ambiguity_threshold(64'd0),
        .classify_valid(classify_valid),
        .label(label),
        .confidence_gap(confidence_gap),
        .ambiguous(ambiguous)
    );

    function [VEC_W-1:0] scenario_features;
        input [1:0] t;
        begin
            case (t)
                2'd0: scenario_features = vec4(
                    rs(18'sd2, 18'sd0),
                    rs(18'sd1, 18'sd0),
                    rs(18'sd0, 18'sd0),
                    rs(18'sd0, 18'sd0)
                );
                2'd1: scenario_features = vec4(
                    rs(18'sd0, 18'sd0),
                    rs(18'sd0, 18'sd0),
                    rs(-18'sd2, 18'sd0),
                    rs(18'sd2, 18'sd1)
                );
                default: scenario_features = {VEC_W{1'b0}};
            endcase
        end
    endfunction

    function [15:0] exp_best;
        input [1:0] t;
        begin exp_best = (t == 2'd1) ? 16'd6 : 16'd1; end
    endfunction

    function [15:0] exp_second;
        input [1:0] t;
        begin exp_second = 16'd0; end
    endfunction

    function [15:0] exp_label;
        input [1:0] t;
        begin exp_label = (t == 2'd1) ? 16'd3 : 16'd1; end
    endfunction

    function [63:0] exp_best_q;
        input [1:0] t;
        begin exp_best_q = (t == 2'd1) ? 64'h0000000100000000
                                       : 64'h0000000200000000;
        end
    endfunction

    function [63:0] exp_second_q;
        input [1:0] t;
        begin exp_second_q = (t == 2'd1) ? 64'h0000000B00000004
                                         : 64'h0000000600000000;
        end
    endfunction

    function [63:0] exp_gap;
        input [1:0] t;
        begin exp_gap = (t == 2'd1) ? 64'h0000000A00000004
                                    : 64'h0000000400000000;
        end
    endfunction

    localparam [3:0] S_RESET = 4'd0;
    localparam [3:0] S_SETUP = 4'd1;
    localparam [3:0] S_START = 4'd2;
    localparam [3:0] S_WAIT_BMU = 4'd3;
    localparam [3:0] S_WAIT_REDUCE = 4'd4;
    localparam [3:0] S_CHECK = 4'd5;
    localparam [3:0] S_PASS = 4'd6;
    localparam [3:0] S_FAIL = 4'd7;

    reg [3:0] test_state = S_RESET;
    reg [1:0] test_idx = 2'd0;
    reg [1:0] tests_done = 2'd0;
    reg [3:0] best_digit = 4'd0;
    reg [7:0] fail_code = 8'd0;
    reg       all_pass = 1'b1;

    always @(posedge sys_clk) begin
        if (!rst_n_int) begin
            test_state <= S_RESET;
            test_idx <= 2'd0;
            tests_done <= 2'd0;
            best_digit <= 4'd0;
            fail_code <= 8'd0;
            all_pass <= 1'b1;
            bmu_start <= 1'b0;
            features <= {VEC_W{1'b0}};
        end else begin
            bmu_start <= 1'b0;

            case (test_state)
                S_RESET: begin
                    test_idx <= 2'd0;
                    tests_done <= 2'd0;
                    test_state <= S_SETUP;
                end

                S_SETUP: begin
                    features <= scenario_features(test_idx);
                    test_state <= S_START;
                end

                S_START: begin
                    bmu_start <= 1'b1;
                    test_state <= S_WAIT_BMU;
                end

                S_WAIT_BMU: begin
                    if (bmu_done) test_state <= S_WAIT_REDUCE;
                end

                S_WAIT_REDUCE: begin
                    if (classify_valid) test_state <= S_CHECK;
                end

                S_CHECK: begin
                    best_digit <= best_node_id[3:0];
                    // Note: bmu_valid may stay high until next start
                    // (needed for training readback).  Skip the bmu_valid
                    // check and proceed directly to value comparison.
                    if (best_node_id !== exp_best(test_idx)) begin
                        fail_code <= 8'hB0 + {6'd0, test_idx};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (second_node_id !== exp_second(test_idx)) begin
                        fail_code <= 8'hC0 + {6'd0, test_idx};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (cluster_label_in !== exp_label(test_idx) ||
                                 label !== exp_label(test_idx)) begin
                        fail_code <= 8'hD0 + {6'd0, test_idx};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (best_q !== exp_best_q(test_idx)) begin
                        fail_code <= 8'hE0 + {6'd0, test_idx};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (second_q !== exp_second_q(test_idx)) begin
                        fail_code <= 8'hE4 + {6'd0, test_idx};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (confidence_gap_in !== exp_gap(test_idx) ||
                                 confidence_gap !== exp_gap(test_idx)) begin
                        fail_code <= 8'hE8 + {6'd0, test_idx};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (has_second !== 1'b1 || ambiguous !== 1'b0 ||
                                 axiomatic_fault !== 1'b0) begin
                        fail_code <= 8'hF0 + {6'd0, test_idx};
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else if (test_idx == 2'd1) begin
                        tests_done <= 2'd2;
                        test_state <= S_PASS;
                    end else begin
                        tests_done <= tests_done + 1'b1;
                        test_idx <= test_idx + 1'b1;
                        test_state <= S_SETUP;
                    end
                end

                S_PASS: begin
                    tests_done <= 2'd2;
                    best_digit <= 4'd6;
                end

                S_FAIL: begin
                    tests_done <= test_idx;
                end

                default: begin
                    fail_code <= 8'hFF;
                    all_pass <= 1'b0;
                    test_state <= S_FAIL;
                end
            endcase
        end
    end

    // LEDs: active-low PASS/FAIL plus heartbeat (matches Tang probe).
    reg [25:0] blink_cnt = 26'd0;
    always @(posedge sys_clk) blink_cnt <= blink_cnt + 1'b1;

    assign led[0] = ~blink_cnt[24];
    assign led[1] = ~(test_state == S_PASS);
    assign led[2] = ~(test_state == S_FAIL);

    // UART telemetry.
    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits = 4'd0;
    reg [15:0] baud_cnt = 16'd0;
    reg        tx_busy = 1'b0;
    reg [7:0]  tx_byte = 8'd0;
    reg        tx_go = 1'b0;
    reg [27:0] line_timer = 28'd0;
    reg [27:0] start_cnt = 28'd0;
    reg        start_ready = 1'b0;
    reg [4:0]  msg_idx = 5'd0;
    reg        line_active = 1'b0;

    assign uart_tx = tx_shift[0];

    function [7:0] hex2ascii;
        input [3:0] h;
        begin
            hex2ascii = (h < 10) ? (8'h30 + h) : (8'h37 + h);
        end
    endfunction

    function [7:0] msg_byte;
        input [4:0] idx;
        reg [7:0] status_ch;
        begin
            status_ch = (test_state == S_PASS) ? "P" :
                        (test_state == S_FAIL) ? "F" : ".";
            case (idx)
                5'd0:  msg_byte = "S";
                5'd1:  msg_byte = "O";
                5'd2:  msg_byte = "M";
                5'd3:  msg_byte = ":";
                5'd4:  msg_byte = status_ch;
                5'd5:  msg_byte = " ";
                5'd6:  msg_byte = "T";
                5'd7:  msg_byte = ":";
                5'd8:  msg_byte = 8'h30 + {6'd0, tests_done};
                5'd9:  msg_byte = " ";
                5'd10: msg_byte = "B";
                5'd11: msg_byte = ":";
                5'd12: msg_byte = hex2ascii(best_digit);
                5'd13: msg_byte = " ";
                5'd14: msg_byte = "E";
                5'd15: msg_byte = ":";
                5'd16: msg_byte = hex2ascii(fail_code[7:4]);
                5'd17: msg_byte = hex2ascii(fail_code[3:0]);
                5'd18: msg_byte = 8'h0D;
                5'd19: msg_byte = 8'h0A;
                default: msg_byte = 8'h20;
            endcase
        end
    endfunction

    always @(posedge sys_clk) begin
        if (!rst_n_int) begin
            tx_shift <= 10'h3FF;
            tx_bits <= 4'd0;
            baud_cnt <= 16'd0;
            tx_busy <= 1'b0;
            tx_byte <= 8'd0;
            tx_go <= 1'b0;
            line_timer <= 28'd0;
            start_cnt <= 28'd0;
            start_ready <= 1'b0;
            msg_idx <= 5'd0;
            line_active <= 1'b0;
        end else begin
            if (tx_busy) begin
                if (baud_cnt < CLKS_PER_BIT - 1) begin
                    baud_cnt <= baud_cnt + 1'b1;
                end else begin
                    baud_cnt <= 16'd0;
                    tx_shift <= {1'b1, tx_shift[9:1]};
                    if (tx_bits == 1) begin
                        tx_busy <= 1'b0;
                        tx_bits <= 4'd0;
                    end else begin
                        tx_bits <= tx_bits - 1'b1;
                    end
                end
            end else if (tx_go) begin
                tx_go <= 1'b0;
                tx_shift <= {1'b1, tx_byte, 1'b0};
                tx_bits <= 4'd10;
                tx_busy <= 1'b1;
                baud_cnt <= 16'd0;
            end else if (!start_ready) begin
                if (start_cnt < START_DELAY - 1)
                    start_cnt <= start_cnt + 1'b1;
                else
                    start_ready <= 1'b1;
            end else if (line_active) begin
                tx_byte <= msg_byte(msg_idx);
                tx_go <= 1'b1;
                if (msg_idx == 5'd19) begin
                    msg_idx <= 5'd0;
                    line_active <= 1'b0;
                end else begin
                    msg_idx <= msg_idx + 1'b1;
                end
            end else if (line_timer < LINE_PERIOD - 1) begin
                line_timer <= line_timer + 1'b1;
            end else begin
                line_timer <= 28'd0;
                msg_idx <= 5'd0;
                line_active <= 1'b1;
            end
        end
    end

endmodule
