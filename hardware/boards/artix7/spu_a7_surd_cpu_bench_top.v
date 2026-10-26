// Offline integrated canonical CPU timing top; external sys_clk target 25 MHz.
// No board operating clock or kernel speed claim follows from this wrapper.
module spu_a7_surd_cpu_bench_top #(
    parameter ENABLE_SURD_CPU=1,
    parameter ENABLE_REGEN=1
) (
    input wire sys_clk,rst_n,
    output wire uart_tx
);
    reg [63:0] rng=64'h13579bdf2468ace1;
    reg [5:0] tick=0;
    reg [4:0] step=0;
    reg pending=0,valid=0;
    reg [63:0] instruction=0;
    reg [31:0] checksum=0;
    reg [2:0] index_a=0,index_b=1,index_c=2;
    wire boot,done,s_ready,s_read,s_retire;
    wire [31:0] s_data;
    wire [3:0] s_status;
    wire qr_valid;
    wire [63:0] qa,qb,qc,qd;
    wire issue_ready=ENABLE_SURD_CPU ? s_ready:boot;
    wire [31:0] event_data=(s_read ? s_data:32'd0) ^
        (s_retire ? {28'd0,s_status}:32'd0) ^
        (qr_valid ? qa[31:0]^qb[31:0]^qc[31:0]^qd[31:0]:32'd0);
    spu13_core #(.DEVICE("SIM"),.ENABLE_SURD_CPU(ENABLE_SURD_CPU),.ENABLE_REGEN(ENABLE_REGEN),
        .ENABLE_SEQUENCER(0),.ENABLE_RPLU(0),.ENABLE_LATTICE(0),.ENABLE_MATH(0),
        .ENABLE_CORE_RPLU_V2(1),.ENABLE_CORE_RPLU_V2_PIPELINE(0),
        .ENABLE_CORE_RPLU_V2_EXTENSIONS(0)) cpu (
        .clk(sys_clk),.rst_n(rst_n),
        .phi_8(tick==8),.phi_13(tick==13),.phi_21(tick==21),
        .dec_fast_cfg_wr_en(1'b0),.dec_fast_cfg_sel(3'd0),.dec_fast_cfg_material(8'd0),
        .dec_fast_cfg_addr(10'd0),.dec_fast_cfg_data(64'd0),.phinary_cfg(16'd0),
        .prime_data(24'd0),.prime_addr(4'd0),.prime_we(1'b0),.boot_done(1'b1),
        .pell_data(32'd0),.pell_addr(3'd0),.pell_we(1'b0),
        .manual_rotor_en(1'b0),.manual_rotor_data(64'd0),.regen_dphi_cfg(8'd0),
        .mem_ready(1'b1),.mem_rd_manifold(832'd0),.mem_burst_done(1'b0),
        .inst_valid(valid),.inst_word(instruction),.inst_done(done),.boot_ready(boot),
        .surd_issue_ready(s_ready),.surd_read_valid(s_read),.surd_read_data(s_data),
        .surd_retire_valid(s_retire),.surd_status(s_status),
        .qr_commit_valid(qr_valid),.qr_commit_A(qa),.qr_commit_B(qb),
        .qr_commit_C(qc),.qr_commit_D(qd));
    always @(posedge sys_clk) begin
        if(!rst_n) begin
            rng<=64'h13579bdf2468ace1;tick<=0;step<=0;
            pending<=0;valid<=0;instruction<=0;checksum<=0;
            index_a<=0;index_b<=1;index_c<=2;
        end else begin
            tick<=tick+1'b1;
            rng<={rng[62:0],rng[63]^rng[62]^rng[60]^rng[59]};
            if(s_read || s_retire || qr_valid)
                checksum<={checksum[30:0],checksum[31]}^event_data;
            if(pending && done) begin
                pending<=0;valid<=0;step<=step==26 ? 0:step+1'b1;
            end else if(!pending && !valid && issue_ready) begin
                pending<=1;valid<=1;
                if(step==0) begin
                    instruction<={8'h1d,8'd0,8'd0,rng[31:0],8'd0};
                    index_a<=rng[2:0];index_b<=rng[5:3];index_c<=rng[8:6];
                end
                else if(step>=1 && step<=6)
                    instruction<={8'h70,5'd0,index_a,5'd0,(step[2:0]-3'd1),rng[31:0]|32'd1,8'd0};
                else if(step==7) instruction<={8'h71,5'd0,index_a,48'd0};
                else if(step>=8 && step<=13)
                    instruction<={8'h70,5'd0,index_b,5'd0,(step[2:0]),rng[31:0]|32'd1,8'd0};
                else if(step==14) instruction<={8'h71,5'd0,index_b,48'd0};
                else if(step==15) instruction<={8'h73,5'd0,index_c,5'd0,index_a,13'd0,index_b,24'd0};
                else if(step==16) instruction<={8'h74,5'd0,index_c,5'd0,index_a,13'd0,index_b,24'd0};
                else if(step==17) instruction<={8'h75,5'd0,index_c,5'd0,index_a,13'd0,index_b,24'd0};
                else if(step==18) instruction<={8'h76,5'd0,index_c,5'd0,index_c,40'd0};
                else if(step>=19 && step<=24)
                    instruction<={8'h72,5'd0,index_c,5'd0,(step[2:0]-3'd3),40'd0};
                else if(step==25) instruction<=64'h7700000000000000;
                else instruction<=64'h1b01000000000000;
            end
        end
    end
    assign uart_tx=^checksum;
endmodule
