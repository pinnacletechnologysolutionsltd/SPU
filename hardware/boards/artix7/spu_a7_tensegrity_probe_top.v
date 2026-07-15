// spu_a7_tensegrity_probe_top.v -- Artix-7 first-tranche tensegrity probe.
//
// A table-loader FSM presents all seven TGR1-derived fixtures to the
// admission guard through its configuration interface.  The wrapper checks
// every terminal state/fault pair and emits the UART verdict:
//
//   TGR:P V:7 E:00
//
// The exact type-uniform equilibrium engine derives the canonical force-
// density ratio and rejects the perturbed vector-6 fixture.

module spu_a7_tensegrity_probe_top #(
    parameter CLKS_PER_BIT = 434,
    parameter START_DELAY  = 25000000,
    parameter LINE_PERIOD  = 10000000
) (
    input  wire       sys_clk,
    input  wire       rst_n,
    output wire [2:0] led,
    output wire       uart_tx
);
    localparam [1:0] EDGE_CABLE = 2'd0;
    localparam [1:0] EDGE_STRUT = 2'd1;
    localparam [1:0] GRID_MAIN  = 2'd1;
    localparam [1:0] GRID_CONJ  = 2'd2;

    localparam [3:0] ST_BALANCED              = 4'd2;
    localparam [3:0] ST_FAULT_CABLE_SLACK     = 4'd4;
    localparam [3:0] ST_FAULT_STRUT_COLLISION = 4'd5;
    localparam [3:0] ST_FAULT_GRID_MISMATCH   = 4'd6;
    localparam [3:0] ST_FAULT_TOPOLOGY        = 4'd7;
    localparam [3:0] ST_FAULT_NOT_IN_EQUILIBRIUM = 4'd8;

    localparam [2:0] F_NONE            = 3'd0;
    localparam [2:0] F_CABLE_SLACK     = 3'd1;
    localparam [2:0] F_STRUT_COLLISION = 3'd2;
    localparam [2:0] F_GRID_MISMATCH   = 3'd3;
    localparam [2:0] F_TOPOLOGY        = 3'd4;
    localparam [2:0] F_NOT_IN_EQUILIBRIUM = 3'd5;

    localparam [3:0] L_RESET       = 4'd0;
    localparam [3:0] L_CLEAR_WAIT  = 4'd1;
    localparam [3:0] L_LOAD_NODE   = 4'd2;
    localparam [3:0] L_NODE_DRAIN  = 4'd3;
    localparam [3:0] L_LOAD_EDGE   = 4'd4;
    localparam [3:0] L_EDGE_DRAIN  = 4'd5;
    localparam [3:0] L_START       = 4'd6;
    localparam [3:0] L_WAIT        = 4'd7;
    localparam [3:0] L_CHECK       = 4'd8;
    localparam [3:0] L_PASS        = 4'd9;
    localparam [3:0] L_FAIL        = 4'd10;

    // Reset: synchronize the board button and guarantee a power-on reset even
    // when the external button is never pressed after configuration.
    reg [1:0] rst_sync = 2'b00;
    reg [7:0] rst_count = 8'd0;
    wire rst_n_int = (rst_count == 8'hff);

    always @(posedge sys_clk) begin
        rst_sync <= {rst_sync[0], rst_n};
        if (!rst_sync[1])
            rst_count <= 8'd0;
        else if (!rst_n_int)
            rst_count <= rst_count + 1'b1;
    end

    reg        guard_clear = 1'b0;
    reg        cfg_node_we = 1'b0;
    reg [3:0]  cfg_node_index = 4'd0;
    reg signed [31:0] cfg_x_a = 32'sd0;
    reg signed [31:0] cfg_x_b = 32'sd0;
    reg signed [31:0] cfg_y_a = 32'sd0;
    reg signed [31:0] cfg_y_b = 32'sd0;
    reg signed [31:0] cfg_z_a = 32'sd0;
    reg signed [31:0] cfg_z_b = 32'sd0;
    reg [1:0]  cfg_grid = 2'd0;
    reg        cfg_edge_we = 1'b0;
    reg [5:0]  cfg_edge_index = 6'd0;
    reg [3:0]  cfg_edge_a = 4'd0;
    reg [3:0]  cfg_edge_b = 4'd0;
    reg [1:0]  cfg_edge_type = 2'd0;
    reg        guard_start = 1'b0;
    wire       guard_done;
    wire [3:0] guard_state;
    wire [2:0] guard_fault;
    wire [4:0] guard_node_count;
    wire [5:0] guard_edge_count;
    wire [4:0] guard_intersection_attempts;

    // The exact-intersection datapath is deliberately advanced at 25 MHz.
    // This uses the repository's established fabric-divider + BUFG pattern:
    // the failed V:6 images proved that OpenXC7's sub-3-ns modeled margin on
    // distributed-table capture is not sufficient evidence on this unit.
    // UART remains on sys_clk, so its 115200-baud contract is unchanged.
    reg guard_clk_div = 1'b0;
    wire guard_clk;
    always @(posedge sys_clk) begin
        if (!rst_n_int)
            guard_clk_div <= 1'b0;
        else
            guard_clk_div <= ~guard_clk_div;
    end
`ifdef SYNTHESIS
    BUFG u_guard_clk_buf (.I(guard_clk_div), .O(guard_clk));
`else
    assign guard_clk = guard_clk_div;
`endif

    spu13_tensegrity_guard u_guard (
        .clk(guard_clk),
        .rst_n(rst_n_int),
        .clear(guard_clear),
        .cfg_node_we(cfg_node_we),
        .cfg_node_index(cfg_node_index),
        .cfg_x_a(cfg_x_a), .cfg_x_b(cfg_x_b),
        .cfg_y_a(cfg_y_a), .cfg_y_b(cfg_y_b),
        .cfg_z_a(cfg_z_a), .cfg_z_b(cfg_z_b),
        .cfg_grid(cfg_grid),
        .cfg_edge_we(cfg_edge_we),
        .cfg_edge_index(cfg_edge_index),
        .cfg_edge_a(cfg_edge_a),
        .cfg_edge_b(cfg_edge_b),
        .cfg_edge_type(cfg_edge_type),
        .start(guard_start),
        .done(guard_done),
        .state_code(guard_state),
        .fault_code(guard_fault),
        .node_count(guard_node_count),
        .edge_count(guard_edge_count),
        .intersection_attempts(guard_intersection_attempts)
    );

    // Canonical expanded-octahedron node table.  The current corpus has
    // integer Z[phi] coordinates, so every b coefficient is zero.
    function signed [31:0] canonical_x;
        input [3:0] index;
        begin
            case (index)
                4'd4, 4'd5:   canonical_x = 32'sd1;
                4'd6, 4'd7:   canonical_x = -32'sd1;
                4'd8, 4'd9:   canonical_x = 32'sd2;
                4'd10, 4'd11: canonical_x = -32'sd2;
                default:      canonical_x = 32'sd0;
            endcase
        end
    endfunction

    function signed [31:0] canonical_y;
        input [3:0] index;
        begin
            case (index)
                4'd0, 4'd1: canonical_y = 32'sd1;
                4'd2, 4'd3: canonical_y = -32'sd1;
                4'd4, 4'd6: canonical_y = 32'sd2;
                4'd5, 4'd7: canonical_y = -32'sd2;
                default:    canonical_y = 32'sd0;
            endcase
        end
    endfunction

    function signed [31:0] canonical_z;
        input [3:0] index;
        begin
            case (index)
                4'd0, 4'd2: canonical_z = 32'sd2;
                4'd1, 4'd3: canonical_z = -32'sd2;
                4'd8, 4'd10: canonical_z = 32'sd1;
                4'd9, 4'd11: canonical_z = -32'sd1;
                default:     canonical_z = 32'sd0;
            endcase
        end
    endfunction

    // Regular-icosahedron antipodal counterexample used by corpus vector 4.
    // Every one of its six struts crosses at the origin.
    function signed [31:0] antipodal_xa;
        input [3:0] index;
        begin
            case(index)
                4,5:antipodal_xa=1; 6,7:antipodal_xa=-1;
                default:antipodal_xa=0;
            endcase
        end
    endfunction
    function signed [31:0] antipodal_xb;
        input [3:0] index;
        begin
            case(index)
                8,9:antipodal_xb=1; 10,11:antipodal_xb=-1;
                default:antipodal_xb=0;
            endcase
        end
    endfunction
    function signed [31:0] antipodal_ya;
        input [3:0] index;
        begin
            case(index)
                0,1:antipodal_ya=1; 2,3:antipodal_ya=-1;
                default:antipodal_ya=0;
            endcase
        end
    endfunction
    function signed [31:0] antipodal_yb;
        input [3:0] index;
        begin
            case(index)
                4,6:antipodal_yb=1; 5,7:antipodal_yb=-1;
                default:antipodal_yb=0;
            endcase
        end
    endfunction
    function signed [31:0] antipodal_za;
        input [3:0] index;
        begin
            case(index)
                8,10:antipodal_za=1; 9,11:antipodal_za=-1;
                default:antipodal_za=0;
            endcase
        end
    endfunction
    function signed [31:0] antipodal_zb;
        input [3:0] index;
        begin
            case(index)
                0,2:antipodal_zb=1; 1,3:antipodal_zb=-1;
                default:antipodal_zb=0;
            endcase
        end
    endfunction

    function [3:0] canonical_edge_a;
        input [5:0] index;
        begin
            case (index)
                0,1,2,3: canonical_edge_a=0; 4,5,6,7: canonical_edge_a=1;
                8,9,10,11: canonical_edge_a=2; 12,13,14,15: canonical_edge_a=3;
                16,17: canonical_edge_a=4; 18,19: canonical_edge_a=5;
                20,21: canonical_edge_a=6; 22,23: canonical_edge_a=7;
                24: canonical_edge_a=0; 25: canonical_edge_a=2;
                26: canonical_edge_a=4; 27: canonical_edge_a=6;
                28: canonical_edge_a=8; default: canonical_edge_a=9;
            endcase
        end
    endfunction

    function [3:0] canonical_edge_b;
        input [5:0] index;
        begin
            case (index)
                0:canonical_edge_b=4; 1:canonical_edge_b=6;
                2:canonical_edge_b=8; 3:canonical_edge_b=10;
                4:canonical_edge_b=4; 5:canonical_edge_b=6;
                6:canonical_edge_b=9; 7:canonical_edge_b=11;
                8:canonical_edge_b=5; 9:canonical_edge_b=7;
                10:canonical_edge_b=8; 11:canonical_edge_b=10;
                12:canonical_edge_b=5; 13:canonical_edge_b=7;
                14:canonical_edge_b=9; 15:canonical_edge_b=11;
                16:canonical_edge_b=8; 17:canonical_edge_b=9;
                18:canonical_edge_b=8; 19:canonical_edge_b=9;
                20:canonical_edge_b=10; 21:canonical_edge_b=11;
                22:canonical_edge_b=10; 23:canonical_edge_b=11;
                24:canonical_edge_b=1; 25:canonical_edge_b=3;
                26:canonical_edge_b=5; 27:canonical_edge_b=7;
                28:canonical_edge_b=10; default:canonical_edge_b=11;
            endcase
        end
    endfunction

    // The topology fixture is two disconnected three-node components.
    function [3:0] topology_edge_a;
        input [5:0] index;
        begin
            case (index)
                0,1: topology_edge_a=0; 2: topology_edge_a=1;
                3,4: topology_edge_a=3; default: topology_edge_a=4;
            endcase
        end
    endfunction

    function [3:0] topology_edge_b;
        input [5:0] index;
        begin
            case (index)
                0:topology_edge_b=1; 1:topology_edge_b=2;
                2:topology_edge_b=2; 3:topology_edge_b=4;
                4:topology_edge_b=5; default:topology_edge_b=5;
            endcase
        end
    endfunction

    function [3:0] antipodal_edge_a;
        input [5:0] index;
        begin
            case(index)
                0,1,2,3,4:antipodal_edge_a=0; 5,6,7,8,9:antipodal_edge_a=1;
                10,11,12,13:antipodal_edge_a=2; 14,15,16,17:antipodal_edge_a=3;
                18,19,20:antipodal_edge_a=4; 21,22,23:antipodal_edge_a=5;
                24,25:antipodal_edge_a=6; 26,27:antipodal_edge_a=7;
                28:antipodal_edge_a=8; 29:antipodal_edge_a=10;
                30:antipodal_edge_a=0; 31:antipodal_edge_a=1;
                32:antipodal_edge_a=4; 33:antipodal_edge_a=5;
                34:antipodal_edge_a=8; default:antipodal_edge_a=9;
            endcase
        end
    endfunction

    function [3:0] antipodal_edge_b;
        input [5:0] index;
        begin
            case(index)
                0:antipodal_edge_b=2; 1:antipodal_edge_b=4; 2:antipodal_edge_b=6;
                3:antipodal_edge_b=8; 4:antipodal_edge_b=10; 5:antipodal_edge_b=3;
                6:antipodal_edge_b=4; 7:antipodal_edge_b=6; 8:antipodal_edge_b=9;
                9:antipodal_edge_b=11; 10:antipodal_edge_b=5; 11:antipodal_edge_b=7;
                12:antipodal_edge_b=8; 13:antipodal_edge_b=10; 14:antipodal_edge_b=5;
                15:antipodal_edge_b=7; 16:antipodal_edge_b=9; 17:antipodal_edge_b=11;
                18:antipodal_edge_b=6; 19:antipodal_edge_b=8; 20:antipodal_edge_b=9;
                21:antipodal_edge_b=7; 22:antipodal_edge_b=8; 23:antipodal_edge_b=9;
                24:antipodal_edge_b=10; 25:antipodal_edge_b=11; 26:antipodal_edge_b=10;
                27:antipodal_edge_b=11; 28:antipodal_edge_b=9; 29:antipodal_edge_b=11;
                30:antipodal_edge_b=3; 31:antipodal_edge_b=2; 32:antipodal_edge_b=7;
                33:antipodal_edge_b=6; 34:antipodal_edge_b=11; default:antipodal_edge_b=10;
            endcase
        end
    endfunction

    function [4:0] fixture_node_count;
        input [2:0] fixture;
        begin fixture_node_count = (fixture == 3'd1) ? 5'd6 : 5'd12; end
    endfunction

    function [5:0] fixture_edge_count;
        input [2:0] fixture;
        begin
            fixture_edge_count = (fixture == 3'd1) ? 6'd6 :
                                 (fixture == 3'd4) ? 6'd36 : 6'd30;
        end
    endfunction

    function [3:0] expected_state;
        input [2:0] fixture;
        begin
            case (fixture)
                3'd0: expected_state = ST_BALANCED;
                3'd1: expected_state = ST_FAULT_TOPOLOGY;
                3'd2: expected_state = ST_FAULT_STRUT_COLLISION;
                3'd3: expected_state = ST_FAULT_CABLE_SLACK;
                3'd4: expected_state = 4'd9;
                3'd5: expected_state = ST_FAULT_GRID_MISMATCH;
                default: expected_state = ST_FAULT_NOT_IN_EQUILIBRIUM;
            endcase
        end
    endfunction

    function [2:0] expected_fault;
        input [2:0] fixture;
        begin
            case (fixture)
                3'd0: expected_fault = F_NONE;
                3'd1: expected_fault = F_TOPOLOGY;
                3'd2: expected_fault = F_STRUT_COLLISION;
                3'd3: expected_fault = F_CABLE_SLACK;
                3'd4: expected_fault = 3'd6;
                3'd5: expected_fault = F_GRID_MISMATCH;
                default: expected_fault = F_NOT_IN_EQUILIBRIUM;
            endcase
        end
    endfunction

    reg [3:0] loader_state = L_RESET;
    reg [2:0] fixture_index = 3'd0;
    reg [3:0] node_index = 4'd0;
    reg [5:0] edge_index = 6'd0;
    reg [2:0] vectors_done = 3'd0;
    reg [7:0] fail_code = 8'd0;

    always @(posedge guard_clk) begin
        if (!rst_n_int) begin
            loader_state <= L_RESET;
            fixture_index <= 3'd0;
            node_index <= 4'd0;
            edge_index <= 6'd0;
            vectors_done <= 3'd0;
            fail_code <= 8'd0;
            guard_clear <= 1'b0;
            cfg_node_we <= 1'b0;
            cfg_edge_we <= 1'b0;
            guard_start <= 1'b0;
        end else begin
            guard_clear <= 1'b0;
            cfg_node_we <= 1'b0;
            cfg_edge_we <= 1'b0;
            guard_start <= 1'b0;

            case (loader_state)
                L_RESET: begin
                    guard_clear <= 1'b1;
                    node_index <= 4'd0;
                    edge_index <= 6'd0;
                    loader_state <= L_CLEAR_WAIT;
                end

                L_CLEAR_WAIT: begin
                    node_index <= 4'd0;
                    loader_state <= L_LOAD_NODE;
                end

                L_LOAD_NODE: begin
                    cfg_node_we <= 1'b1;
                    cfg_node_index <= node_index;
                    cfg_x_b <= (fixture_index == 3'd4) ? antipodal_xb(node_index) : 32'sd0;
                    cfg_y_b <= (fixture_index == 3'd4) ? antipodal_yb(node_index) : 32'sd0;
                    cfg_z_b <= (fixture_index == 3'd4) ? antipodal_zb(node_index) : 32'sd0;
                    cfg_grid <= (fixture_index == 3'd5 && node_index == 4'd0)
                              ? GRID_CONJ : GRID_MAIN;

                    if (fixture_index == 3'd1) begin
                        cfg_x_a <= 32'sd0;
                        cfg_y_a <= 32'sd0;
                        cfg_z_a <= 32'sd0;
                    end else if (fixture_index == 3'd4) begin
                        cfg_x_a <= antipodal_xa(node_index);
                        cfg_y_a <= antipodal_ya(node_index);
                        cfg_z_a <= antipodal_za(node_index);
                    end else if (fixture_index == 3'd6 && node_index == 4'd0) begin
                        cfg_x_a <= canonical_x(node_index) + 32'sd1;
                        cfg_y_a <= canonical_y(node_index);
                        cfg_z_a <= canonical_z(node_index);
                    end else if (fixture_index == 3'd3 && node_index == 4'd4) begin
                        cfg_x_a <= canonical_x(4'd0);
                        cfg_y_a <= canonical_y(4'd0);
                        cfg_z_a <= canonical_z(4'd0);
                    end else begin
                        cfg_x_a <= canonical_x(node_index);
                        cfg_y_a <= canonical_y(node_index);
                        cfg_z_a <= canonical_z(node_index);
                    end

                    if (node_index + 1'b1 >= fixture_node_count(fixture_index))
                        loader_state <= L_NODE_DRAIN;
                    else
                        node_index <= node_index + 1'b1;
                end

                L_NODE_DRAIN: begin
                    edge_index <= 6'd0;
                    loader_state <= L_LOAD_EDGE;
                end

                L_LOAD_EDGE: begin
                    cfg_edge_we <= 1'b1;
                    cfg_edge_index <= edge_index;
                    if (fixture_index == 3'd1) begin
                        cfg_edge_a <= topology_edge_a(edge_index);
                        cfg_edge_b <= topology_edge_b(edge_index);
                        cfg_edge_type <= EDGE_STRUT;
                    end else if (fixture_index == 3'd4) begin
                        cfg_edge_a <= antipodal_edge_a(edge_index);
                        cfg_edge_b <= antipodal_edge_b(edge_index);
                        cfg_edge_type <= (edge_index < 6'd30) ? EDGE_CABLE : EDGE_STRUT;
                    end else begin
                        cfg_edge_a <= (fixture_index == 3'd2 && edge_index == 6'd25)
                                    ? 4'd0 : canonical_edge_a(edge_index);
                        cfg_edge_b <= (fixture_index == 3'd2 && edge_index == 6'd25)
                                    ? 4'd9 : canonical_edge_b(edge_index);
                        cfg_edge_type <= (edge_index < 6'd24) ? EDGE_CABLE : EDGE_STRUT;
                    end

                    if (edge_index + 1'b1 >= fixture_edge_count(fixture_index))
                        loader_state <= L_EDGE_DRAIN;
                    else
                        edge_index <= edge_index + 1'b1;
                end

                L_EDGE_DRAIN: loader_state <= L_START;

                L_START: begin
                    guard_start <= 1'b1;
                    loader_state <= L_WAIT;
                end

                L_WAIT: begin
                    if (guard_done)
                        loader_state <= L_CHECK;
                end

                L_CHECK: begin
                    if (guard_node_count !== fixture_node_count(fixture_index) ||
                        guard_edge_count !== fixture_edge_count(fixture_index)) begin
                        fail_code <= 8'h40 + {5'd0, fixture_index};
                        loader_state <= L_FAIL;
                    end else if (guard_state !== expected_state(fixture_index) ||
                                 guard_fault !== expected_fault(fixture_index)) begin
                        // V already identifies the failing fixture. Report the
                        // actual state/fault pair as 1SSSSFFF so a board-only
                        // divergence is diagnosable without a second image.
                        fail_code <= {1'b1, guard_state, guard_fault};
                        loader_state <= L_FAIL;
                    end else if (fixture_index == 3'd6) begin
                        vectors_done <= 3'd7;
                        loader_state <= L_PASS;
                    end else begin
                        vectors_done <= fixture_index + 1'b1;
                        fixture_index <= fixture_index + 1'b1;
                        loader_state <= L_RESET;
                    end
                end

                L_PASS: vectors_done <= 3'd7;
                L_FAIL: loader_state <= L_FAIL;

                default: begin
                    fail_code <= 8'hff;
                    loader_state <= L_FAIL;
                end
            endcase
        end
    end

    // LEDs are diagnostic outputs only on this board and are not acceptance
    // evidence.  This Wukong unit's LED pins have a known electrical anomaly;
    // keep them quiescent and take the verdict exclusively from UART E3.
    assign led = 3'b000;

    // Repeating 115200-baud UART status.  Transmission is gated until the
    // self-check reaches a terminal state, so no provisional verdict can be
    // mistaken for the silicon result.
    reg [9:0]  tx_shift = 10'h3ff;
    reg [3:0]  tx_bits = 4'd0;
    reg [15:0] baud_count = 16'd0;
    reg [31:0] start_count = 32'd0;
    reg [31:0] line_count = 32'd0;
    reg [4:0]  msg_index = 5'd0;
    reg        start_ready = 1'b0;
    reg        line_active = 1'b0;

    wire terminal = (loader_state == L_PASS || loader_state == L_FAIL);
    assign uart_tx = tx_shift[0];

    function [7:0] hex_ascii;
        input [3:0] value;
        begin hex_ascii = (value < 10) ? ("0" + value) : ("A" + value - 10); end
    endfunction

    function [7:0] message_byte;
        input [4:0] index;
        begin
            case (index)
                0: message_byte="T"; 1: message_byte="G"; 2: message_byte="R";
                3: message_byte=":";
                4: message_byte=(loader_state == L_PASS) ? "P" : "F";
                5: message_byte=" "; 6: message_byte="V"; 7: message_byte=":";
                8: message_byte="0" + vectors_done;
                9: message_byte=" "; 10:message_byte="E"; 11:message_byte=":";
                12:message_byte=hex_ascii(fail_code[7:4]);
                13:message_byte=hex_ascii(fail_code[3:0]);
                14:message_byte=(loader_state == L_PASS) ? 8'h0d : " ";
                15:message_byte=(loader_state == L_PASS) ? 8'h0a : "A";
                16:message_byte=":";
                17:message_byte=hex_ascii({3'b000,guard_intersection_attempts[4]});
                18:message_byte=hex_ascii(guard_intersection_attempts[3:0]);
                19:message_byte=8'h0d; default:message_byte=8'h0a;
            endcase
        end
    endfunction

    always @(posedge sys_clk) begin
        if (!rst_n_int) begin
            tx_shift <= 10'h3ff;
            tx_bits <= 4'd0;
            baud_count <= 16'd0;
            start_count <= 32'd0;
            line_count <= 32'd0;
            msg_index <= 5'd0;
            start_ready <= 1'b0;
            line_active <= 1'b0;
        end else if (!start_ready) begin
            if (start_count + 1'b1 >= START_DELAY)
                start_ready <= 1'b1;
            else
                start_count <= start_count + 1'b1;
        end else if (tx_bits != 0) begin
            if (baud_count + 1'b1 >= CLKS_PER_BIT) begin
                baud_count <= 16'd0;
                tx_shift <= {1'b1, tx_shift[9:1]};
                tx_bits <= tx_bits - 1'b1;
            end else
                baud_count <= baud_count + 1'b1;
        end else if (line_active) begin
            tx_shift <= {1'b1, message_byte(msg_index), 1'b0};
            tx_bits <= 4'd10;
            baud_count <= 16'd0;
            if ((loader_state == L_PASS && msg_index == 5'd15) ||
                (loader_state == L_FAIL && msg_index == 5'd20)) begin
                msg_index <= 5'd0;
                line_active <= 1'b0;
            end else
                msg_index <= msg_index + 1'b1;
        end else if (terminal) begin
            if (line_count + 1'b1 >= LINE_PERIOD) begin
                line_count <= 32'd0;
                msg_index <= 5'd0;
                line_active <= 1'b1;
            end else
                line_count <= line_count + 1'b1;
        end
    end

endmodule
