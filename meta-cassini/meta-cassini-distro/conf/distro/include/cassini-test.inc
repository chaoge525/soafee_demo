# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

# Config specifc to the cassini-test distro feature, enabled using
# DISTRO_FEATURES

DISTRO_FEATURES:append = " ptest"
EXTRA_IMAGE_FEATURES:append = " debug-tweaks"
IMAGE_INSTALL:append = " container-engine-integration-tests-ptest \
                         k3s-integration-tests-ptest \
                         user-accounts-integration-tests-ptest"
