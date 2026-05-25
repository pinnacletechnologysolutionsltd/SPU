// spu13_tang25k_top.v (v1.9.7 - Toggling Handshake Final)
module spu13_tang25k_top #(
    parameter ENABLE_SDRAM = 0,
    parameter ENABLE_CORE_RPLU = 0,
    parameter ENABLE_CORE_LATTICE = 0,
    parameter ENABLE_CORE_MATH = 1
) (
    input  wire periph_rx, sys_clk, input wire uart_rx_telemetry,
    output wire [2:0] led, output wire uart_tx, uart_tx_telemetry,
    output wire sdram_clk, sdram_cs_n, sdram_ras_n, sdram_cas_n, sdram_we_n,
    output wire [1:0] sdram_ba, output wire sdram_a0, sdram_a1, sdram_a2, sdram_a3, sdram_a4, sdram_a5, sdram_a6, sdram_a7, sdram_a8, sdram_a9, sdram_a10, sdram_a11, sdram_a12,
    inout  wire [15:0] sdram_dq, output wire [1:0] sdram_dm
);
    // 1. Clocks
    wire clk_50m; BUFG u_b50(.I(sys_clk), .O(clk_50m));
    reg [5:0] cdiv; always @(posedge clk_50m) cdiv <= cdiv + 1;
    wire clk_core; BUFG u_bc(.I(cdiv[2]), .O(clk_core));
    reg [7:0] rcnt; wire rst_n = (rcnt == 8'hFF);
    always @(posedge clk_core) if (rcnt != 8'hFF) rcnt <= rcnt + 1;

    // 2. Timing
    reg [24:0] hbeat; reg p_last; always @(posedge clk_core) begin hbeat <= hbeat + 1; p_last <= hbeat[14]; end
    wire p_trig = (hbeat[14] && !p_last);
    reg [8:0] pcnt; always @(posedge clk_core) begin if (!rst_n) pcnt <= 273; else if (p_trig) pcnt <= 0; else if (pcnt < 273) pcnt <= pcnt + 1; end
    wire [4:0] psub = (pcnt < 273) ? (pcnt % 21) : 0;
    wire ph8 = (psub == 7), ph13 = (psub == 12), ph21 = (psub == 20);

    // 3. Core
    wire bdone; wire [23:0] pdat; wire [3:0] padr; wire pwe; wire [31:0] qout;
    wire [15:0] hq, hr; wire hv; wire [3:0] aptr;
    spu13_core u_core(.clk(clk_core), .rst_n(rst_n), .phi_8(ph8), .phi_13(ph13), .phi_21(ph21), .prime_data(pdat), .prime_addr(padr), .prime_we(pwe), .boot_done(bdone), .quadrance_out(qout), .hex_valid(hv), .hex_q(hq), .hex_r(hr), .current_axis_ptr(aptr), .seq_flash_cs(seq_flash_cs), .seq_flash_sck(seq_flash_sck), .seq_flash_mosi(seq_flash_mosi), .seq_flash_miso(seq_flash_miso));
    spu_laminar_boot u_boot(.clk(clk_core), .rst_n(rst_n), .flash_cs(boot_flash_cs), .flash_sck(boot_flash_sck), .flash_miso(flash_miso), .flash_mosi(boot_flash_mosi), .bram_data(pdat), .bram_addr(padr), .bram_we(pwe), .boot_done(bdone));

    // Flash pin mux: laminar_boot drives before boot_done, sequencer after
    wire boot_flash_cs, boot_flash_sck, boot_flash_mosi;
    assign flash_cs   = bdone ? seq_flash_cs   : boot_flash_cs;
    assign flash_sck  = bdone ? seq_flash_sck  : boot_flash_sck;
    assign flash_mosi = bdone ? seq_flash_mosi : boot_flash_mosi;
    assign seq_flash_miso = flash_miso;

    // 4. Telemetry Handshake
    reg [415:0] r_qsnap; reg [31:0] r_qcyc [0:12]; reg r_seq;
    reg [15:0] r_hq, r_hr; reg r_hpending; reg [2:0] r_hack_sync;
    integer i;
    always @(posedge clk_core) begin
        if (ph21) begin r_qcyc[aptr] <= qout; if (aptr == 12) begin for (i=0; i<13; i=i+1) r_qsnap[i*32 +: 32] <= r_qcyc[i]; r_seq <= !r_seq; end end
        if (hv && !r_hpending) begin r_hq <= hq; r_hr <= hr; r_hpending <= 1; end
        else if (r_hpending && (r_hack_sync[2] != r_hack_sync[1])) r_hpending <= 0; // Edge detection for toggle
    end

    reg [2:0] r_seq_sync; reg r_hack_50m;
    always @(posedge clk_50m) begin r_seq_sync <= {r_seq_sync[1:0], r_seq}; r_hack_sync <= {r_hack_sync[1:0], r_hack_50m}; end
    
    reg r_seen; reg [415:0] r_qtx; reg [3:0] r_midx, r_bidx; reg r_busy, r_txo; reg [8:0] r_treg; reg [15:0] r_tclk; reg [3:0] r_tbit;
    function [7:0] h2a; input [3:0] h; begin h2a = (h<10)?(8'h30+h):(8'h37+h); end endfunction
    
    wire [7:0] w_msg [0:15];
    wire [31:0] w_curq = r_qtx[r_bidx*32 +: 32];
    assign w_msg[0] = r_hpending ? "H" : (r_bidx==15 ? "S" : "Q");
    assign w_msg[1] = ":";
    assign w_msg[2] = r_hpending ? h2a(r_hq[15:12]) : h2a(w_curq[31:28]);
    assign w_msg[3] = r_hpending ? h2a(r_hq[11:8])  : h2a(w_curq[27:24]);
    assign w_msg[4] = r_hpending ? h2a(r_hq[7:4])   : h2a(w_curq[23:20]);
    assign w_msg[5] = r_hpending ? h2a(r_hq[3:0])   : h2a(w_curq[19:16]);
    assign w_msg[6] = " ";
    assign w_msg[7] = r_hpending ? h2a(r_hr[15:12]) : h2a(w_curq[15:12]);
    assign w_msg[8] = r_hpending ? h2a(r_hr[11:8])  : h2a(w_curq[11:8]);
    assign w_msg[9] = r_hpending ? h2a(r_hr[7:4])   : h2a(w_curq[7:4]);
    assign w_msg[10]= r_hpending ? h2a(r_hr[3:0])   : h2a(w_curq[3:0]);
    assign w_msg[11]= " "; assign w_msg[12]= "A"; assign w_msg[13]= h2a(r_bidx);
    assign w_msg[14]= 8'h0D; assign w_msg[15]= 8'h0A;

    reg [7:0] r_tbyte; always @(posedge clk_50m) r_tbyte <= w_msg[r_midx];

    always @(posedge clk_50m or negedge rst_n) begin
        if (!rst_n) begin r_busy<=0; r_txo<=1; r_midx<=0; r_bidx<=0; r_seen<=0; r_hack_50m<=0; end
        else if (!r_busy) begin
            r_txo <= 1;
            if (r_midx != 0) begin r_treg <= {1'b1, r_tbyte}; r_busy <= 1; r_tbit <= 0; r_tclk <= 0; end
            else if (r_hpending) begin r_treg <= {1'b1, r_tbyte}; r_busy <= 1; r_tbit <= 0; r_tclk <= 0; end
            else if (r_seq_sync[2] != r_seen) begin r_qtx <= r_qsnap; r_seen <= r_seq_sync[2]; r_bidx <= 0; r_treg <= {1'b1, r_tbyte}; r_busy <= 1; r_tbit <= 0; r_tclk <= 0; end
        end else begin
            if (r_tclk < 433) r_tclk <= r_tclk + 1;
            else begin
                r_tclk <= 0;
                if (r_tbit == 0) r_txo <= 0;
                else if (r_tbit < 9) begin r_txo <= r_treg[0]; r_treg <= {1'b0, r_treg[8:1]}; end
                else r_txo <= 1;
                if (r_tbit < 10) r_tbit <= r_tbit + 1;
                else begin
                    r_busy <= 0;
                    if (r_midx == 15) begin
                        r_midx <= 0;
                        if (r_hpending) r_hack_50m <= ~r_hack_50m; // Toggling ack
                        else if (r_bidx < 12) r_bidx <= r_bidx + 1; else r_bidx <= 15;
                    end else r_midx <= r_midx + 1;
                end
            end
        end
    end

    assign uart_tx = r_txo; assign uart_tx_telemetry = r_txo;
    assign led = {bdone, r_seen, r_hpending};
    assign sdram_clk = clk_core; assign sdram_cs_n = 1; assign sdram_dq = 16'hzzzz;
    assign {sdram_ras_n, sdram_cas_n, sdram_we_n} = 3'b111; assign sdram_ba = 2'b00; assign sdram_dm = 2'b00;
    assign {sdram_a0, sdram_a1, sdram_a2, sdram_a3, sdram_a4, sdram_a5, sdram_a6, sdram_a7, sdram_a8, sdram_a9, sdram_a10, sdram_a11, sdram_a12} = 13'd0;
endmodule

(* blackbox *) module BUFG (input I, output O); endmodule
