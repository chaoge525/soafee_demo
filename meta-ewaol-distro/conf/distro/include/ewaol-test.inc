# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Config specifc to the ewaol-test distro feature, enabled using
# DISTRO_FEATURES

DISTRO_FEATURES:append = " ptest"
EXTRA_IMAGE_FEATURES:append = " debug-tweaks"
IMAGE_INSTALL:append = " container-engine-integration-tests-ptest \
                         k3s-integration-tests-ptest \
                         user-accounts-integration-tests-ptest"

IMAGE_INSTALL:append = "${@bb.utils.contains('DISTRO_FEATURES',\
    'ewaol-virtualization', ' virtualization-integration-tests-ptest', '', d)}"
