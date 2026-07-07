// spu13_tang25k_som_hydrate_probe.v -- Tang 25K SOM BRAM hydration probe.
//
// Self-checking board proof for the BRAM-backed SOM node-weight store.
// This intentionally tests the storage primitive only: the full writeable BMU
// image exceeds Tang 25K placement headroom, while the existing SOM/BMU probe
// already verifies classification from this same BRAM wrapper.
//
// UART at 115200 baud:
//   HYD:P T:3 B:6 E:00  PASS
//   HYD:F T:<n> B:<b> E:<code>  FAIL

module spu13_tang25k_som_hydrate_probe (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx
);
    localparam CLK_FREQ = 50000000;
    localparam CLKS_PER_BIT = 434;  // 115200 baud at 50 MHz
    localparam START_DELAY = CLK_FREQ / 2;
    localparam LINE_PERIOD = CLK_FREQ / 5;

    localparam WIDTH = 18;
    localparam FEATURE_W = 2 * WIDTH;
    localparam VEC_W = 4 * FEATURE_W;

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

    wire [VEC_W-1:0] zero_node = vec4(
        rs(18'sd0, 18'sd0),
        rs(18'sd0, 18'sd0),
        rs(18'sd0, 18'sd0),
        rs(18'sd0, 18'sd0)
    );

    wire [VEC_W-1:0] node0_hydrated = vec4(
        rs(18'sd8, 18'sd0),
        rs(18'sd0, 18'sd0),
        rs(18'sd0, 18'sd0),
        rs(18'sd0, 18'sd0)
    );

    wire [VEC_W-1:0] node6_initial = vec4(
        rs(18'sd0, 18'sd0),
        rs(18'sd0, 18'sd0),
        rs(-18'sd2, 18'sd0),
        rs(18'sd1, 18'sd1)
    );

    wire [VEC_W-1:0] node6_hydrated = vec4(
        rs(18'sd0, 18'sd0),
        rs(18'sd0, 18'sd0),
        rs(-18'sd2, 18'sd0),
        rs(18'sd4, 18'sd1)
    );

    reg [7:0] rst_cnt = 8'd0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) begin
        if (!rst_n) rst_cnt <= rst_cnt + 1'b1;
    end

    reg  [2:0] rd_addr = 3'd0;
    wire [VEC_W-1:0] rd_data;
    reg        wr_en = 1'b0;
    reg  [2:0] wr_addr = 3'd0;
    reg  [3:0] wr_be = 4'b0000;
    reg  [VEC_W-1:0] wr_data = {VEC_W{1'b0}};

    spu_som_weight_bram #(.MAX_NODES(7), .WIDTH(WIDTH)) u_bram (
        .clk(sys_clk),
        .rd_addr(rd_addr),
        .rd_data(rd_data),
        .wr_en(wr_en),
        .wr_addr(wr_addr),
        .wr_be(wr_be),
        .wr_data(wr_data)
    );

    localparam [3:0] S_RESET        = 4'd0;
    localparam [3:0] S_READ0_WAIT   = 4'd1;
    localparam [3:0] S_READ0_CHECK  = 4'd2;
    localparam [3:0] S_WRITE0       = 4'd3;
    localparam [3:0] S_READ0H_WAIT  = 4'd4;
    localparam [3:0] S_READ0H_CHECK = 4'd5;
    localparam [3:0] S_WRITE6       = 4'd6;
    localparam [3:0] S_READ6_WAIT   = 4'd7;
    localparam [3:0] S_READ6_CHECK  = 4'd8;
    localparam [3:0] S_PASS         = 4'd9;
    localparam [3:0] S_FAIL         = 4'd10;

    reg [3:0] test_state = S_RESET;
    reg [1:0] tests_done = 2'd0;
    reg [3:0] best_digit = 4'd0;
    reg [7:0] fail_code = 8'd0;
    reg       all_pass = 1'b1;
    reg [3:0] wait_ctr = 4'd0;

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            test_state <= S_RESET;
            tests_done <= 2'd0;
            best_digit <= 4'd0;
            fail_code <= 8'd0;
            all_pass <= 1'b1;
            wait_ctr <= 4'd0;
            rd_addr <= 3'd0;
            wr_en <= 1'b0;
            wr_addr <= 3'd0;
            wr_be <= 4'b0000;
            wr_data <= {VEC_W{1'b0}};
        end else begin
            wr_en <= 1'b0;

            case (test_state)
                S_RESET: begin
                    rd_addr <= 3'd0;
                    wait_ctr <= 4'd0;
                    tests_done <= 2'd0;
                    best_digit <= 4'd0;
                    test_state <= S_READ0_WAIT;
                end

                S_READ0_WAIT: begin
                    if (wait_ctr == 4'd3)
                        test_state <= S_READ0_CHECK;
                    else
                        wait_ctr <= wait_ctr + 1'b1;
                end

                S_READ0_CHECK: begin
                    if (rd_data !== zero_node) begin
                        fail_code <= 8'hB0;
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else begin
                        tests_done <= 2'd1;
                        test_state <= S_WRITE0;
                    end
                end

                S_WRITE0: begin
                    wr_addr <= 3'd0;
                    wr_be <= 4'b0001;
                    wr_data <= node0_hydrated;
                    wr_en <= 1'b1;
                    rd_addr <= 3'd0;
                    wait_ctr <= 4'd0;
                    best_digit <= 4'd0;
                    test_state <= S_READ0H_WAIT;
                end

                S_READ0H_WAIT: begin
                    wr_be <= 4'b0000;
                    rd_addr <= 3'd0;
                    if (wait_ctr == 4'd5)
                        test_state <= S_READ0H_CHECK;
                    else
                        wait_ctr <= wait_ctr + 1'b1;
                end

                S_READ0H_CHECK: begin
                    if (rd_data !== node0_hydrated) begin
                        fail_code <= 8'hC0;
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else begin
                        tests_done <= 2'd2;
                        test_state <= S_WRITE6;
                    end
                end

                S_WRITE6: begin
                    wr_addr <= 3'd6;
                    wr_be <= 4'b1000;
                    wr_data <= node6_hydrated;
                    wr_en <= 1'b1;
                    rd_addr <= 3'd6;
                    wait_ctr <= 4'd0;
                    best_digit <= 4'd6;
                    test_state <= S_READ6_WAIT;
                end

                S_READ6_WAIT: begin
                    wr_be <= 4'b0000;
                    rd_addr <= 3'd6;
                    if (wait_ctr == 4'd5)
                        test_state <= S_READ6_CHECK;
                    else
                        wait_ctr <= wait_ctr + 1'b1;
                end

                S_READ6_CHECK: begin
                    if (rd_data !== node6_hydrated ||
                        rd_data[0*FEATURE_W +: FEATURE_W] !==
                            node6_initial[0*FEATURE_W +: FEATURE_W] ||
                        rd_data[1*FEATURE_W +: FEATURE_W] !==
                            node6_initial[1*FEATURE_W +: FEATURE_W] ||
                        rd_data[2*FEATURE_W +: FEATURE_W] !==
                            node6_initial[2*FEATURE_W +: FEATURE_W]) begin
                        fail_code <= 8'hD6;
                        all_pass <= 1'b0;
                        test_state <= S_FAIL;
                    end else begin
                        tests_done <= 2'd3;
                        fail_code <= 8'h00;
                        all_pass <= 1'b1;
                        test_state <= S_PASS;
                    end
                end

                S_PASS: begin
                    tests_done <= 2'd3;
                    best_digit <= 4'd6;
                end

                S_FAIL: begin
                    all_pass <= 1'b0;
                end

                default: begin
                    fail_code <= 8'hFF;
                    all_pass <= 1'b0;
                    test_state <= S_FAIL;
                end
            endcase
        end
    end

    reg [25:0] blink_cnt = 26'd0;
    always @(posedge sys_clk) blink_cnt <= blink_cnt + 1'b1;

    assign led[0] = ~blink_cnt[24];
    assign led[1] = ~(test_state == S_PASS);
    assign led[2] = ~(test_state == S_FAIL);

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
                5'd0:  msg_byte = "H";
                5'd1:  msg_byte = "Y";
                5'd2:  msg_byte = "D";
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
        if (!rst_n) begin
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
