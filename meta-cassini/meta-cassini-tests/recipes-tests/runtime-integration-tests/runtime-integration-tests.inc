# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

export TEST_COMMON_DIR = "${datadir}/runtime-integration-tests-common"
export TEST_RUNTIME_DIR = "/var/run/cassini-integration-tests"

ENVSUBST_VARS:append = " \$TEST_COMMON_DIR\
                         \$TEST_RUNTIME_DIR "

do_install[vardeps] += "\
    TEST_COMMON_DIR \
    TEST_RUNTIME_DIR \
    "
