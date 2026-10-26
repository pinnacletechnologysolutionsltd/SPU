// spu_flash_map.vh — W25Q128JVSQ (16MB) Address Map
// Defines retained for spu_laminar_boot.v hydration addresses.
`define FLASH_PELL_BASE        24'h100000
`define FLASH_GOLDEN_BASE      24'h100100
`define FLASH_RPLU_CFG_BASE    24'h110000
// 64KB clear of FLASH_RPLU_CFG_BASE's table region. Consumed by
// spu4_som_flash_loader.v -- 4 nodes x NUM_FEATURES x 4 bytes (P,Q as two
// 16-bit big-endian halves per feature), NUM_FEATURES ascending, node 0 first.
`define FLASH_SPU4_SOM_BASE    24'h120000
