# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL image core config with common packages"

IMAGE_LINGUAS = " "

LICENSE = "MIT"

# meta-virtualization/recipes-containers/k3s/README.md states that K3s requires
# 2GB of space in the rootfs to ensure containers can start
EWAOL_ROOTFS_EXTRA_SPACE ?= "2000000"

CASSINI_ROOTFS_EXTRA_SPACE ?= "${EWAOL_ROOTFS_EXTRA_SPACE}"

inherit cassini-image
