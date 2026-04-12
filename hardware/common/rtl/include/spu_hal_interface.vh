// Minimal spu_hal_interface.vh stub for simulation triage
// Defines the LAMINAR display bus convention used by HAL modules.

`ifndef _SPU_HAL_INTERFACE_VH_
`define _SPU_HAL_INTERFACE_VH_

`define LAMINAR_DISPLAY_BUS \
    input  wire        pulse_61k, \
    input  wire [15:0] q_a, \
    input  wire [15:0] q_b, \
    input  wire [15:0] q_c, \
    input  wire [15:0] q_energy, \
    input  wire [15:0] rational_scale, \
    output wire        display_ready

// Minimal default definitions to avoid undefined macro warnings
`ifndef SOUL_BASE_ADDR
`define SOUL_BASE_ADDR 0
`endif

`ifndef ADDR_STOICISM
`define ADDR_STOICISM 0
`endif

`endif // _SPU_HAL_INTERFACE_VH_
