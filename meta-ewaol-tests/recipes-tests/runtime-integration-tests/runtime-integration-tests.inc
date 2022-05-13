# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

export TEST_COMMON_DIR = "${datadir}/runtime-integration-tests-common"
export TEST_RUNTIME_DIR = "/var/run/ewaol-integration-tests"

ENVSUBST_VARS:append = " \$TEST_COMMON_DIR\
                         \$TEST_RUNTIME_DIR "

do_install[vardeps] += "\
    TEST_COMMON_DIR \
    TEST_RUNTIME_DIR \
    "
