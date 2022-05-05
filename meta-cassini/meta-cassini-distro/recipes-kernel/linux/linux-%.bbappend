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
