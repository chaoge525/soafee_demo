# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL Xen Host Image."

require ewaol-image-core.inc

inherit features_check
REQUIRED_DISTRO_FEATURES += "ewaol-virtualization"

EXTRA_IMAGEDEPENDS:append = " xen"

# Increase storage size by 2GB to not run out of free space
EWAOL_HOST_ROOTFS_EXTRA_SPACE ?= "2000000"

IMAGE_ROOTFS_EXTRA_SPACE:append = "${@ ' + ${EWAOL_HOST_ROOTFS_EXTRA_SPACE}' \
                                      if '${EWAOL_HOST_ROOTFS_EXTRA_SPACE}' \
                                      else ''}"

IMAGE_INSTALL:append = " \
    ewaol-vm-package \
    kernel-module-xen-blkback \
    kernel-module-xen-gntalloc \
    kernel-module-xen-gntdev \
    kernel-module-xen-netback \
    qemu-keymaps \
    qemu-system-i386 \
    xen-tools \
    "
