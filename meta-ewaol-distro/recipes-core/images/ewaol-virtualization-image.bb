# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL Virtualization image, providing a Control VM as Xen Dom0."

require ewaol-image-core.inc

inherit features_check
REQUIRED_DISTRO_FEATURES = "ewaol-virtualization"
CONFLICT_DISTRO_FEATURES = "ewaol-baremetal"

EXTRA_IMAGEDEPENDS:append = " xen"

# Increase storage size by 2GB to not run out of free space
EWAOL_CONTROL_VM_ROOTFS_EXTRA_SPACE ?= "2000000"

IMAGE_ROOTFS_EXTRA_SPACE:append = " \
    ${@ ' + ${EWAOL_CONTROL_VM_ROOTFS_EXTRA_SPACE}' \
    if '${EWAOL_CONTROL_VM_ROOTFS_EXTRA_SPACE}' \
    else ''} \
    "

IMAGE_INSTALL:append = " \
    ${@ 'ewaol-guest-vm-package' if d.getVar('BUILD_EWAOL_GUEST_VM') == 'True' else ''} \
    ${@ 'prebuilt-guest-vm-package' if d.getVar('INCLUDE_PREBUILT_GUEST_VM') == 'True' else ''} \
    kernel-module-xen-blkback \
    kernel-module-xen-gntalloc \
    kernel-module-xen-gntdev \
    kernel-module-xen-netback \
    qemu-keymaps \
    qemu-system-i386 \
    xen-tools \
    "
