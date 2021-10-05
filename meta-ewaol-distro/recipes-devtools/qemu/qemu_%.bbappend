# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

OVERRIDES:append = "${EWAOL_OVERRIDES}"

QEMU_TARGETS:ewaol-virtualization = "i386"
QEMU_TARGETS:append:aarch64:ewaol-virtualization = " aarch64"

require ${@bb.utils.contains('DISTRO_FEATURES', \
                             'ewaol-virtualization', \
                             'recipes-devtools/qemu/qemu-package-split.inc', \
                             '', d)}
