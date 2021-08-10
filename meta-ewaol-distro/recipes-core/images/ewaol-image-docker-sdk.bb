# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL sdk Image with docker runtime."

require ewaol-image-docker.bb

inherit features_check

REQUIRED_DISTRO_FEATURES = "ewaol-sdk"
