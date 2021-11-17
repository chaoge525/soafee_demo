# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL SDK Image"

require ewaol-image-core.inc

inherit features_check

REQUIRED_DISTRO_FEATURES = "ewaol-sdk"
