# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL Virtualization SDK Image"

require ewaol-virtualization-image.bb

REQUIRED_DISTRO_FEATURES += " ewaol-sdk"
