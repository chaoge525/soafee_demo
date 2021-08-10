# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Config specifc to the ewaol-sdk distro feature, enabled using
# DISTRO_FEATURES

IMAGE_FEATURES_append = " \
 package-management \
 dev-pkgs \
 tools-sdk \
 tools-debug \
 tools-profile \
 debug-tweaks \
 ssh-server-openssh"

IMAGE_INSTALL_append = " kernel-devsrc kernel-modules"

IMAGE_INSTALL_append_aarch64 = " gator-daemon"
