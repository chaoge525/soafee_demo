# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

export TEST_COMMON_DIR = "${datadir}/runtime-integration-tests-common"
ENVSUBST_VARS:append = " \$TEST_COMMON_DIR"
