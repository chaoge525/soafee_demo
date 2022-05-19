# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

SUMMARY = "Creates an 'CASSINI_TEST_ACCOUNT' account used for running CASSINI \
           runtime integration tests and installs common include files."
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"

# Default values, used only if 'meta-cassini-distro/conf/distro/cassini.conf'
# is skipped.
CASSINI_TEST_ACCOUNT ??= "test"
CASSINI_ADMIN_GROUP ??= "sudo"

# Comma separated list of groups for 'CASSINI_TEST_ACCOUNT' user
CASSINI_TEST_GROUPS = "${CASSINI_ADMIN_GROUP}"

inherit allarch useradd
require runtime-integration-tests.inc

USERADD_PACKAGES = "${PN}"
USERADD_PARAM:${PN} = "--create-home \
                       --password '' \
                       --groups ${CASSINI_TEST_GROUPS} \
                       --user-group ${CASSINI_TEST_ACCOUNT};"

OVERRIDES:append = "${CASSINI_OVERRIDES}"
RDEPENDS:${PN}:append:cassini-security = " expect"
DEPENDS:append = " gettext-native"

SRC_URI = "file://integration-tests-common-funcs.sh \
           file://login-console-funcs.expect \
           file://run-command.expect"

do_configure[noexec] = "1"
do_compile[noexec] = "1"

do_install() {
    install -d "${D}/${TEST_COMMON_DIR}"

    envsubst '$TEST_RUNTIME_DIR' < "${WORKDIR}/integration-tests-common-funcs.sh" \
        > "${D}/${TEST_COMMON_DIR}/integration-tests-common-funcs.sh"

    install --mode="644" "${WORKDIR}/login-console-funcs.expect" \
        "${D}/${TEST_COMMON_DIR}"

    envsubst '$TEST_COMMON_DIR' < "${WORKDIR}/run-command.expect" \
        > "${D}/${TEST_COMMON_DIR}/run-command.expect"
}

FILES:${PN} += "${TEST_COMMON_DIR}"
