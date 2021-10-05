# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL Image Core config with common packages"

IMAGE_INSTALL = "packagegroup-core-boot ${CORE_IMAGE_EXTRA_INSTALL}"

IMAGE_LINGUAS = " "

LICENSE = "MIT"

inherit core-image

# meta-virtualization/recipes-containers/k3s/README.md states that K3S requires
# 2GB of space in the rootfs to ensure containers can start, lets add 5GB
IMAGE_ROOTFS_EXTRA_SPACE ?= "5000000"

IMAGE_INSTALL += " \
    ca-certificates \
    docker-moby \
    k3s-server \
    packagegroup-core-ssh-openssh \
    procps \
    wget \
    "
