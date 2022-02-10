# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

require ewaol-image-core.inc

SUMMARY = "EWAOL Baremetal image"

inherit features_check

REQUIRED_DISTRO_FEATURES = "ewaol-baremetal"
CONFLICT_DISTRO_FEATURES = "ewaol-virtualization"
