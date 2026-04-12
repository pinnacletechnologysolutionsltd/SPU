// reset_adapter.v — small helper to derive active-high reset from active-low rst_n
// Added to help unify reset polarity across top-level wrappers.

module reset_adapter (
    input  wire rst_n_in,
    output wire reset_out
);

    // Simple combinational inversion: active-high reset asserted when rst_n_in==0
    assign reset_out = ~rst_n_in;

endmodule
