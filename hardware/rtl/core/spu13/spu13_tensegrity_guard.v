// SPDX-License-Identifier: CERN-OHL-W-2.0
// Bounded tensegrity admission guard for the TGR1 sidecar ABI.
//
// This block intentionally implements only the bounded admission guards:
// topology/connectivity, strut endpoint separation, exact closed strut
// contact, cable/GAP collapse, MAIN/CONJ GAP consistency, and exact
// type-uniform force-density equilibrium over Z[phi].
module spu13_tensegrity_guard #(
    parameter MAX_NODES = 12,
    parameter MAX_EDGES = 40
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        clear,
    input  wire        cfg_node_we,
    input  wire [3:0]  cfg_node_index,
    input  wire signed [31:0] cfg_x_a, cfg_x_b, cfg_y_a, cfg_y_b, cfg_z_a, cfg_z_b,
    input  wire [1:0]  cfg_grid,
    input  wire        cfg_edge_we,
    input  wire [5:0]  cfg_edge_index,
    input  wire [3:0]  cfg_edge_a, cfg_edge_b,
    input  wire [1:0]  cfg_edge_type,
    input  wire        start,
    output reg         done,
    output reg [3:0]   state_code,
    output reg [2:0]   fault_code,
    output reg [4:0]   node_count,
    output reg [5:0]   edge_count,
    output reg [4:0]   intersection_attempts
);
    localparam EDGE_CABLE = 2'd0, EDGE_STRUT = 2'd1, EDGE_GAP = 2'd2;
    localparam GRID_UNTAGGED = 2'd0;
    localparam ST_IDLE = 4'd0, ST_CONFIGURING = 4'd1, ST_BALANCED = 4'd2;
    localparam ST_FAULT_CABLE_SLACK = 4'd4, ST_FAULT_STRUT_COLLISION = 4'd5;
    localparam ST_FAULT_GRID_MISMATCH = 4'd6, ST_FAULT_TOPOLOGY = 4'd7;
    localparam ST_FAULT_NOT_IN_EQUILIBRIUM = 4'd8;
    localparam ST_FAULT_STRUT_INTERSECTION = 4'd9;
    localparam F_NONE = 3'd0, F_CABLE_SLACK = 3'd1, F_STRUT_COLLISION = 3'd2;
    localparam F_GRID_MISMATCH = 3'd3, F_TOPOLOGY = 3'd4;
    localparam F_NOT_IN_EQUILIBRIUM = 3'd5;
    localparam F_STRUT_INTERSECTION = 3'd6;

    localparam [4:0]
               S_IDLE = 5'd0, S_TOPOLOGY = 5'd1, S_CONNECT_INIT = 5'd2,
               S_CONNECT_SCAN = 5'd3, S_CONNECT_CHECK = 5'd4,
               S_GUARD_INIT = 5'd5, S_GUARD_SCAN = 5'd6, S_DECIDE = 5'd7,
               S_INTERSECT_INIT = 5'd8, S_INTERSECT_FIND = 5'd9,
               S_INTERSECT_START = 5'd10, S_INTERSECT_WAIT = 5'd11,
               S_FAULT_HOLD = 5'd12, S_GUARD_NODE = 5'd13,
               S_GUARD_EVAL = 5'd14, S_EQ_INIT = 5'd15,
               S_EQ_EDGE = 5'd16, S_EQ_ROW = 5'd17,
               S_EQ_SIGN_C = 5'd18, S_EQ_SIGN_S = 5'd19,
               S_EQ_MUL_LEFT = 5'd20, S_EQ_MUL_RIGHT = 5'd21,
               S_EQ_COMPARE = 5'd22, S_EQ_ADVANCE = 5'd23;

    // The probe needs several independent asynchronous coordinate reads
    // (guard scan, segment predicate, equilibrium row). Keep this bounded
    // 12-entry table in registers; inferring a third replicated RAM32M read
    // port produces an incomplete timing graph in nextpnr-xilinx.
    (* mem2reg *) reg signed [31:0] node_xa [0:MAX_NODES-1];
    (* mem2reg *) reg signed [31:0] node_xb [0:MAX_NODES-1];
    (* mem2reg *) reg signed [31:0] node_ya [0:MAX_NODES-1];
    (* mem2reg *) reg signed [31:0] node_yb [0:MAX_NODES-1];
    (* mem2reg *) reg signed [31:0] node_za [0:MAX_NODES-1];
    (* mem2reg *) reg signed [31:0] node_zb [0:MAX_NODES-1];
    (* mem2reg *) reg [1:0] node_grid [0:MAX_NODES-1];
    reg [3:0] edge_a [0:MAX_EDGES-1];
    reg [3:0] edge_b [0:MAX_EDGES-1];
    reg [1:0] edge_type [0:MAX_EDGES-1];

    reg [4:0] fsm;
    reg [5:0] edge_i;
    reg [4:0] connect_pass;
    reg [5:0] structural_count;
    reg topology_error, collision_error, intersection_error, slack_error, grid_error;
    reg equilibrium_error;
    reg [5:0] pair_i, pair_j;
    reg intersection_start;
    reg scan_valid;
    reg [3:0] scan_edge_a, scan_edge_b;
    reg [1:0] scan_edge_type;
    reg scan_collision, scan_slack, scan_grid_error;
    reg [3:0] eq_node;
    reg [1:0] eq_axis;
    reg [5:0] eq_edge_i;
    reg signed [38:0] eq_cable_a, eq_cable_b;
    reg signed [38:0] eq_strut_a, eq_strut_b;
    reg signed [38:0] eq_pivot_cable_a, eq_pivot_cable_b;
    reg signed [38:0] eq_pivot_strut_a, eq_pivot_strut_b;
    reg eq_pivot_valid;
    reg [1:0] eq_cable_sign;
    reg signed [79:0] eq_left_a, eq_left_b;
    reg reachable [0:MAX_NODES-1];
    reg [1:0] strut_degree [0:MAX_NODES-1];
    integer i;

    wire edge_valid = (edge_i < edge_count) &&
                      (edge_a[edge_i] < node_count) &&
                      (edge_b[edge_i] < node_count);
    wire same_endpoint = edge_valid &&
        node_xa[edge_a[edge_i]] == node_xa[edge_b[edge_i]] &&
        node_xb[edge_a[edge_i]] == node_xb[edge_b[edge_i]] &&
        node_ya[edge_a[edge_i]] == node_ya[edge_b[edge_i]] &&
        node_yb[edge_a[edge_i]] == node_yb[edge_b[edge_i]] &&
        node_za[edge_a[edge_i]] == node_za[edge_b[edge_i]] &&
        node_zb[edge_a[edge_i]] == node_zb[edge_b[edge_i]];

    wire pair_valid = pair_i < edge_count && pair_j < edge_count &&
                      edge_a[pair_i] < node_count && edge_b[pair_i] < node_count &&
                      edge_a[pair_j] < node_count && edge_b[pair_j] < node_count;
    wire pair_shared_endpoint = pair_valid &&
        (edge_a[pair_i] == edge_a[pair_j] || edge_a[pair_i] == edge_b[pair_j] ||
         edge_b[pair_i] == edge_a[pair_j] || edge_b[pair_i] == edge_b[pair_j]);
    wire intersection_busy, intersection_done, intersection_contact;

    // Equilibrium row source. For node i and axis k, accumulate
    //   C_ik = sum_cable/gap (x_i - x_j)
    //   S_ik = sum_strut     (x_i - x_j)
    // A type-uniform exact self-stress exists iff every nonzero (C,S) row is
    // field-collinear with one pivot row and the resulting cable/strut force
    // densities have the required positive/negative signs.
    wire eq_edge_valid = eq_edge_i < edge_count &&
                         edge_a[eq_edge_i] < node_count &&
                         edge_b[eq_edge_i] < node_count;
    wire eq_incident = eq_edge_valid &&
                       (edge_a[eq_edge_i] == eq_node || edge_b[eq_edge_i] == eq_node);
    wire [3:0] eq_other = (edge_a[eq_edge_i] == eq_node)
                          ? edge_b[eq_edge_i] : edge_a[eq_edge_i];
    wire signed [31:0] eq_node_coord_a = (eq_axis == 2'd0) ? node_xa[eq_node] :
                                                  (eq_axis == 2'd1) ? node_ya[eq_node] :
                                                                    node_za[eq_node];
    wire signed [31:0] eq_node_coord_b = (eq_axis == 2'd0) ? node_xb[eq_node] :
                                                  (eq_axis == 2'd1) ? node_yb[eq_node] :
                                                                    node_zb[eq_node];
    wire signed [31:0] eq_other_coord_a = (eq_axis == 2'd0) ? node_xa[eq_other] :
                                                   (eq_axis == 2'd1) ? node_ya[eq_other] :
                                                                     node_za[eq_other];
    wire signed [31:0] eq_other_coord_b = (eq_axis == 2'd0) ? node_xb[eq_other] :
                                                   (eq_axis == 2'd1) ? node_yb[eq_other] :
                                                                     node_zb[eq_other];
    wire signed [32:0] eq_delta_a = {eq_node_coord_a[31],eq_node_coord_a} -
                                    {eq_other_coord_a[31],eq_other_coord_a};
    wire signed [32:0] eq_delta_b = {eq_node_coord_b[31],eq_node_coord_b} -
                                    {eq_other_coord_b[31],eq_other_coord_b};

    // One shared 39x39 Z[phi] multiplier. Aggregate coefficients need 39
    // signed bits for MAX_EDGES<=40; 80 bits retain all three-term products.
    reg signed [38:0] eq_mul_xa, eq_mul_xb, eq_mul_ya, eq_mul_yb;
    wire signed [77:0] eq_mul_ac_raw = eq_mul_xa * eq_mul_ya;
    wire signed [77:0] eq_mul_bd_raw = eq_mul_xb * eq_mul_yb;
    wire signed [77:0] eq_mul_ad_raw = eq_mul_xa * eq_mul_yb;
    wire signed [77:0] eq_mul_bc_raw = eq_mul_xb * eq_mul_ya;
    wire signed [79:0] eq_mul_ac = {{2{eq_mul_ac_raw[77]}},eq_mul_ac_raw};
    wire signed [79:0] eq_mul_bd = {{2{eq_mul_bd_raw[77]}},eq_mul_bd_raw};
    wire signed [79:0] eq_mul_ad = {{2{eq_mul_ad_raw[77]}},eq_mul_ad_raw};
    wire signed [79:0] eq_mul_bc = {{2{eq_mul_bc_raw[77]}},eq_mul_bc_raw};
    wire signed [79:0] eq_mul_out_a = eq_mul_ac + eq_mul_bd;
    wire signed [79:0] eq_mul_out_b = eq_mul_ad + eq_mul_bc + eq_mul_bd;

    always @* begin
        eq_mul_xa = 39'sd0; eq_mul_xb = 39'sd0;
        eq_mul_ya = 39'sd0; eq_mul_yb = 39'sd0;
        if (fsm == S_EQ_MUL_LEFT) begin
            eq_mul_xa = eq_cable_a; eq_mul_xb = eq_cable_b;
            eq_mul_ya = eq_pivot_strut_a; eq_mul_yb = eq_pivot_strut_b;
        end else if (fsm == S_EQ_MUL_RIGHT) begin
            eq_mul_xa = eq_strut_a; eq_mul_xb = eq_strut_b;
            eq_mul_ya = eq_pivot_cable_a; eq_mul_yb = eq_pivot_cable_b;
        end
    end

    // Exact sign of a+b*phi using (2a+b)+b*sqrt(5), shared by the two pivot
    // coefficients. This is the same integer-square predicate as the oracle.
    localparam [1:0] EQ_SG_ZERO=2'd0, EQ_SG_POS=2'd1, EQ_SG_NEG=2'd2;
    reg signed [38:0] eq_sign_a, eq_sign_b;
    wire signed [40:0] eq_sign_r = ({{2{eq_sign_a[38]}},eq_sign_a} <<< 1) +
                                   {{2{eq_sign_b[38]}},eq_sign_b};
    wire signed [40:0] eq_sign_root = {{2{eq_sign_b[38]}},eq_sign_b};
    wire [81:0] eq_sign_r_sq = eq_sign_r * eq_sign_r;
    wire [81:0] eq_sign_s_sq = eq_sign_root * eq_sign_root;
    wire [81:0] eq_sign_5s_sq = (eq_sign_s_sq << 2) + eq_sign_s_sq;
    reg [1:0] eq_sign_value;

    always @* begin
        eq_sign_a = (fsm == S_EQ_SIGN_S) ? eq_pivot_strut_a : eq_pivot_cable_a;
        eq_sign_b = (fsm == S_EQ_SIGN_S) ? eq_pivot_strut_b : eq_pivot_cable_b;
        if (eq_sign_r == 0 && eq_sign_root == 0)
            eq_sign_value = EQ_SG_ZERO;
        else if (!eq_sign_r[40] && !eq_sign_root[40])
            eq_sign_value = EQ_SG_POS;
        else if (eq_sign_r[40] && eq_sign_root[40])
            eq_sign_value = EQ_SG_NEG;
        else if (!eq_sign_r[40] && eq_sign_root[40])
            eq_sign_value = (eq_sign_r_sq > eq_sign_5s_sq) ? EQ_SG_POS : EQ_SG_NEG;
        else
            eq_sign_value = (eq_sign_5s_sq > eq_sign_r_sq) ? EQ_SG_POS : EQ_SG_NEG;
    end

    spu13_tensegrity_intersection u_intersection (
        .clk(clk), .rst_n(rst_n && !clear), .start(intersection_start),
        .p0_xa(node_xa[edge_a[pair_i]]), .p0_xb(node_xb[edge_a[pair_i]]),
        .p0_ya(node_ya[edge_a[pair_i]]), .p0_yb(node_yb[edge_a[pair_i]]),
        .p0_za(node_za[edge_a[pair_i]]), .p0_zb(node_zb[edge_a[pair_i]]),
        .p1_xa(node_xa[edge_b[pair_i]]), .p1_xb(node_xb[edge_b[pair_i]]),
        .p1_ya(node_ya[edge_b[pair_i]]), .p1_yb(node_yb[edge_b[pair_i]]),
        .p1_za(node_za[edge_b[pair_i]]), .p1_zb(node_zb[edge_b[pair_i]]),
        .q0_xa(node_xa[edge_a[pair_j]]), .q0_xb(node_xb[edge_a[pair_j]]),
        .q0_ya(node_ya[edge_a[pair_j]]), .q0_yb(node_yb[edge_a[pair_j]]),
        .q0_za(node_za[edge_a[pair_j]]), .q0_zb(node_zb[edge_a[pair_j]]),
        .q1_xa(node_xa[edge_b[pair_j]]), .q1_xb(node_xb[edge_b[pair_j]]),
        .q1_ya(node_ya[edge_b[pair_j]]), .q1_yb(node_yb[edge_b[pair_j]]),
        .q1_za(node_za[edge_b[pair_j]]), .q1_zb(node_zb[edge_b[pair_j]]),
        .busy(intersection_busy), .done(intersection_done), .contact(intersection_contact)
    );

    always @(posedge clk) begin
        if (!rst_n || clear) begin
            fsm <= S_IDLE;
            done <= 1'b0;
            state_code <= ST_IDLE;
            fault_code <= F_NONE;
            node_count <= 0;
            edge_count <= 0;
            edge_i <= 0;
            connect_pass <= 0;
            structural_count <= 0;
            topology_error <= 0;
            collision_error <= 0;
            intersection_error <= 0;
            slack_error <= 0;
            grid_error <= 0;
            equilibrium_error <= 0;
            pair_i <= 0;
            pair_j <= 0;
            intersection_start <= 0;
            intersection_attempts <= 0;
            scan_valid <= 0;
            scan_edge_a <= 0;
            scan_edge_b <= 0;
            scan_edge_type <= 0;
            scan_collision <= 0;
            scan_slack <= 0;
            scan_grid_error <= 0;
            eq_node <= 0;
            eq_axis <= 0;
            eq_edge_i <= 0;
            eq_cable_a <= 0; eq_cable_b <= 0;
            eq_strut_a <= 0; eq_strut_b <= 0;
            eq_pivot_cable_a <= 0; eq_pivot_cable_b <= 0;
            eq_pivot_strut_a <= 0; eq_pivot_strut_b <= 0;
            eq_pivot_valid <= 0;
            eq_cable_sign <= EQ_SG_ZERO;
            eq_left_a <= 0; eq_left_b <= 0;
            for (i = 0; i < MAX_NODES; i = i + 1) begin
                reachable[i] <= 0;
                strut_degree[i] <= 0;
            end
        end else begin
            done <= 1'b0;
            intersection_start <= 1'b0;
            if (fsm == S_IDLE) begin
                if (cfg_node_we && cfg_node_index < MAX_NODES) begin
                    node_xa[cfg_node_index] <= cfg_x_a;
                    node_xb[cfg_node_index] <= cfg_x_b;
                    node_ya[cfg_node_index] <= cfg_y_a;
                    node_yb[cfg_node_index] <= cfg_y_b;
                    node_za[cfg_node_index] <= cfg_z_a;
                    node_zb[cfg_node_index] <= cfg_z_b;
                    node_grid[cfg_node_index] <= cfg_grid;
                    if (cfg_node_index >= node_count)
                        node_count <= cfg_node_index + 1'b1;
                end
                if (cfg_edge_we && cfg_edge_index < MAX_EDGES) begin
                    edge_a[cfg_edge_index] <= cfg_edge_a;
                    edge_b[cfg_edge_index] <= cfg_edge_b;
                    edge_type[cfg_edge_index] <= cfg_edge_type;
                    if (cfg_edge_index >= edge_count)
                        edge_count <= cfg_edge_index + 1'b1;
                end
                if (start) begin
                    state_code <= ST_CONFIGURING;
                    fault_code <= F_NONE;
                    edge_i <= 0;
                    structural_count <= 0;
                    topology_error <= 0;
                    collision_error <= 0;
                    intersection_error <= 0;
                    slack_error <= 0;
                    grid_error <= 0;
                    equilibrium_error <= 0;
                    intersection_attempts <= 0;
                    fsm <= S_TOPOLOGY;
                end
            end else if (fsm == S_TOPOLOGY) begin
                if (!edge_valid)
                    topology_error <= 1'b1;
                else if (edge_type[edge_i] == EDGE_STRUT || edge_type[edge_i] == EDGE_GAP)
                    structural_count <= structural_count + 1'b1;
                if (edge_i + 1'b1 >= edge_count) begin
                    edge_i <= 0;
                    fsm <= S_CONNECT_INIT;
                end else
                    edge_i <= edge_i + 1'b1;
            end else if (fsm == S_CONNECT_INIT) begin
                if (node_count < 6 || structural_count < 6)
                    topology_error <= 1'b1;
                for (i = 0; i < MAX_NODES; i = i + 1)
                    reachable[i] <= 1'b0;
                if (node_count != 0)
                    reachable[0] <= 1'b1;
                edge_i <= 0;
                connect_pass <= 0;
                fsm <= S_CONNECT_SCAN;
            end else if (fsm == S_CONNECT_SCAN) begin
                if (edge_valid) begin
                    if (reachable[edge_a[edge_i]]) reachable[edge_b[edge_i]] <= 1'b1;
                    if (reachable[edge_b[edge_i]]) reachable[edge_a[edge_i]] <= 1'b1;
                end
                if (edge_i + 1'b1 >= edge_count) begin
                    edge_i <= 0;
                    if (connect_pass + 1'b1 >= node_count)
                        fsm <= S_CONNECT_CHECK;
                    else
                        connect_pass <= connect_pass + 1'b1;
                end else
                    edge_i <= edge_i + 1'b1;
            end else if (fsm == S_CONNECT_CHECK) begin
                for (i = 0; i < MAX_NODES; i = i + 1)
                    if (i < node_count && !reachable[i]) topology_error <= 1'b1;
                fsm <= S_GUARD_INIT;
            end else if (fsm == S_GUARD_INIT) begin
                for (i = 0; i < MAX_NODES; i = i + 1)
                    strut_degree[i] <= 0;
                edge_i <= 0;
                fsm <= S_GUARD_SCAN;
            end else if (fsm == S_GUARD_SCAN) begin
                // Stage 1: isolate the distributed edge-table read from the
                // node-table predicates. This path was the only near-critical
                // path in the first V:6 Artix route and failed in silicon
                // despite 0.7 ns of modeled slack.
                scan_valid <= edge_valid;
                if (edge_valid) begin
                    scan_edge_a <= edge_a[edge_i];
                    scan_edge_b <= edge_b[edge_i];
                    scan_edge_type <= edge_type[edge_i];
                end
                fsm <= S_GUARD_NODE;
            end else if (fsm == S_GUARD_NODE) begin
                // Stage 2: evaluate node-table and degree predicates from
                // registered endpoint indices.
                scan_collision <= scan_valid && scan_edge_type == EDGE_STRUT &&
                    (scan_edge_a == scan_edge_b ||
                     (node_xa[scan_edge_a] == node_xa[scan_edge_b] &&
                      node_xb[scan_edge_a] == node_xb[scan_edge_b] &&
                      node_ya[scan_edge_a] == node_ya[scan_edge_b] &&
                      node_yb[scan_edge_a] == node_yb[scan_edge_b] &&
                      node_za[scan_edge_a] == node_za[scan_edge_b] &&
                      node_zb[scan_edge_a] == node_zb[scan_edge_b]) ||
                     strut_degree[scan_edge_a] != 0 ||
                     strut_degree[scan_edge_b] != 0);
                scan_slack <= scan_valid &&
                    (scan_edge_type == EDGE_CABLE || scan_edge_type == EDGE_GAP) &&
                    node_xa[scan_edge_a] == node_xa[scan_edge_b] &&
                    node_xb[scan_edge_a] == node_xb[scan_edge_b] &&
                    node_ya[scan_edge_a] == node_ya[scan_edge_b] &&
                    node_yb[scan_edge_a] == node_yb[scan_edge_b] &&
                    node_za[scan_edge_a] == node_za[scan_edge_b] &&
                    node_zb[scan_edge_a] == node_zb[scan_edge_b];
                scan_grid_error <= scan_valid &&
                    node_grid[scan_edge_a] != node_grid[scan_edge_b] &&
                    node_grid[scan_edge_a] != GRID_UNTAGGED &&
                    node_grid[scan_edge_b] != GRID_UNTAGGED &&
                    scan_edge_type != EDGE_GAP;
                fsm <= S_GUARD_EVAL;
            end else if (fsm == S_GUARD_EVAL) begin
                // Stage 3: commit only registered predicate results.
                if (scan_collision) collision_error <= 1'b1;
                if (scan_slack) slack_error <= 1'b1;
                if (scan_grid_error) grid_error <= 1'b1;
                if (scan_valid && scan_edge_type == EDGE_STRUT) begin
                    strut_degree[scan_edge_a] <= strut_degree[scan_edge_a] + 1'b1;
                    strut_degree[scan_edge_b] <= strut_degree[scan_edge_b] + 1'b1;
                end
                if (edge_i + 1'b1 >= edge_count)
                    fsm <= S_INTERSECT_INIT;
                else begin
                    edge_i <= edge_i + 1'b1;
                    fsm <= S_GUARD_SCAN;
                end
            end else if (fsm == S_INTERSECT_INIT) begin
                pair_i <= 0;
                pair_j <= 1;
                fsm <= S_INTERSECT_FIND;
            end else if (fsm == S_INTERSECT_FIND) begin
                if (pair_i + 1'b1 >= edge_count) begin
                    fsm <= S_EQ_INIT;
                end else if (pair_j >= edge_count) begin
                    pair_i <= pair_i + 1'b1;
                    pair_j <= pair_i + 2'd2;
                end else if (pair_valid && edge_type[pair_i] == EDGE_STRUT &&
                             edge_type[pair_j] == EDGE_STRUT && !pair_shared_endpoint) begin
                    fsm <= S_INTERSECT_START;
                end else begin
                    pair_j <= pair_j + 1'b1;
                end
            end else if (fsm == S_INTERSECT_START) begin
                intersection_start <= 1'b1;
                intersection_attempts <= intersection_attempts + 1'b1;
                fsm <= S_INTERSECT_WAIT;
            end else if (fsm == S_INTERSECT_WAIT) begin
                if (intersection_done) begin
                    if (intersection_contact) begin
                        intersection_error <= 1'b1;
                        fsm <= S_DECIDE;
                    end else begin
                        pair_j <= pair_j + 1'b1;
                        fsm <= S_INTERSECT_FIND;
                    end
                end
            end else if (fsm == S_EQ_INIT) begin
                eq_node <= 0;
                eq_axis <= 0;
                eq_edge_i <= 0;
                eq_cable_a <= 0; eq_cable_b <= 0;
                eq_strut_a <= 0; eq_strut_b <= 0;
                eq_pivot_valid <= 1'b0;
                equilibrium_error <= 1'b0;
                fsm <= S_EQ_EDGE;
            end else if (fsm == S_EQ_EDGE) begin
                if (eq_incident) begin
                    if (edge_type[eq_edge_i] == EDGE_STRUT) begin
                        eq_strut_a <= eq_strut_a + {{6{eq_delta_a[32]}},eq_delta_a};
                        eq_strut_b <= eq_strut_b + {{6{eq_delta_b[32]}},eq_delta_b};
                    end else begin
                        eq_cable_a <= eq_cable_a + {{6{eq_delta_a[32]}},eq_delta_a};
                        eq_cable_b <= eq_cable_b + {{6{eq_delta_b[32]}},eq_delta_b};
                    end
                end
                if (eq_edge_i + 1'b1 >= edge_count)
                    fsm <= S_EQ_ROW;
                else
                    eq_edge_i <= eq_edge_i + 1'b1;
            end else if (fsm == S_EQ_ROW) begin
                if (eq_cable_a == 0 && eq_cable_b == 0 &&
                    eq_strut_a == 0 && eq_strut_b == 0) begin
                    fsm <= S_EQ_ADVANCE;
                end else if (!eq_pivot_valid) begin
                    if ((eq_cable_a == 0 && eq_cable_b == 0) ||
                        (eq_strut_a == 0 && eq_strut_b == 0)) begin
                        equilibrium_error <= 1'b1;
                        fsm <= S_DECIDE;
                    end else begin
                        eq_pivot_cable_a <= eq_cable_a;
                        eq_pivot_cable_b <= eq_cable_b;
                        eq_pivot_strut_a <= eq_strut_a;
                        eq_pivot_strut_b <= eq_strut_b;
                        eq_pivot_valid <= 1'b1;
                        fsm <= S_EQ_SIGN_C;
                    end
                end else begin
                    fsm <= S_EQ_MUL_LEFT;
                end
            end else if (fsm == S_EQ_SIGN_C) begin
                eq_cable_sign <= eq_sign_value;
                fsm <= S_EQ_SIGN_S;
            end else if (fsm == S_EQ_SIGN_S) begin
                if (eq_sign_value == EQ_SG_ZERO ||
                    eq_cable_sign == EQ_SG_ZERO ||
                    eq_sign_value != eq_cable_sign) begin
                    equilibrium_error <= 1'b1;
                    fsm <= S_DECIDE;
                end else begin
                    fsm <= S_EQ_ADVANCE;
                end
            end else if (fsm == S_EQ_MUL_LEFT) begin
                eq_left_a <= eq_mul_out_a;
                eq_left_b <= eq_mul_out_b;
                fsm <= S_EQ_MUL_RIGHT;
            end else if (fsm == S_EQ_MUL_RIGHT) begin
                if (eq_left_a != eq_mul_out_a || eq_left_b != eq_mul_out_b) begin
                    equilibrium_error <= 1'b1;
                    fsm <= S_DECIDE;
                end else begin
                    fsm <= S_EQ_ADVANCE;
                end
            end else if (fsm == S_EQ_ADVANCE) begin
                eq_edge_i <= 0;
                eq_cable_a <= 0; eq_cable_b <= 0;
                eq_strut_a <= 0; eq_strut_b <= 0;
                if (eq_axis == 2'd2) begin
                    eq_axis <= 0;
                    if (eq_node + 1'b1 >= node_count) begin
                        if (!eq_pivot_valid) equilibrium_error <= 1'b1;
                        fsm <= S_DECIDE;
                    end else begin
                        eq_node <= eq_node + 1'b1;
                        fsm <= S_EQ_EDGE;
                    end
                end else begin
                    eq_axis <= eq_axis + 1'b1;
                    fsm <= S_EQ_EDGE;
                end
            end else if (fsm == S_DECIDE) begin
                if (topology_error) begin
                    state_code <= ST_FAULT_TOPOLOGY; fault_code <= F_TOPOLOGY;
                    fsm <= S_FAULT_HOLD;
                end else if (collision_error) begin
                    state_code <= ST_FAULT_STRUT_COLLISION; fault_code <= F_STRUT_COLLISION;
                    fsm <= S_FAULT_HOLD;
                end else if (slack_error) begin
                    state_code <= ST_FAULT_CABLE_SLACK; fault_code <= F_CABLE_SLACK;
                    fsm <= S_FAULT_HOLD;
                end else if (intersection_error) begin
                    state_code <= ST_FAULT_STRUT_INTERSECTION; fault_code <= F_STRUT_INTERSECTION;
                    fsm <= S_FAULT_HOLD;
                end else if (grid_error) begin
                    state_code <= ST_FAULT_GRID_MISMATCH; fault_code <= F_GRID_MISMATCH;
                    fsm <= S_FAULT_HOLD;
                end else if (equilibrium_error) begin
                    state_code <= ST_FAULT_NOT_IN_EQUILIBRIUM;
                    fault_code <= F_NOT_IN_EQUILIBRIUM;
                    fsm <= S_FAULT_HOLD;
                end else begin
                    state_code <= ST_BALANCED; fault_code <= F_NONE;
                    fsm <= S_IDLE;
                end
                done <= 1'b1;
            end else begin // S_FAULT_HOLD: explicit clear/reset is the only exit.
                fsm <= S_FAULT_HOLD;
            end
        end
    end
endmodule
