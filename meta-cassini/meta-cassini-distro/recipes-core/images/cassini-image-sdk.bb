# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

SUMMARY = "CASSINI SDK Image"

require cassini-image-base.bb

inherit features_check

REQUIRED_DISTRO_FEATURES += " cassini-sdk"
