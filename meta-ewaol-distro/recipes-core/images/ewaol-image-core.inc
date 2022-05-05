# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL image core config with common packages"

IMAGE_LINGUAS = " "

LICENSE = "MIT"

IMAGE_BUILDINFO_VARS = " \
    BBMULTICONFIG DISTRO DISTRO_VERSION DISTRO_FEATURES IMAGE_FEATURES \
    IMAGE_NAME MACHINE MACHINE_FEATURES DEFAULTTUNE COMBINED_FEATURES "

inherit core-image image-buildinfo extrausers

# meta-virtualization/recipes-containers/k3s/README.md states that K3s requires
# 2GB of space in the rootfs to ensure containers can start
EWAOL_ROOTFS_EXTRA_SPACE ?= "2000000"

IMAGE_ROOTFS_EXTRA_SPACE:append = "${@ ' + ${EWAOL_ROOTFS_EXTRA_SPACE}' \
                                      if '${EWAOL_ROOTFS_EXTRA_SPACE}' \
                                      else ''}"

IMAGE_FEATURES += "ssh-server-openssh bash-completion-pkgs"

IMAGE_INSTALL += " \
    bash \
    bash-completion-extra \
    ca-certificates \
    docker-ce \
    k3s-server \
    procps \
    sudo \
    wget \
    "

# Add two users: one with admin access and one without admin access
# 'EWAOL_USER_ACCOUNT', 'EWAOL_ADMIN_ACCOUNT'
EXTRA_USERS_PARAMS:prepend = " useradd -p '' ${EWAOL_USER_ACCOUNT}; \
                               useradd -p '' ${EWAOL_ADMIN_ACCOUNT}; \
                               groupadd ${EWAOL_ADMIN_GROUP}; \
                               usermod -aG ${EWAOL_ADMIN_GROUP} ${EWAOL_ADMIN_ACCOUNT}; \
                             "
