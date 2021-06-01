# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

require ewaol-image-core.inc

SUMMARY = "EWAOL Image with docker runtime."

IMAGE_INSTALL += "docker-moby"
