# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Config specifc to the ewaol-test distro feature, enabled using
# DISTRO_FEATURES

DISTRO_FEATURES_append = " ptest"
EXTRA_IMAGE_FEATURES_append = " debug-tweaks"
IMAGE_INSTALL_append = " container-engine-integration-tests-ptest \
                         k3s-integration-tests-ptest"
