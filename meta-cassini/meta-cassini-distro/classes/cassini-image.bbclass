# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

IMAGE_BUILDINFO_VARS = " \
    BBMULTICONFIG DISTRO DISTRO_VERSION DISTRO_FEATURES IMAGE_FEATURES \
    IMAGE_NAME MACHINE MACHINE_FEATURES DEFAULTTUNE COMBINED_FEATURES "

inherit core-image extrausers image-buildinfo

# meta-virtualization/recipes-containers/k3s/README.md states that K3s requires
# 2GB of space in the rootfs to ensure containers can start
CASSINI_ROOTFS_EXTRA_SPACE ?= "2000000"

IMAGE_ROOTFS_EXTRA_SPACE:append = "${@ ' + ${CASSINI_ROOTFS_EXTRA_SPACE}' \
                                      if '${CASSINI_ROOTFS_EXTRA_SPACE}' \
                                      else ''}"

IMAGE_FEATURES += "ssh-server-openssh bash-completion-pkgs"

IMAGE_INSTALL += "\
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
# 'CASSINI_USER_ACCOUNT', 'CASSINI_ADMIN_ACCOUNT'
EXTRA_USERS_PARAMS:prepend = " useradd -p '' ${CASSINI_USER_ACCOUNT}; \
                               useradd -p '' ${CASSINI_ADMIN_ACCOUNT}; \
                               groupadd ${CASSINI_ADMIN_GROUP}; \
                               usermod -aG ${CASSINI_ADMIN_GROUP} ${CASSINI_ADMIN_ACCOUNT}; \
                             "
