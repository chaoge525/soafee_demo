# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend:ewaol := "${THISDIR}:"

#
# ewaol kmeta
#

SRC_URI:append:ewaol = " file://ewaol-kmeta;type=kmeta;name=ewaol-kmeta;destsuffix=ewaol-kmeta"

# Add gator daemon kernel configs dependencies.
KERNEL_FEATURES:append:ewaol:aarch64 = "${@bb.utils.contains('DISTRO_FEATURES', \
        'ewaol-sdk', \
        ' features/ewaol/gator.scc', '', d)}"
