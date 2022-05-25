# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend:ewaol := "${THISDIR}:${THISDIR}/linux-yocto:"

#
# yocto kernel cache
#

# Add patch for kernel meta only for kernel recipes
EWAOL_KERNEL_META_PATCHES:append:ewaol = "${@bb.utils.contains('PROVIDES', \
        'virtual/kernel', \
        ' file://0001-xen-move-x86-configs-into-a-separate-file.patch;patchdir=kernel-meta', \
        '', d)}"

SRC_URI:append:ewaol = "${EWAOL_KERNEL_META_PATCHES}"
