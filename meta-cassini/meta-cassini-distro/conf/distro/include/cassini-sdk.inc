# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

# Config specifc to the cassini-sdk distro feature, enabled using
# DISTRO_FEATURES

IMAGE_FEATURES:append = " \
 package-management \
 dev-pkgs \
 tools-sdk \
 tools-debug \
 tools-profile \
 debug-tweaks \
 ssh-server-openssh"

IMAGE_INSTALL:append = " kernel-base kernel-devsrc kernel-modules"

IMAGE_INSTALL:append:aarch64 = " gator-daemon"
