// SPDX-License-Identifier: CERN-OHL-W-2.0
// Transactional TGR1 table store, parser, and bounded admission sidecar.
//
// The inactive half of a double-buffered byte RAM receives one complete TGR1
// record.  Transport commit alone is insufficient: magic/version/flags,
// declared size, bounds, payload CRC-32, node padding/grid tags, and edge
// fields are validated before the table is replayed into the admission guard.
// The active bank and its last mechanical verdict change only after a valid
// table reaches a terminal guard result; malformed or aborted writes roll back.

module spu13_tensegrity_sidecar #(
    parameter MAX_NODES = 12,
    parameter MAX_EDGES = 40,
    parameter MAX_BYTES = 508,
    parameter PARSE_WATCHDOG_LIMIT = 4096,
    parameter VERIFY_WATCHDOG_LIMIT = 1000000,
    parameter USE_ZPHI_KARATSUBA = 1
) (
    input  wire         clk,
    input  wire         rst_n,

    input  wire         stream_start,
    input  wire [15:0]  stream_length,
    input  wire [31:0]  stream_vector_id,
    input  wire         stream_valid,
    input  wire [7:0]   stream_data,
    input  wire         stream_commit,
    input  wire         stream_abort,
    input  wire         status_hold,

    output wire [127:0] transport_status,
    output wire         active_valid,
    output wire         busy,
    output wire [7:0]   loader_error
);
    localparam [7:0]
        ERR_NONE       = 8'd0,
        ERR_TRANSPORT  = 8'd1,
        ERR_MAGIC      = 8'd2,
        ERR_VERSION    = 8'd3,
        ERR_FLAGS      = 8'd4,
        ERR_BOUNDS     = 8'd5,
        ERR_LENGTH     = 8'd6,
        ERR_CRC32      = 8'd7,
        ERR_NODE       = 8'd8,
        ERR_EDGE       = 8'd9,
        ERR_GUARD_TIMEOUT = 8'd10,
        ERR_PARSE_TIMEOUT = 8'd11;

    localparam integer TOTAL_BYTES = 2 * MAX_BYTES;
    localparam integer ADDR_W = $clog2(TOTAL_BYTES);

    (* ram_style = "block" *) reg [7:0] table_mem [0:TOTAL_BYTES-1];
    reg [ADDR_W-1:0] read_addr;
    reg [7:0] mem_q;

    reg active_bank;
    reg staging_bank;
    reg active_valid_reg;
    reg rx_busy;
    reg verify_busy;
    reg [7:0] error_code;
    reg overflow_seen;
    reg [15:0] write_count;
    reg [15:0] received_count;
    reg [15:0] last_received;
    reg [15:0] last_expected;
    reg [15:0] declared_length;
    reg [31:0] staging_vector_id;

    reg [31:0] magic_shift;
    reg [7:0] header_version;
    reg [7:0] header_nodes;
    reg [7:0] header_edges;
    reg [7:0] header_flags;
    reg [31:0] header_crc;
    reg [31:0] payload_crc;

    reg [3:0] active_state;
    reg [2:0] active_fault;
    reg [31:0] active_vector_id;
    reg [7:0] active_nodes;
    reg [7:0] active_edges;

    wire [15:0] header_nodes_w = {8'd0, header_nodes};
    wire [15:0] header_edges_w = {8'd0, header_edges};
    wire [15:0] node_payload_bytes = (header_nodes_w << 5) -
                                     (header_nodes_w << 2);
    wire [15:0] edge_payload_bytes = header_edges_w << 2;
    wire [15:0] header_length = 16'd12 + node_payload_bytes +
                                edge_payload_bytes;

    function [31:0] crc32_byte;
        input [31:0] crc;
        input [7:0] byte_data;
        reg [31:0] s;
        integer bit_index;
        begin
            s = crc ^ byte_data;
            for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1)
                s = s[0] ? ((s >> 1) ^ 32'hEDB88320) : (s >> 1);
            crc32_byte = s;
        end
    endfunction

    // Guard configuration replay interface.
    reg guard_clear;
    reg cfg_node_we;
    reg [3:0] cfg_node_index;
    reg signed [31:0] cfg_x_a, cfg_x_b, cfg_y_a, cfg_y_b, cfg_z_a, cfg_z_b;
    reg [1:0] cfg_grid;
    reg cfg_edge_we;
    reg [5:0] cfg_edge_index;
    reg [3:0] cfg_edge_a, cfg_edge_b;
    reg [1:0] cfg_edge_type;
    reg guard_start;
    wire guard_done;
    wire [3:0] guard_state;
    wire [2:0] guard_fault;
    wire [4:0] guard_node_count;
    wire [5:0] guard_edge_count;
    wire [4:0] guard_intersection_attempts;
    wire [7:0] guard_service_stage;

    spu13_tensegrity_guard #(
        .MAX_NODES(MAX_NODES),
        .MAX_EDGES(MAX_EDGES),
        .USE_ZPHI_KARATSUBA(USE_ZPHI_KARATSUBA)
    ) u_guard (
        .clk(clk), .rst_n(rst_n), .clear(guard_clear),
        .cfg_node_we(cfg_node_we), .cfg_node_index(cfg_node_index),
        .cfg_x_a(cfg_x_a), .cfg_x_b(cfg_x_b),
        .cfg_y_a(cfg_y_a), .cfg_y_b(cfg_y_b),
        .cfg_z_a(cfg_z_a), .cfg_z_b(cfg_z_b), .cfg_grid(cfg_grid),
        .cfg_edge_we(cfg_edge_we), .cfg_edge_index(cfg_edge_index),
        .cfg_edge_a(cfg_edge_a), .cfg_edge_b(cfg_edge_b),
        .cfg_edge_type(cfg_edge_type), .start(guard_start),
        .done(guard_done), .state_code(guard_state), .fault_code(guard_fault),
        .node_count(guard_node_count), .edge_count(guard_edge_count),
        .intersection_attempts(guard_intersection_attempts),
        .service_stage(guard_service_stage)
    );

    localparam [3:0]
        P_IDLE        = 4'd0,
        P_CLEAR       = 4'd1,
        P_NODE_REQ    = 4'd2,
        P_NODE_WAIT   = 4'd3,
        P_NODE_GET    = 4'd4,
        P_NODE_WRITE  = 4'd5,
        P_EDGE_REQ    = 4'd6,
        P_EDGE_WAIT   = 4'd7,
        P_EDGE_GET    = 4'd8,
        P_EDGE_WRITE  = 4'd9,
        P_GUARD_START = 4'd10,
        P_GUARD_WAIT  = 4'd11;

    reg [3:0] parse_state;
    reg [7:0] parse_index;
    reg [5:0] record_byte;
    reg [223:0] record_shift;
    reg [223:0] node_record;
    reg [31:0] edge_record;
    reg [15:0] record_base;
    reg guard_result_pending;
    reg [3:0] pending_guard_state;
    reg [2:0] pending_guard_fault;
    reg [15:0] parse_watchdog;
    reg [23:0] verify_watchdog;
    reg [7:0] verify_stage;

    wire [ADDR_W-1:0] staging_base = staging_bank ? MAX_BYTES : 0;
    wire [ADDR_W-1:0] write_address = staging_base + write_count[ADDR_W-1:0];
    wire [7:0] status_flags = {4'b0000, active_valid_reg, verify_busy,
                               rx_busy, (error_code != ERR_NONE)};

    assign active_valid = active_valid_reg;
    assign busy = rx_busy || verify_busy;
    assign loader_error = error_code;
    assign transport_status = {
        8'd1, {4'd0, active_state}, {5'd0, active_fault}, verify_stage,
        active_vector_id,
        status_flags, error_code,
        active_nodes, active_edges,
        last_received, last_expected
    };

    always @(posedge clk) begin
        mem_q <= table_mem[read_addr];

        if (!rst_n) begin
            active_bank <= 1'b0;
            staging_bank <= 1'b1;
            active_valid_reg <= 1'b0;
            rx_busy <= 1'b0;
            verify_busy <= 1'b0;
            error_code <= ERR_NONE;
            overflow_seen <= 1'b0;
            write_count <= 16'd0;
            received_count <= 16'd0;
            last_received <= 16'd0;
            last_expected <= 16'd0;
            declared_length <= 16'd0;
            staging_vector_id <= 32'd0;
            magic_shift <= 32'd0;
            header_version <= 8'd0;
            header_nodes <= 8'd0;
            header_edges <= 8'd0;
            header_flags <= 8'd0;
            header_crc <= 32'd0;
            payload_crc <= 32'hFFFFFFFF;
            active_state <= 4'd0;
            active_fault <= 3'd0;
            active_vector_id <= 32'd0;
            active_nodes <= 8'd0;
            active_edges <= 8'd0;
            read_addr <= {ADDR_W{1'b0}};
            guard_clear <= 1'b0;
            cfg_node_we <= 1'b0;
            cfg_node_index <= 4'd0;
            cfg_x_a <= 0; cfg_x_b <= 0; cfg_y_a <= 0; cfg_y_b <= 0;
            cfg_z_a <= 0; cfg_z_b <= 0; cfg_grid <= 0;
            cfg_edge_we <= 1'b0;
            cfg_edge_index <= 6'd0;
            cfg_edge_a <= 4'd0; cfg_edge_b <= 4'd0; cfg_edge_type <= 2'd0;
            guard_start <= 1'b0;
            parse_state <= P_IDLE;
            parse_index <= 8'd0;
            record_byte <= 6'd0;
            record_shift <= 224'd0;
            node_record <= 224'd0;
            edge_record <= 32'd0;
            record_base <= 16'd0;
            guard_result_pending <= 1'b0;
            pending_guard_state <= 4'd0;
            pending_guard_fault <= 3'd0;
            parse_watchdog <= 16'd0;
            verify_watchdog <= 24'd0;
            verify_stage <= 8'd0;
        end else begin
            guard_clear <= 1'b0;
            cfg_node_we <= 1'b0;
            cfg_edge_we <= 1'b0;
            guard_start <= 1'b0;

            // B3 holds the status-producing state machine while its sixteen
            // bytes are shifted out.  The guard itself may finish during the
            // hold, so remember its one-cycle done pulse and commit it after
            // CS deasserts.
            if (status_hold && guard_done) begin
                guard_result_pending <= 1'b1;
                pending_guard_state <= guard_state;
                pending_guard_fault <= guard_fault;
            end

            if (stream_start && !rx_busy && !verify_busy) begin
                staging_bank <= ~active_bank;
                declared_length <= stream_length;
                staging_vector_id <= stream_vector_id;
                write_count <= 16'd0;
                received_count <= 16'd0;
                magic_shift <= 32'd0;
                header_version <= 8'd0;
                header_nodes <= 8'd0;
                header_edges <= 8'd0;
                header_flags <= 8'd0;
                header_crc <= 32'd0;
                payload_crc <= 32'hFFFFFFFF;
                guard_result_pending <= 1'b0;
                parse_watchdog <= 16'd0;
                verify_watchdog <= 24'd0;
                verify_stage <= 8'd0;
                overflow_seen <= (stream_length > MAX_BYTES);
                error_code <= ERR_NONE;
                rx_busy <= 1'b1;
            end else if (stream_start) begin
                error_code <= ERR_TRANSPORT;
            end

            if (stream_valid && rx_busy) begin
                received_count <= received_count + 1'b1;
                if (write_count < MAX_BYTES) begin
                    table_mem[write_address] <= stream_data;
                    write_count <= write_count + 1'b1;
                end else begin
                    overflow_seen <= 1'b1;
                end
                case (received_count)
                    16'd0, 16'd1, 16'd2, 16'd3:
                        magic_shift <= {magic_shift[23:0], stream_data};
                    16'd4: header_version <= stream_data;
                    16'd5: header_nodes <= stream_data;
                    16'd6: header_edges <= stream_data;
                    16'd7: header_flags <= stream_data;
                    16'd8, 16'd9, 16'd10, 16'd11:
                        header_crc <= {header_crc[23:0], stream_data};
                    default: payload_crc <= crc32_byte(payload_crc, stream_data);
                endcase
            end

            if (stream_abort && rx_busy) begin
                rx_busy <= 1'b0;
                error_code <= ERR_TRANSPORT;
                last_received <= received_count;
                last_expected <= declared_length;
            end

            if (stream_commit && rx_busy) begin
                rx_busy <= 1'b0;
                last_received <= received_count;
                last_expected <= header_length;
                if (overflow_seen || header_nodes > MAX_NODES ||
                    header_edges > MAX_EDGES) begin
                    error_code <= ERR_BOUNDS;
                end else if (magic_shift != 32'h54475231) begin
                    error_code <= ERR_MAGIC;
                end else if (header_version != 8'd1) begin
                    error_code <= ERR_VERSION;
                end else if (header_flags != 8'd0) begin
                    error_code <= ERR_FLAGS;
                end else if (received_count != declared_length ||
                             declared_length != header_length) begin
                    error_code <= ERR_LENGTH;
                end else if ((~payload_crc) != header_crc) begin
                    error_code <= ERR_CRC32;
                end else begin
                    error_code <= ERR_NONE;
                    verify_busy <= 1'b1;
                    parse_state <= P_CLEAR;
                    verify_stage <= 8'h11;
                    parse_watchdog <= 16'd0;
                    verify_watchdog <= 24'd0;
                    parse_index <= 8'd0;
                    record_byte <= 6'd0;
                    record_shift <= 224'd0;
                    record_base <= 16'd12;
                end
            end

            if (!status_hold) begin
            if (parse_state != P_IDLE && parse_state != P_GUARD_WAIT &&
                parse_watchdog + 1'b1 >= PARSE_WATCHDOG_LIMIT) begin
                // Parsing is part of the admission transaction and must be
                // bounded just like the exact mechanical services. Preserve
                // the active bank/verdict and expose the exact parser substate.
                verify_busy <= 1'b0;
                error_code <= ERR_PARSE_TIMEOUT;
                guard_result_pending <= 1'b0;
                guard_clear <= 1'b1;
                parse_watchdog <= 16'd0;
                verify_watchdog <= 24'd0;
                verify_stage <= 8'h90 | {4'd0, parse_state};
                parse_state <= P_IDLE;
            end else begin
            if (parse_state != P_IDLE && parse_state != P_GUARD_WAIT) begin
                parse_watchdog <= parse_watchdog + 1'b1;
                verify_stage <= 8'h10 | {4'd0, parse_state};
            end else if (parse_state == P_IDLE) begin
                parse_watchdog <= 16'd0;
            end
            case (parse_state)
                P_IDLE: begin end

                P_CLEAR: begin
                    guard_clear <= 1'b1;
                    if (header_nodes == 0) begin
                        record_base <= 16'd12;
                        parse_index <= 8'd0;
                        parse_state <= (header_edges == 0) ? P_GUARD_START : P_EDGE_REQ;
                    end else begin
                        parse_state <= P_NODE_REQ;
                    end
                end

                P_NODE_REQ: begin
                    read_addr <= staging_base + record_base + record_byte;
                    parse_state <= P_NODE_WAIT;
                end

                P_NODE_WAIT: parse_state <= P_NODE_GET;

                P_NODE_GET: begin
                    record_shift <= {record_shift[215:0], mem_q};
                    if (record_byte == 6'd27) begin
                        node_record <= {record_shift[215:0], mem_q};
                        parse_state <= P_NODE_WRITE;
                    end else begin
                        record_byte <= record_byte + 1'b1;
                        parse_state <= P_NODE_REQ;
                    end
                end

                P_NODE_WRITE: begin
                    if (node_record[31:24] > 8'd2 || node_record[23:0] != 0) begin
                        error_code <= ERR_NODE;
                        verify_busy <= 1'b0;
                        parse_watchdog <= 16'd0;
                        parse_state <= P_IDLE;
                    end else begin
                        cfg_node_index <= parse_index[3:0];
                        cfg_x_a <= node_record[223:192];
                        cfg_x_b <= node_record[191:160];
                        cfg_y_a <= node_record[159:128];
                        cfg_y_b <= node_record[127:96];
                        cfg_z_a <= node_record[95:64];
                        cfg_z_b <= node_record[63:32];
                        cfg_grid <= node_record[25:24];
                        cfg_node_we <= 1'b1;
                        record_shift <= 224'd0;
                        record_byte <= 6'd0;
                        if (parse_index + 1'b1 >= header_nodes) begin
                            parse_index <= 8'd0;
                            record_base <= 16'd12 + node_payload_bytes;
                            parse_state <= (header_edges == 0) ? P_GUARD_START : P_EDGE_REQ;
                        end else begin
                            parse_index <= parse_index + 1'b1;
                            record_base <= record_base + 16'd28;
                            parse_state <= P_NODE_REQ;
                        end
                    end
                end

                P_EDGE_REQ: begin
                    read_addr <= staging_base + record_base + record_byte;
                    parse_state <= P_EDGE_WAIT;
                end

                P_EDGE_WAIT: parse_state <= P_EDGE_GET;

                P_EDGE_GET: begin
                    record_shift <= {record_shift[215:0], mem_q};
                    if (record_byte == 6'd3) begin
                        edge_record <= {record_shift[23:0], mem_q};
                        parse_state <= P_EDGE_WRITE;
                    end else begin
                        record_byte <= record_byte + 1'b1;
                        parse_state <= P_EDGE_REQ;
                    end
                end

                P_EDGE_WRITE: begin
                    if (edge_record[7:0] != 0 || edge_record[15:8] > 8'd2 ||
                        edge_record[31:24] >= header_nodes ||
                        edge_record[23:16] >= header_nodes) begin
                        error_code <= ERR_EDGE;
                        verify_busy <= 1'b0;
                        parse_watchdog <= 16'd0;
                        parse_state <= P_IDLE;
                    end else begin
                        cfg_edge_index <= parse_index[5:0];
                        cfg_edge_a <= edge_record[27:24];
                        cfg_edge_b <= edge_record[19:16];
                        cfg_edge_type <= edge_record[9:8];
                        cfg_edge_we <= 1'b1;
                        record_shift <= 224'd0;
                        record_byte <= 6'd0;
                        if (parse_index + 1'b1 >= header_edges) begin
                            parse_state <= P_GUARD_START;
                        end else begin
                            parse_index <= parse_index + 1'b1;
                            record_base <= record_base + 16'd4;
                            parse_state <= P_EDGE_REQ;
                        end
                    end
                end

                P_GUARD_START: begin
                    guard_start <= 1'b1;
                    verify_stage <= 8'd2;
                    parse_watchdog <= 16'd0;
                    verify_watchdog <= 24'd0;
                    parse_state <= P_GUARD_WAIT;
                end

                P_GUARD_WAIT: begin
                    verify_stage <= guard_service_stage;
                    if (guard_done || guard_result_pending) begin
                        active_bank <= staging_bank;
                        active_valid_reg <= 1'b1;
                        active_state <= guard_result_pending ?
                                        pending_guard_state : guard_state;
                        active_fault <= guard_result_pending ?
                                        pending_guard_fault : guard_fault;
                        active_vector_id <= staging_vector_id;
                        active_nodes <= header_nodes;
                        active_edges <= header_edges;
                        verify_busy <= 1'b0;
                        error_code <= ERR_NONE;
                        guard_result_pending <= 1'b0;
                        verify_watchdog <= 24'd0;
                        verify_stage <= 8'd8;
                        parse_state <= P_IDLE;
                    end else if (verify_watchdog + 1'b1 >= VERIFY_WATCHDOG_LIMIT) begin
                        // A mechanically unresponsive service must never make
                        // the transactional loader permanently busy.  Preserve
                        // the active bank/verdict and expose the exact service
                        // that timed out with bit 7 set.
                        verify_busy <= 1'b0;
                        error_code <= ERR_GUARD_TIMEOUT;
                        guard_result_pending <= 1'b0;
                        guard_clear <= 1'b1;
                        verify_watchdog <= 24'd0;
                        verify_stage <= 8'h80 | guard_service_stage;
                        parse_state <= P_IDLE;
                    end else begin
                        verify_watchdog <= verify_watchdog + 1'b1;
                    end
                end

                default: parse_state <= P_IDLE;
            endcase
            end
            end
        end
    end
endmodule
