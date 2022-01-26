# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL SDK Image"

require ewaol-image-core.inc

inherit features_check

REQUIRED_DISTRO_FEATURES = "ewaol-sdk"
CONFLICT_DISTRO_FEATURES = "ewaol-virtualization"
