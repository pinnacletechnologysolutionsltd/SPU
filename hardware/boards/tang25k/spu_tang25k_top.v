// Tang-25k board top for SPU-4 smoketest
// Minimal wrapper: includes Sierpinski clock, SPU-4 core (RPLU disabled),
// an inert Davis gate instantiation (monitor-only) and a simple smoke driver
// that toggles an LED and emits a single UART byte on power-up (sim-only)

`timescale 1ns/1ps

module spu_tang25k_top (
    input  wire clk_in,
    input  wire rst_n,
    output wire led_out,
    output wire uart_tx,
    output wire smoke_ok
);

    // Fractal / Fibonacci timing source (kept in wrapper as requested)
    wire phi_8, phi_13, phi_21, heartbeat;
    spu_sierpinski_clk u_sclk (
        .clk(clk_in),
        .rst_n(rst_n),
        .phi_8(phi_8),
        .phi_13(phi_13),
        .phi_21(phi_21),
        .heartbeat(heartbeat)
    );

    // SPU-4 core: keep RPLU BRAM disabled for smoke test
    wire         snap_alert;
    wire         whisper_tx;
    wire [63:0]  debug_reg_r0;
    wire [9:0]   pc;

    spu4_top #(.ENABLE_RPLU_BRAM(0)) u_spu4 (
        .clk(clk_in),
        .rst_n(rst_n),
        .rplu_cfg_wr_en(1'b0),
        .rplu_cfg_sel(3'd0),
        .rplu_cfg_material(1'b0),
        .rplu_cfg_addr(10'd0),
        .rplu_cfg_data(64'd0),
        .inst_data(24'd0),
        .pc(pc),
        .snap_alert(snap_alert),
        .whisper_tx(whisper_tx),
        .debug_reg_r0(debug_reg_r0)
    );

    // Davis gate (monitor-only): instantiate with zero input and do not
    // wire its outputs into any reset/henosis logic. This keeps it observable
    // but non-intrusive for early bring-up.
    wire [63:0] q_rotated;
    wire [31:0] quadrance;
    wire [31:0] ivm_quadrance;
    wire [15:0] gasket_sum;
    wire signed [31:0] audio_p, audio_q;

    davis_gate_dsp #(.DEVICE("SIM")) u_davis (
        .clk(clk_in),
        .rst_n(rst_n),
        .q_vector(64'd0),
        .q_rotated(q_rotated),
        .quadrance(quadrance),
        .ivm_quadrance(ivm_quadrance),
        .gasket_sum(gasket_sum),
        .audio_p(audio_p),
        .audio_q(audio_q)
    );

    // Simple smoke driver: toggles LED and sends a single UART-like byte
    // on first power-up. This is used to confirm FPGA programming / power.
    board_smoke u_smoke (
        .clk(clk_in),
        .rst_n(rst_n),
        .led(led_out),
        .uart_tx(uart_tx),
        .smoke_ok(smoke_ok)
    );

endmodule


// Very small simulation-friendly smoke generator. Keeps logic minimal so
// synthesis can either ignore or replace with a board-level heartbeat later.
module board_smoke (
    input  wire clk,
    input  wire rst_n,
    output reg  led,
    output reg  uart_tx,
    output reg  smoke_ok
);
    reg [31:0] cnt;
    reg        started;

    // Simple coarse UART state for simulation-only confirmation (1 byte)
    reg [7:0]  tx_byte;
    reg [3:0]  tx_bit;
    reg [15:0] tx_div;
    reg        tx_busy;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt      <= 32'd0;
            started  <= 1'b0;
            led      <= 1'b0;
            uart_tx  <= 1'b1; // idle high
            smoke_ok <= 1'b0;
            tx_byte  <= 8'd0;
            tx_bit   <= 4'd0;
            tx_div   <= 16'd0;
            tx_busy  <= 1'b0;
        end else begin
            cnt <= cnt + 1;
            // slow heartbeat -> led toggles on a high bit
            led <= cnt[23];

            if (!started && cnt == 32'd1000) begin
                started <= 1'b1;
                // Simulation console confirmation
                $display("SMOKE: POWER-ON OK at time=%0t", $time);
                // Prepare to send 'O' (0x4F) as a single proof-of-life byte
                tx_byte <= 8'h4F;
                tx_busy <= 1'b1;
                tx_bit  <= 4'd0;
                tx_div  <= 16'd0;
            end

            if (tx_busy) begin
                tx_div <= tx_div + 1;
                // coarse divider — tuned for simulation speed, not real baud
                if (tx_div == 16'd100) begin
                    tx_div <= 16'd0;
                    if (tx_bit == 0) begin
                        uart_tx <= 1'b0; // start bit
                        tx_bit <= tx_bit + 1;
                    end else if (tx_bit >= 1 && tx_bit <= 8) begin
                        uart_tx <= tx_byte[tx_bit-1];
                        tx_bit <= tx_bit + 1;
                    end else if (tx_bit == 9) begin
                        uart_tx <= 1'b1; // stop bit
                        tx_bit <= 4'd0;
                        tx_busy <= 1'b0;
                        smoke_ok <= 1'b1; // signal testbench
                        $display("SMOKE: UART SENT 'O' at time=%0t", $time);
                    end
                end
            end
        end
    end

endmodule
