# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

EWAOL_MACHINE_EXTRAS ?= "${EWAOL_ARM_BSP_DYNAMIC_DIR}/conf/machine/ewaol-machine-extra-settings.inc"
require ${@bb.utils.contains('BBFILE_COLLECTIONS', 'meta-arm-bsp', \
                             '${EWAOL_MACHINE_EXTRAS}' , \
                             '', d)}
