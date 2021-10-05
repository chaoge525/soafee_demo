# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL Xen Host Image."

require ewaol-image-core.inc

inherit features_check
REQUIRED_DISTRO_FEATURES += "ewaol-virtualization"

EXTRA_IMAGEDEPENDS:append = " xen"

# Lets add 5GB by default
EWAOL_HOST_ROOTFS_EXTRA_SPACE ?= " + 5000000"
IMAGE_ROOTFS_EXTRA_SPACE:append ?= "${EWAOL_HOST_ROOTFS_EXTRA_SPACE}"

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
