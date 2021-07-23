# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL Image Core config with common packages"

IMAGE_INSTALL = "packagegroup-core-boot ${CORE_IMAGE_EXTRA_INSTALL}"

IMAGE_LINGUAS = " "

LICENSE = "MIT"

inherit core-image

# meta-virtualization/recipes-containers/k3s/README.md states that K3S requires
# 2GB of space in the rootfs to ensure containers can start
IMAGE_ROOTFS_SIZE ?= "2097152"
IMAGE_ROOTFS_EXTRA_SPACE_append = "${@bb.utils.contains("DISTRO_FEATURES", "systemd", " + 4096", "", d)}"

IMAGE_INSTALL += " \
    packagegroup-core-ssh-openssh \
    ca-certificates \
    k3s-server \
    "
