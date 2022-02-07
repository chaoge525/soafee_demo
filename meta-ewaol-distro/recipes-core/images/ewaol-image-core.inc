# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL image core config with common packages"

IMAGE_INSTALL = "packagegroup-core-boot ${CORE_IMAGE_EXTRA_INSTALL}"

IMAGE_LINGUAS = " "

LICENSE = "MIT"

inherit core-image

# meta-virtualization/recipes-containers/k3s/README.md states that K3s requires
# 2GB of space in the rootfs to ensure containers can start
EWAOL_ROOTFS_EXTRA_SPACE ?= "2000000"

IMAGE_ROOTFS_EXTRA_SPACE:append = "${@ ' + ${EWAOL_ROOTFS_EXTRA_SPACE}' \
                                      if '${EWAOL_ROOTFS_EXTRA_SPACE}' \
                                      else ''}"

IMAGE_INSTALL += " \
    ca-certificates \
    docker-moby \
    k3s-server \
    packagegroup-core-ssh-openssh \
    procps \
    wget \
    "
