# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend:ewaol := "${THISDIR}:${THISDIR}/linux-yocto:"

#
# ewaol kmeta
#

SRC_URI:append:ewaol = " file://ewaol-kmeta;type=kmeta;name=ewaol-kmeta;destsuffix=ewaol-kmeta"

# Add gator daemon kernel configs dependencies.
KERNEL_FEATURES:append:ewaol:aarch64 = "${@bb.utils.contains('DISTRO_FEATURES', \
        'ewaol-sdk', \
        ' features/ewaol/gator.scc', '', d)}"

#
# yocto kernel cache
#

# Add patch for kernel meta only for kernel recipes
EWAOL_KERNEL_META_PATCHES:append:ewaol = "${@bb.utils.contains('PROVIDES', \
        'virtual/kernel', \
        ' file://0001-xen-move-x86-configs-into-a-separate-file.patch;patchdir=kernel-meta', \
        '', d)}"

SRC_URI:append:ewaol = "${EWAOL_KERNEL_META_PATCHES}"
