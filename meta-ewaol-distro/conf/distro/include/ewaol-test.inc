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

# With v1.6.0, BATS returns success with failing tests. The exit status of a
# BATS 'run' command called from the teardown_file() function is returned as
# the exit status of the bats script. This means that even if the test cases
# fail, a successful teardown will produce a passing test suite execution.
# This is a regression from v1.5.0.
# https://github.com/bats-core/bats-core/issues/575
PREFERRED_VERSION_pn-bats = "1.5.0"
