// spu13_satellite_aggregator.v — 13-satellite whisper + bus aggregator
//
// Arlinghaus meso-tier governor component.  Instantiates up to 13
// independent whisper v1 listeners (one per satellite UART RX line)
// and aggregates their status into a flat register table.  The shared
// command bus interface allows the governor to address individual
// satellites for reconfiguration.
//
// Status table (per satellite, 13 entries), bit [15] down to [0]:
//   incoherent(1) som_valid(1) reserved(1) som_label[3:0] snap(1) dissonance[7:0]
//   = 16 bits per satellite, 208 bits total.
//
// Aggregate outputs:
//   - worst_axis: index of satellite with highest dissonance
//   - worst_dissonance: 8-bit value
//   - incoherent_count: how many satellites are in 3-miss deadman
//   - som_labels[51:0]: 13 × 4-bit SOM labels packed

module spu13_satellite_aggregator #(
    parameter NUM_SATELLITES = 13,
    parameter CLK_HZ         = 50000000,
    parameter BAUD           = 115200,
    parameter PERIOD_CYCLES  = 50000000 / 6000  // ~8333 at 50 MHz
) (
    input  wire         clk,
    input  wire         rst_n,

    // Whisper RX lines (one per satellite)
    input  wire [NUM_SATELLITES-1:0] whisper_rx,

    // Shared command bus (SPI-style, governor → satellite)
    output reg  [3:0]   bus_cs,        // chip-select (4 bits = up to 15 satellites)
    output reg          bus_sck,
    output reg          bus_mosi,
    input  wire         bus_miso,

    // Aggregated status table (combinational readout)
    output wire [NUM_SATELLITES*16-1:0] status_table,

    // Aggregate telemetry
    output reg  [3:0]   worst_axis,
    output reg  [7:0]   worst_dissonance,
    output reg  [3:0]   incoherent_count,
    output wire [51:0]  som_labels,     // 13 × 4 bits

    // Bus command interface (governor → aggregator)
    input  wire         cmd_valid,
    input  wire [3:0]   cmd_satellite,   // which satellite to address
    input  wire [7:0]   cmd_opcode,      // command to send
    output reg          cmd_done,
    output reg          cmd_error
);

    // ── Whisper listener instances ──────────────────────────────────
    genvar s;
    generate
        for (s = 0; s < NUM_SATELLITES; s = s + 1) begin : gen_listener
            wire [3:0]  rx_node_id;
            wire [2:0]  rx_flags;
            wire [7:0]  rx_dissonance;
            wire [7:0]  rx_status;
            wire        rx_valid;
            wire        rx_err;
            wire        rx_incoherent;

            spu_whisper_v1_listener #(
                .CLK_HZ(CLK_HZ), .BAUD(BAUD), .PERIOD_CYCLES(PERIOD_CYCLES)
            ) u_listener (
                .clk(clk), .rst_n(rst_n),
                .rx(whisper_rx[s]),
                .node_id(rx_node_id), .flags(rx_flags),
                .dissonance(rx_dissonance), .seq(rx_status),
                .frame_valid(rx_valid), .frame_err(rx_err),
                .incoherent(rx_incoherent)
            );

            // ── Status register per satellite ──────────────────────
            // Latched on frame_valid; incoherent is continuous.
            reg [15:0] sat_status;

            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    sat_status <= 16'd0;
                end else begin
                    if (rx_valid) begin
                        // [15]=incoherent [14]=som_valid [13]=reserved
                        // [12:9]=som_label [8]=snap [7:0]=dissonance
                        // Whisper `ss` is an application-status byte; the
                        // Arlinghaus profile assigns its low nibble to label.
                        sat_status <= {rx_incoherent,
                                       1'b1,           // frame_valid → som_valid
                                       1'b0,           // reserved
                                       rx_status[3:0],
                                       rx_flags[0],    // snap_locked
                                       rx_dissonance};
                    end else begin
                        // Incoherent is continuous — update even without new frame
                        sat_status[15] <= rx_incoherent;
                        if (rx_incoherent)
                            sat_status[14] <= 1'b0;  // som_valid cleared on incoherent
                    end
                end
            end

            assign status_table[(s+1)*16-1 -: 16] = sat_status;

            // SOM label extraction
            assign som_labels[(s+1)*4-1 -: 4] = sat_status[12:9];

        end
    endgenerate

    // ── Aggregate telemetry (combinational scan) ───────────────────
    integer ai;
    always @(*) begin
        worst_axis       = 4'd0;
        worst_dissonance = 8'd0;
        incoherent_count = 4'd0;

        for (ai = 0; ai < NUM_SATELLITES; ai = ai + 1) begin
            if (status_table[ai*16 + 15])  // incoherent bit
                incoherent_count = incoherent_count + 4'd1;

            if (status_table[ai*16 + 7 -: 8] > worst_dissonance) begin
                worst_dissonance = status_table[ai*16 + 7 -: 8];
                worst_axis = ai[3:0];
            end
        end
    end

    // ── Shared command bus FSM (simplified: single-byte command) ───
    localparam BUS_IDLE   = 2'd0;
    localparam BUS_SEND   = 2'd1;
    localparam BUS_WAIT   = 2'd2;

    reg [1:0] bus_state;
    reg [7:0] bus_byte;
    reg [3:0] bus_bit;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bus_state <= BUS_IDLE;
            bus_cs    <= 4'hF;     // all deselected (active-low CS would be high)
            bus_sck   <= 1'b0;
            bus_mosi  <= 1'b0;
            bus_byte  <= 8'd0;
            bus_bit   <= 4'd0;
            cmd_done  <= 1'b0;
            cmd_error <= 1'b0;
        end else begin
            cmd_done  <= 1'b0;
            cmd_error <= 1'b0;

            case (bus_state)
                BUS_IDLE: begin
                    if (cmd_valid) begin
                        bus_cs   <= cmd_satellite;  // select target satellite
                        bus_byte <= cmd_opcode;
                        bus_bit  <= 4'd7;
                        bus_state <= BUS_SEND;
                    end
                end

                BUS_SEND: begin
                    // Bit-bang one byte over shared bus
                    bus_mosi <= bus_byte[bus_bit];
                    bus_sck  <= 1'b1;
                    if (bus_bit > 0) begin
                        bus_bit <= bus_bit - 4'd1;
                    end else begin
                        bus_sck  <= 1'b0;
                        bus_state <= BUS_WAIT;
                    end
                end

                BUS_WAIT: begin
                    bus_sck <= 1'b0;
                    // Wait one cycle for satellite to respond, then deselect
                    bus_cs   <= 4'hF;
                    cmd_done <= 1'b1;
                    bus_state <= BUS_IDLE;
                end

                default: bus_state <= BUS_IDLE;
            endcase
        end
    end

endmodule
