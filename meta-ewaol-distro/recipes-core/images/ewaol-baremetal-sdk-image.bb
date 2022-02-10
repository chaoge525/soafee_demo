# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL Baremetal SDK Image"

require ewaol-baremetal-image.bb

REQUIRED_DISTRO_FEATURES += " ewaol-sdk"
