#include "ff.h"
#include "diskio.h"
#include "spu_sd.h"
#include <string.h>

static DSTATUS sd_status = STA_NOINIT;

DSTATUS disk_initialize(BYTE pdrv) {
    (void)pdrv;
    if (spu_sd_init()) {
        sd_status = 0;
    } else {
        sd_status = STA_NOINIT | STA_NODISK;
    }
    return sd_status;
}

DSTATUS disk_status(BYTE pdrv) {
    (void)pdrv;
    if (!spu_sd_mounted()) {
        sd_status |= STA_NODISK;
    } else {
        sd_status &= ~STA_NODISK;
    }
    return sd_status;
}

DRESULT disk_read(BYTE pdrv, BYTE *buff, LBA_t sector, UINT count) {
    (void)pdrv;
    if (!spu_sd_mounted()) return RES_NOTRDY;
    int rc = spu_sd_read_blocks(sector, buff, count);
    return rc == 0 ? RES_OK : RES_ERROR;
}

DRESULT disk_write(BYTE pdrv, const BYTE *buff, LBA_t sector, UINT count) {
    (void)pdrv;
    if (!spu_sd_mounted()) return RES_NOTRDY;
    int rc = spu_sd_write_blocks(sector, buff, count);
    return rc == 0 ? RES_OK : RES_ERROR;
}

DRESULT disk_ioctl(BYTE pdrv, BYTE cmd, void *buff) {
    (void)pdrv;
    switch (cmd) {
    case CTRL_SYNC:
        return RES_OK;
    case GET_SECTOR_COUNT:
        *(LBA_t *)buff = 0; // caller probes via FatFs
        return RES_OK;
    case GET_SECTOR_SIZE:
        *(WORD *)buff = 512;
        return RES_OK;
    case GET_BLOCK_SIZE:
        *(DWORD *)buff = 1;
        return RES_OK;
    default:
        return RES_PARERR;
    }
}
