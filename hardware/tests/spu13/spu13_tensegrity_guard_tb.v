`timescale 1ns/1ps

module spu13_tensegrity_guard_tb;
    reg clk = 0, rst_n = 0, clear = 0, cfg_node_we = 0, cfg_edge_we = 0, start = 0;
    reg [3:0] cfg_node_index, cfg_edge_a, cfg_edge_b;
    reg [1:0] cfg_grid;
    reg [5:0] cfg_edge_index;
    reg [1:0] cfg_edge_type;
    reg signed [31:0] cfg_x_a, cfg_x_b, cfg_y_a, cfg_y_b, cfg_z_a, cfg_z_b;
    wire done;
    wire [3:0] state_code;
    wire [2:0] fault_code;
    wire [4:0] node_count;
    wire [5:0] edge_count;
    wire [4:0] intersection_attempts;
    integer errors = 0;

    always #5 clk = ~clk;

    spu13_tensegrity_guard dut (
        .clk(clk), .rst_n(rst_n), .clear(clear),
        .cfg_node_we(cfg_node_we), .cfg_node_index(cfg_node_index),
        .cfg_x_a(cfg_x_a), .cfg_x_b(cfg_x_b), .cfg_y_a(cfg_y_a), .cfg_y_b(cfg_y_b),
        .cfg_z_a(cfg_z_a), .cfg_z_b(cfg_z_b), .cfg_grid(cfg_grid),
        .cfg_edge_we(cfg_edge_we), .cfg_edge_index(cfg_edge_index),
        .cfg_edge_a(cfg_edge_a), .cfg_edge_b(cfg_edge_b), .cfg_edge_type(cfg_edge_type),
        .start(start), .done(done), .state_code(state_code), .fault_code(fault_code),
        .node_count(node_count), .edge_count(edge_count),
        .intersection_attempts(intersection_attempts)
    );

    task wipe;
    begin
        @(negedge clk); clear = 1; @(posedge clk); @(negedge clk); clear = 0; @(posedge clk);
    end endtask

    task node;
        input [3:0] index; input integer x; input integer y; input integer z; input [1:0] grid;
    begin
        @(negedge clk);
        cfg_node_index=index; cfg_x_a=x; cfg_x_b=0; cfg_y_a=y; cfg_y_b=0;
        cfg_z_a=z; cfg_z_b=0; cfg_grid=grid; cfg_node_we=1;
        @(posedge clk); @(negedge clk); cfg_node_we=0; @(posedge clk);
    end endtask

    task node_phi;
        input [3:0] index;
        input integer xa; input integer xb; input integer ya;
        input integer yb; input integer za; input integer zb;
    begin
        @(negedge clk);
        cfg_node_index=index; cfg_x_a=xa; cfg_x_b=xb; cfg_y_a=ya; cfg_y_b=yb;
        cfg_z_a=za; cfg_z_b=zb; cfg_grid=1; cfg_node_we=1;
        @(posedge clk); @(negedge clk); cfg_node_we=0; @(posedge clk);
    end endtask

    task put_edge;
        input [5:0] index; input [3:0] a; input [3:0] b; input [1:0] kind;
    begin
        @(negedge clk);
        cfg_edge_index=index; cfg_edge_a=a; cfg_edge_b=b; cfg_edge_type=kind; cfg_edge_we=1;
        @(posedge clk); @(negedge clk); cfg_edge_we=0; @(posedge clk);
    end endtask

    task antipodal_nodes;
    begin
        node_phi(0,0,0,1,0,0,1);   node_phi(1,0,0,1,0,0,-1);
        node_phi(2,0,0,-1,0,0,1);  node_phi(3,0,0,-1,0,0,-1);
        node_phi(4,1,0,0,1,0,0);   node_phi(5,1,0,0,-1,0,0);
        node_phi(6,-1,0,0,1,0,0);  node_phi(7,-1,0,0,-1,0,0);
        node_phi(8,0,1,0,0,1,0);   node_phi(9,0,1,0,0,-1,0);
        node_phi(10,0,-1,0,0,1,0); node_phi(11,0,-1,0,0,-1,0);
    end endtask

    task antipodal_edges;
    begin
        put_edge(0,0,2,0); put_edge(1,0,4,0); put_edge(2,0,6,0); put_edge(3,0,8,0); put_edge(4,0,10,0);
        put_edge(5,1,3,0); put_edge(6,1,4,0); put_edge(7,1,6,0); put_edge(8,1,9,0); put_edge(9,1,11,0);
        put_edge(10,2,5,0); put_edge(11,2,7,0); put_edge(12,2,8,0); put_edge(13,2,10,0);
        put_edge(14,3,5,0); put_edge(15,3,7,0); put_edge(16,3,9,0); put_edge(17,3,11,0);
        put_edge(18,4,6,0); put_edge(19,4,8,0); put_edge(20,4,9,0); put_edge(21,5,7,0);
        put_edge(22,5,8,0); put_edge(23,5,9,0); put_edge(24,6,10,0); put_edge(25,6,11,0);
        put_edge(26,7,10,0); put_edge(27,7,11,0); put_edge(28,8,9,0); put_edge(29,10,11,0);
        put_edge(30,0,3,1); put_edge(31,1,2,1); put_edge(32,4,7,1);
        put_edge(33,5,6,1); put_edge(34,8,11,1); put_edge(35,9,10,1);
    end endtask

    task prove_fault_lockout;
        integer k;
    begin
        @(negedge clk);
        cfg_node_index=11; cfg_x_a=99; cfg_x_b=0; cfg_y_a=0; cfg_y_b=0;
        cfg_z_a=0; cfg_z_b=0; cfg_grid=1; cfg_node_we=1;
        cfg_edge_index=35; cfg_edge_a=0; cfg_edge_b=1; cfg_edge_type=0;
        cfg_edge_we=1; start=1;
        @(posedge clk); @(negedge clk);
        cfg_node_we=0; cfg_edge_we=0; start=0;
        for (k=0;k<20;k=k+1) begin
            @(posedge clk); #1;
            if (done) begin errors=errors+1; $display("FAIL terminal fault accepted restart"); end
        end
        if (state_code !== 7 || fault_code !== 4 || node_count !== 6 || edge_count !== 6) begin
            errors=errors+1;
            $display("FAIL terminal fault poison state=%0d fault=%0d nodes=%0d edges=%0d",
                     state_code,fault_code,node_count,edge_count);
        end else $display("PASS terminal fault lockout/poison hold");
    end endtask

    task canonical_nodes;
    begin
        node(0,0,1,2,1); node(1,0,1,-2,1); node(2,0,-1,2,1); node(3,0,-1,-2,1);
        node(4,1,2,0,1); node(5,1,-2,0,1); node(6,-1,2,0,1); node(7,-1,-2,0,1);
        node(8,2,0,1,1); node(9,2,0,-1,1); node(10,-2,0,1,1); node(11,-2,0,-1,1);
    end endtask

    task canonical_nodes_phi_scaled;
    begin
        node_phi(0,0,0,0,1,0,2);   node_phi(1,0,0,0,1,0,-2);
        node_phi(2,0,0,0,-1,0,2);  node_phi(3,0,0,0,-1,0,-2);
        node_phi(4,0,1,0,2,0,0);   node_phi(5,0,1,0,-2,0,0);
        node_phi(6,0,-1,0,2,0,0);  node_phi(7,0,-1,0,-2,0,0);
        node_phi(8,0,2,0,0,0,1);   node_phi(9,0,2,0,0,0,-1);
        node_phi(10,0,-2,0,0,0,1); node_phi(11,0,-2,0,0,0,-1);
    end endtask

    task canonical_edges;
    begin
        put_edge(0,0,4,0); put_edge(1,0,6,0); put_edge(2,0,8,0); put_edge(3,0,10,0);
        put_edge(4,1,4,0); put_edge(5,1,6,0); put_edge(6,1,9,0); put_edge(7,1,11,0);
        put_edge(8,2,5,0); put_edge(9,2,7,0); put_edge(10,2,8,0); put_edge(11,2,10,0);
        put_edge(12,3,5,0); put_edge(13,3,7,0); put_edge(14,3,9,0); put_edge(15,3,11,0);
        put_edge(16,4,8,0); put_edge(17,4,9,0); put_edge(18,5,8,0); put_edge(19,5,9,0);
        put_edge(20,6,10,0); put_edge(21,6,11,0); put_edge(22,7,10,0); put_edge(23,7,11,0);
        put_edge(24,0,1,1); put_edge(25,2,3,1); put_edge(26,4,5,1); put_edge(27,6,7,1);
        put_edge(28,8,10,1); put_edge(29,9,11,1);
    end endtask

    task run_expect;
        input [3:0] expected_state; input [2:0] expected_fault; input [8*24-1:0] name;
    begin
        @(negedge clk); start=1; @(posedge clk); @(negedge clk); start=0;
        @(posedge done); #1;
        if (state_code !== expected_state || fault_code !== expected_fault) begin
            $display("FAIL %0s state=%0d fault=%0d expected=%0d/%0d", name, state_code, fault_code, expected_state, expected_fault);
            errors = errors + 1;
        end else
            $display("PASS %0s state=%0d fault=%0d", name, state_code, fault_code);
        @(posedge clk);
    end endtask

    initial begin
        cfg_node_index=0; cfg_grid=0; cfg_edge_index=0; cfg_edge_a=0; cfg_edge_b=0; cfg_edge_type=0;
        cfg_x_a=0; cfg_x_b=0; cfg_y_a=0; cfg_y_b=0; cfg_z_a=0; cfg_z_b=0;
        repeat (2) @(posedge clk); rst_n=1;

        wipe; canonical_nodes; canonical_edges;
        run_expect(2,0,"canonical");

        wipe; canonical_nodes_phi_scaled; canonical_edges;
        run_expect(2,0,"canonical_phi_scaled");

        wipe; canonical_nodes; canonical_edges; put_edge(25,0,9,1);
        run_expect(5,2,"strut_collision");

        wipe; canonical_nodes; canonical_edges; node(4,0,1,2,1);
        run_expect(4,1,"cable_slack");

        wipe; canonical_nodes; canonical_edges; node(0,0,1,2,2);
        run_expect(6,3,"grid_mismatch");

        wipe;
        node(0,0,0,0,1); node(1,0,0,0,1); node(2,0,0,0,1);
        node(3,0,0,0,1); node(4,0,0,0,1); node(5,0,0,0,1);
        put_edge(0,0,1,1); put_edge(1,0,2,1); put_edge(2,1,2,1);
        put_edge(3,3,4,1); put_edge(4,3,5,1); put_edge(5,4,5,1);
        run_expect(7,4,"disconnected_topology");
        prove_fault_lockout;

        wipe; antipodal_nodes; antipodal_edges;
        run_expect(9,6,"strut_intersection");

        wipe; canonical_nodes; canonical_edges; node(0,1,1,2,1);
        run_expect(8,5,"not_in_equilibrium");

        if (errors == 0) $display("SPU13_TENSEGRITY_GUARD_TB: PASS");
        else $display("SPU13_TENSEGRITY_GUARD_TB: FAIL errors=%0d", errors);
        $finish(errors != 0);
    end
endmodule
