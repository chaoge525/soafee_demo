# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend:cassini := "${THISDIR}:${THISDIR}/linux-yocto:"

#
# cassini kmeta
#

SRC_URI:append:cassini = " file://cassini-kmeta;type=kmeta;name=cassini-kmeta;destsuffix=cassini-kmeta"

# Add gator daemon kernel configs dependencies.
KERNEL_FEATURES:append:cassini:aarch64 = "${@bb.utils.contains('DISTRO_FEATURES', \
        'cassini-sdk', \
        ' features/cassini/gator.scc', '', d)}"

#
# yocto kernel cache
#

# Add patch for kernel meta only for kernel recipes
CASSINI_KERNEL_META_PATCHES:append:cassini = "${@bb.utils.contains('PROVIDES', \
        'virtual/kernel', \
        ' file://0001-security-move-x86_64-configs-to-separate-file.patch;patchdir=kernel-meta', \
        '', d)}"

SRC_URI:append:cassini = "${CASSINI_KERNEL_META_PATCHES}"
