`timescale 1ns/1ps

module spu13_tensegrity_sidecar_tb #(
    parameter USE_ZPHI_KARATSUBA = 0
);
    reg clk = 0;
    always #5 clk = ~clk;

    reg rst_n = 0;
    reg stream_start = 0;
    reg [15:0] stream_length = 0;
    reg [31:0] stream_vector_id = 0;
    reg stream_valid = 0;
    reg [7:0] stream_data = 0;
    reg stream_commit = 0;
    reg stream_abort = 0;
    reg status_hold = 0;
    wire [127:0] transport_status;
    wire active_valid;
    wire busy;
    wire [7:0] loader_error;

    reg [7:0] blob [0:507];
    integer errors = 0;
    integer i;
    integer admission_cycles;
    integer tb_cycle_counter = 0;
    integer transaction_start_cycle = 0;
    reg [31:0] crc;

    always @(posedge clk)
        tb_cycle_counter = tb_cycle_counter + 1;

    spu13_tensegrity_sidecar #(
        .PARSE_WATCHDOG_LIMIT(2048),
        .VERIFY_WATCHDOG_LIMIT(100000),
        .USE_ZPHI_KARATSUBA(USE_ZPHI_KARATSUBA)
    ) dut (
        .clk(clk), .rst_n(rst_n),
        .stream_start(stream_start), .stream_length(stream_length),
        .stream_vector_id(stream_vector_id),
        .stream_valid(stream_valid), .stream_data(stream_data),
        .stream_commit(stream_commit), .stream_abort(stream_abort),
        .status_hold(status_hold),
        .transport_status(transport_status), .active_valid(active_valid),
        .busy(busy), .loader_error(loader_error)
    );

    function [31:0] crc32_byte;
        input [31:0] crc_in;
        input [7:0] byte_data;
        reg [31:0] s;
        integer b;
        begin
            s = crc_in ^ byte_data;
            for (b = 0; b < 8; b = b + 1)
                s = s[0] ? ((s >> 1) ^ 32'hEDB88320) : (s >> 1);
            crc32_byte = s;
        end
    endfunction

    task put32;
        input integer offset;
        input signed [31:0] value;
        begin
            blob[offset]   = value[31:24];
            blob[offset+1] = value[23:16];
            blob[offset+2] = value[15:8];
            blob[offset+3] = value[7:0];
        end
    endtask

    task put_node;
        input integer index;
        input signed [31:0] x, y, z;
        integer base;
        begin
            base = 12 + index * 28;
            put32(base, x);      put32(base+4, 0);
            put32(base+8, y);    put32(base+12, 0);
            put32(base+16, z);   put32(base+20, 0);
            blob[base+24] = 1;
            blob[base+25] = 0; blob[base+26] = 0; blob[base+27] = 0;
        end
    endtask

    task put_edge;
        input integer index;
        input [7:0] node_a, node_b, edge_kind;
        integer base;
        begin
            base = 12 + 12*28 + index*4;
            blob[base] = node_a;
            blob[base+1] = node_b;
            blob[base+2] = edge_kind;
            blob[base+3] = 0;
        end
    endtask

    task finalize_header;
        begin
            blob[0] = "T"; blob[1] = "G"; blob[2] = "R"; blob[3] = "1";
            blob[4] = 1; blob[5] = 12; blob[6] = 30; blob[7] = 0;
            crc = 32'hFFFFFFFF;
            for (i = 12; i < 468; i = i + 1)
                crc = crc32_byte(crc, blob[i]);
            crc = ~crc;
            blob[8] = crc[31:24]; blob[9] = crc[23:16];
            blob[10] = crc[15:8]; blob[11] = crc[7:0];
        end
    endtask

    task build_canonical;
        begin
            for (i = 0; i < 508; i = i + 1) blob[i] = 0;
            put_node(0,0,1,2); put_node(1,0,1,-2);
            put_node(2,0,-1,2); put_node(3,0,-1,-2);
            put_node(4,1,2,0); put_node(5,1,-2,0);
            put_node(6,-1,2,0); put_node(7,-1,-2,0);
            put_node(8,2,0,1); put_node(9,2,0,-1);
            put_node(10,-2,0,1); put_node(11,-2,0,-1);

            put_edge(0,0,4,0); put_edge(1,0,6,0); put_edge(2,0,8,0); put_edge(3,0,10,0);
            put_edge(4,1,4,0); put_edge(5,1,6,0); put_edge(6,1,9,0); put_edge(7,1,11,0);
            put_edge(8,2,5,0); put_edge(9,2,7,0); put_edge(10,2,8,0); put_edge(11,2,10,0);
            put_edge(12,3,5,0); put_edge(13,3,7,0); put_edge(14,3,9,0); put_edge(15,3,11,0);
            put_edge(16,4,8,0); put_edge(17,4,9,0); put_edge(18,5,8,0); put_edge(19,5,9,0);
            put_edge(20,6,10,0); put_edge(21,6,11,0); put_edge(22,7,10,0); put_edge(23,7,11,0);
            put_edge(24,0,1,1); put_edge(25,2,3,1); put_edge(26,4,5,1); put_edge(27,6,7,1);
            put_edge(28,8,10,1); put_edge(29,9,11,1);
            finalize_header;
        end
    endtask

    task begin_stream;
        input [31:0] vector_id;
        begin
            @(negedge clk);
            transaction_start_cycle = tb_cycle_counter;
            stream_length = 468;
            stream_vector_id = vector_id;
            stream_start = 1;
            @(negedge clk);
            stream_start = 0;
        end
    endtask

    task send_complete;
        input [31:0] vector_id;
        begin
            begin_stream(vector_id);
            for (i = 0; i < 468; i = i + 1) begin
                stream_data = blob[i]; stream_valid = 1;
                @(negedge clk);
            end
            stream_valid = 0;
            stream_commit = 1;
            @(negedge clk);
            stream_commit = 0;
        end
    endtask

    task wait_idle;
        output integer elapsed_cycles;
        integer timeout;
        begin
            timeout = 0;
            while (busy && timeout < 200000) begin
                @(negedge clk);
                timeout = timeout + 1;
            end
            if (timeout == 200000) begin
                errors = errors + 1;
                $display("FAIL sidecar timeout");
            end
            elapsed_cycles = timeout;
        end
    endtask

    task expect_status;
        input [7:0] expected_state;
        input [7:0] expected_fault;
        input [31:0] expected_vector;
        input [8*40-1:0] name;
        begin
            if (!active_valid || transport_status[119:112] !== expected_state ||
                transport_status[111:104] !== expected_fault ||
                transport_status[95:64] !== expected_vector) begin
                errors = errors + 1;
                $display("FAIL %0s valid=%b state=%0d fault=%0d vector=%h error=%0d",
                         name, active_valid, transport_status[119:112],
                         transport_status[111:104], transport_status[95:64],
                         loader_error);
            end else begin
                $display("PASS %0s state=%0d fault=%0d vector=%h",
                         name, expected_state, expected_fault, expected_vector);
            end
        end
    endtask

    initial begin
        repeat (4) @(negedge clk);
        rst_n = 1;

        build_canonical;
        send_complete(32'h12345678);
        wait_idle(admission_cycles);
        expect_status(2, 0, 32'h12345678, "canonical transactional load");
        $display("ZPHI_CYCLE kind=sidecar fixture=valid_admission mode=%0d cycles=%0d decision=state_%0d_fault_%0d",
                 USE_ZPHI_KARATSUBA, tb_cycle_counter - transaction_start_cycle,
                 transport_status[119:112], transport_status[111:104]);
        if (transport_status[47:40] !== 8'd12 ||
            transport_status[39:32] !== 8'd30 || loader_error !== 0) begin
            errors = errors + 1;
            $display("FAIL canonical diagnostics nodes=%0d edges=%0d error=%0d",
                     transport_status[47:40], transport_status[39:32], loader_error);
        end

        // Parsing is transactional too: a wedged BRAM replay substate must
        // terminate, identify that substate, and preserve the active verdict.
        build_canonical;
        send_complete(32'hBAD0C0DE);
        while (dut.parse_state != 4'd3)
            @(negedge clk);
        force dut.parse_state = 4'd3;
        wait_idle(admission_cycles);
        release dut.parse_state;
        expect_status(2, 0, 32'h12345678, "parser-timeout rollback");
        if (loader_error !== 11 || transport_status[103:96] !== 8'h93) begin
            errors = errors + 1;
            $display("FAIL parser timeout diagnostics error=%0d stage=%02h",
                     loader_error, transport_status[103:96]);
        end

        // If an exact service never returns, the loader must terminate with
        // an explicit stage-coded timeout and preserve the active transaction.
        // Hold the intersection service's completion wire so the coordinator
        // remains at that explicit service boundary until its watchdog fires.
        build_canonical;
        force dut.u_guard.intersection_done = 1'b0;
        send_complete(32'hDEADC0DE);
        wait_idle(admission_cycles);
        release dut.u_guard.intersection_done;
        expect_status(2, 0, 32'h12345678, "guard-timeout rollback");
        if (loader_error !== 10 || transport_status[103:96] !== 8'h85) begin
            errors = errors + 1;
            $display("FAIL timeout diagnostics error=%0d stage=%02h",
                     loader_error, transport_status[103:96]);
        end

        build_canonical;
        send_complete(32'h12345678);
        wait_idle(admission_cycles);
        expect_status(2, 0, 32'h12345678, "post-timeout recovery");
        $display("ZPHI_CYCLE kind=sidecar fixture=timeout_recovery mode=%0d cycles=%0d decision=state_%0d_fault_%0d",
                 USE_ZPHI_KARATSUBA, tb_cycle_counter - transaction_start_cycle,
                 transport_status[119:112], transport_status[111:104]);
        if (loader_error !== 0 || transport_status[103:96] !== 8'd8) begin
            errors = errors + 1;
            $display("FAIL recovery diagnostics error=%0d stage=%02h",
                     loader_error, transport_status[103:96]);
        end

        // A B3 read may overlap the guard's one-cycle done pulse. Hold the
        // published status at that exact boundary, prove the old transaction
        // remains coherent, then release and commit the remembered result.
        build_canonical;
        send_complete(32'hCAFEBABE);
        while (dut.parse_state != 4'd11)
            @(negedge clk);
        status_hold = 1'b1;
        i = 0;
        while (!dut.guard_result_pending && i < 200000) begin
            @(negedge clk);
            i = i + 1;
        end
        if (i == 200000 || !busy) begin
            errors = errors + 1;
            $display("FAIL status hold did not remember guard completion");
        end
        expect_status(2, 0, 32'h12345678, "B3 hold preserves prior transaction");
        status_hold = 1'b0;
        wait_idle(admission_cycles);
        expect_status(2, 0, 32'hCAFEBABE, "B3 release commits pending result");

        // An aborted write must preserve the prior active bank and verdict.
        begin_stream(32'hAAAAAAAA);
        for (i = 0; i < 20; i = i + 1) begin
            stream_data = blob[i]; stream_valid = 1; @(negedge clk);
        end
        stream_valid = 0; stream_abort = 1; @(negedge clk); stream_abort = 0;
        wait_idle(admission_cycles);
        expect_status(2, 0, 32'hCAFEBABE, "transport abort rollback");
        if (loader_error !== 1) begin
            errors = errors + 1;
            $display("FAIL abort error code got=%0d", loader_error);
        end

        // A payload mutation with the old header CRC must also roll back.
        blob[100] = blob[100] ^ 8'h01;
        send_complete(32'hBBBBBBBB);
        wait_idle(admission_cycles);
        expect_status(2, 0, 32'hCAFEBABE, "CRC32 rollback");
        $display("ZPHI_CYCLE kind=sidecar fixture=corrupt_payload_rollback mode=%0d cycles=%0d decision=state_%0d_fault_%0d",
                 USE_ZPHI_KARATSUBA, tb_cycle_counter - transaction_start_cycle,
                 transport_status[119:112], transport_status[111:104]);
        if (loader_error !== 7) begin
            errors = errors + 1;
            $display("FAIL CRC32 error code got=%0d", loader_error);
        end

        // Restore the table, perturb node 0 x, and recompute the payload CRC.
        build_canonical;
        put32(12, 1);
        finalize_header;
        send_complete(32'd6);
        wait_idle(admission_cycles);
        expect_status(8, 5, 32'd6, "not-in-equilibrium active verdict");
        $display("ZPHI_CYCLE kind=sidecar fixture=mechanical_negative_admission mode=%0d cycles=%0d decision=state_%0d_fault_%0d",
                 USE_ZPHI_KARATSUBA, tb_cycle_counter - transaction_start_cycle,
                 transport_status[119:112], transport_status[111:104]);

        // Pin reset recovery separately from timeout recovery. A complete
        // reset must clear the active transaction, after which the same valid
        // table is admitted independently with the selected multiplier.
        rst_n = 0;
        repeat (2) @(negedge clk);
        rst_n = 1;
        repeat (2) @(negedge clk);
        build_canonical;
        send_complete(32'hC1EA0001);
        wait_idle(admission_cycles);
        expect_status(2, 0, 32'hC1EA0001, "reset/reload recovery");
        $display("ZPHI_CYCLE kind=sidecar fixture=reset_recovery mode=%0d cycles=%0d decision=state_%0d_fault_%0d",
                 USE_ZPHI_KARATSUBA, tb_cycle_counter - transaction_start_cycle,
                 transport_status[119:112], transport_status[111:104]);

        if (errors == 0)
            $display("SPU13_TENSEGRITY_SIDECAR_TB: PASS");
        else
            $display("SPU13_TENSEGRITY_SIDECAR_TB: FAIL errors=%0d", errors);
        $finish(errors != 0);
    end
endmodule
