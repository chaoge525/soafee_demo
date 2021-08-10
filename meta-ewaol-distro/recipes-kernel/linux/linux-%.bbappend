# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS_prepend_ewaol := "${THISDIR}:"

#
# ewaol kmeta
#

SRC_URI_append_ewaol = " file://ewaol-kmeta;type=kmeta;name=ewaol-kmeta;destsuffix=ewaol-kmeta"

# Add gator daemon kernel configs dependencies.
KERNEL_FEATURES_append_ewaol_aarch64 = "${@bb.utils.contains('DISTRO_FEATURES', \
        'ewaol-sdk', \
        ' features/ewaol/gator.scc', '', d)}"
