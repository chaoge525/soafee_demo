# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

require ewaol-image-core.inc

SUMMARY = "EWAOL Image"

inherit features_check
CONFLICT_DISTRO_FEATURES = "ewaol-virtualization"
