`timescale 1ns/1ps
// HEX telemetry keeps its historical (B-D,A-D) order and 16-bit width.
module spu13_core_hex_conformance_tb;
    // The frozen decoder candidate retains preselected-lane HEX timing.
    // This define is supplied only by its explicit qualification fixture.
`ifdef SPU_HEX_PRESELECT_PROFILE
    localparam PRESELECT_HEX=1;
`else
    localparam PRESELECT_HEX=0;
`endif
    reg clk=0,rst_n=0,inst_valid=0;
    reg [63:0] inst_word=0;
    wire inst_done,hex_valid,boot_ready;
    wire [15:0] hex_q,hex_r;
    wire qr_commit_valid;
    wire [3:0] qr_commit_lane;
    integer i,guard,completions;
    always #5 clk=~clk;
    spu13_core #(.DEVICE("SIM"),.ENABLE_RPLU(0),.ENABLE_LATTICE(0),
        .ENABLE_MATH(0),.ENABLE_SEQUENCER(0),.ENABLE_IROTC(1)) uut (
        .clk(clk),.rst_n(rst_n),.phi_8(1'b0),.phi_13(1'b0),.phi_21(1'b0),
        .dec_fast_cfg_wr_en(1'b0),.dec_fast_cfg_sel(3'd0),
        .dec_fast_cfg_material(8'd0),.dec_fast_cfg_addr(10'd0),
        .dec_fast_cfg_data(64'd0),.phinary_cfg(16'd0),
        .prime_data(24'd0),.prime_addr(4'd0),.prime_we(1'b0),
        .boot_done(1'b1),.pell_data(32'd0),.pell_addr(3'd0),.pell_we(1'b0),
        .manual_rotor_en(1'b0),.manual_rotor_data(64'd0),
        .mem_ready(1'b1),.mem_rd_manifold(832'd0),.mem_burst_done(1'b0),
        .inst_valid(inst_valid),.inst_word(inst_word),.inst_done(inst_done),
        .hex_valid(hex_valid),.hex_q(hex_q),.hex_r(hex_r),.boot_ready(boot_ready),
        .qr_commit_valid(qr_commit_valid),.qr_commit_lane(qr_commit_lane)
    );

    task issue;
        input [63:0] word;
        input check_hex;
        input [15:0] expected_q,expected_r;
        begin
            @(negedge clk);inst_word=word;inst_valid=1;
            guard=0;
            @(posedge clk);#1;
            while(!inst_done && guard<40) begin
                @(posedge clk);#1;guard=guard+1;
            end
            if(!inst_done) $fatal(1,"instruction completion timeout %h",word);
            if(word[63:56]==8'h1d &&
               (!qr_commit_valid || qr_commit_lane !== (word[55:48]%13)))
                $fatal(1,"public QLDI byte wrap mismatch %h lane=%d",word,qr_commit_lane);
            if(check_hex && (!hex_valid || hex_q!==expected_q || hex_r!==expected_r))
                $fatal(1,"HEX %h got (%h,%h) expected (%h,%h)",
                    word,hex_q,hex_r,expected_q,expected_r);
            // Keep valid high past retirement: exactly one completion.
            completions=1;
            repeat(3) begin
                @(posedge clk);#1;
                if(inst_done) completions=completions+1;
                if(check_hex && hex_valid) $fatal(1,"duplicate HEX telemetry");
            end
            if(completions!=1) $fatal(1,"duplicate retirement");
            @(negedge clk);inst_valid=0;inst_word=0;
            repeat(2) @(posedge clk);
        end
    endtask

    task project;
        input [63:0] word;
        input [15:0] expected_q,expected_r;
        begin
            // Old profile requires an explicit source-selection transaction.
            // Its result is outside the selected-source assertion; retirement
            // and exactly-once behavior are still checked by issue().
            if(PRESELECT_HEX) issue(word,0,0,0);
            issue(word,1,expected_q,expected_r);
        end
    endtask

    initial begin
        repeat(3) @(negedge clk);rst_n=1;
        guard=0;
        while(!boot_ready && guard<100) begin
            @(posedge clk);#1;guard=guard+1;
        end
        if(!boot_ready) $fatal(1,"boot timeout");
        issue(64'h1d01000305000100,0,0,0); // QR1=(3,5,0,1)
        issue(64'h1d0200fe07000400,0,0,0); // QR2=(-2,7,0,4)
        project(64'h1600020000000000,16'd3,16'hfffa);
        project(64'h1600010000000000,16'd4,16'd2);
        project(64'h1600020000000000,16'd3,16'hfffa);
        issue(64'h1dff00090c000200,0,0,0); // QR255 wraps to QR8
        project(64'h1600ff0000000000,16'd10,16'd7);
        // Public dispatch, not a private helper name, verifies the byte domain.
        for(i=0;i<256;i=i+1) begin
            issue({8'h1d,i[7:0],8'd0,i[7:0],8'd12,8'd0,8'd2,8'd0},0,0,0);
            project({8'h16,8'd0,i[7:0],40'd0},16'd10,i<128?i-2:i-258);
        end
        $display("PASS HEX public all256 byte indices, signed output, held-valid retirement; preselect_profile=%0d",PRESELECT_HEX);
        $finish;
    end
    initial begin #100000;$fatal(1,"test deadline");end
endmodule
