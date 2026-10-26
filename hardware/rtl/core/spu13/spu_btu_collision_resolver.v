`timescale 1ns / 1ps

module spu_btu_collision_resolver (
    input wire clk,
    input wire rst_n,
    input wire [63:0] neuron_activation_lines, // 64-node input grid (One-Hot or Multi-Hot)

    // Core SPU Pipeline Control
    output reg pipeline_stall,                  // Drops back to Stage 1 to hold wave input
    output reg [5:0] selected_row_k,            // Decoded 1D address for BTU ROM selection
    output reg bus_valid);

    reg [63:0] pending_queue;
    wire multi_hot_detected;

    // Detect if more than one node has fired simultaneously
    // Clears the lowest set bit and checks if remaining bits are non-zero
    assign multi_hot_detected = (neuron_activation_lines & (neuron_activation_lines - 1)) != 0;

    // Combinational Priority Encoder Matrix (Finds lowest index active bit)
    integer i, j;
    reg [5:0] priority_index;
    reg found_bit, queued_found;

    always @(*) begin
        priority_index = 6'd0;
        found_bit = 1'b0;
        for (i = 0; i < 64; i = i + 1) begin
            if (neuron_activation_lines[i] && !found_bit) begin
                priority_index = i[5:0];
                found_bit = 1'b1;
            end
        end
    end

    // Sequential Tracking Datapath
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pipeline_stall <= 1'b0;
            selected_row_k <= 6'd0;
            pending_queue  <= 64'd0;
            bus_valid      <= 1'b0;
        end else begin
            if (pending_queue != 64'd0) begin
                // --- SERVICE QUEUED COLLISION (Cycle 2) ---
                // Process the next remaining bit in our backlog array
                queued_found = 1'b0;

                for (j = 0; j < 64; j = j + 1) begin
                    if (pending_queue[j] && !queued_found) begin
                        selected_row_k <= j[5:0];
                        pending_queue[j] <= 1'b0; // Clear it out of the queue
                        queued_found = 1'b1;
                    end
                end

                // If this was the last queued node, clear the bubble stall line
                if ((pending_queue & (pending_queue - 1)) == 0) begin
                    pipeline_stall <= 1'b0;
                end
                bus_valid <= 1'b1;

            end else if (neuron_activation_lines != 64'd0) begin
                // --- INITIAL DISPATCH (Cycle 1) ---
                selected_row_k <= priority_index;
                bus_valid      <= 1'b1;

                if (multi_hot_detected) begin
                    // Multiple peaks hit! Trap the secondary bits inside our pending matrix
                    // and drop a pipeline bubble stall backward to stop Stage 1 ingestion.
                    pending_queue  <= neuron_activation_lines;
                    pending_queue[priority_index] <= 1'b0; // Clear the one we are servicing now
                    pipeline_stall <= 1'b1;
                end else begin
                    pipeline_stall <= 1'b0;
                end
            end else begin
                bus_valid      <= 1'b0;
                pipeline_stall <= 1'b0;
            end
        end
    end
endmodule