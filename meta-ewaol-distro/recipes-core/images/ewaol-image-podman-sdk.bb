# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL sdk Image with podman runtime."

require ewaol-image-podman.bb

inherit features_check

REQUIRED_DISTRO_FEATURES = "ewaol-sdk"
