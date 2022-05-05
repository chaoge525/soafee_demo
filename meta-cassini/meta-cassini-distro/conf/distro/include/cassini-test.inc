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

# With v1.6.0, BATS returns success with failing tests. The exit status of a
# BATS 'run' command called from the teardown_file() function is returned as
# the exit status of the bats script. This means that even if the test cases
# fail, a successful teardown will produce a passing test suite execution.
# This is a regression from v1.5.0.
# https://github.com/bats-core/bats-core/issues/575

# Update (10May2022): The reported bug was already fixed upstream and a patch
# has been sent to meta-oe to apply the backport fix on top of 1.6.0. This
# will be requested to have it also backported to kirkstone branch.
# When importing baremetal test, make sure to check the status and remove this
# compatibility.
# https://jira.arm.com/browse/OSSEMBEDA-1722
PREFERRED_VERSION_pn-bats = "1.5.0"
