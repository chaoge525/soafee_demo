# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "Creates an 'EWAOL_TEST_ACCOUNT' account used for running EWAOL \
           runtime integration tests and installs common include files."
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"

# Default values, used only if 'meta-ewaol-distro/conf/distro/ewaol.conf'
# is skipped.
EWAOL_TEST_ACCOUNT ??= "test"
EWAOL_ADMIN_GROUP ??= "sudo"

# Comma separated list of groups for 'EWAOL_TEST_ACCOUNT' user
EWAOL_TEST_GROUPS = "${EWAOL_ADMIN_GROUP}"

inherit allarch useradd
require runtime-integration-tests.inc

USERADD_PACKAGES = "${PN}"
USERADD_PARAM:${PN} = "--create-home \
                       --password '' \
                       --groups ${EWAOL_TEST_GROUPS} \
                       --user-group ${EWAOL_TEST_ACCOUNT};"

OVERRIDES:append = "${EWAOL_OVERRIDES}"
RDEPENDS:${PN}:append:ewaol-virtualization = " expect"
RDEPENDS:${PN}:append:ewaol-security = " expect"
DEPENDS:append = " gettext-native"

SRC_URI = "file://integration-tests-common-funcs.sh \
           file://login-console-funcs.expect \
           file://run-command.expect"

SRC_URI:append:ewaol-virtualization = " \
    file://integration-tests-common-virtual-funcs.sh \
    "

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

do_install:append:ewaol-virtualization() {

    envsubst '$TEST_COMMON_DIR' \
        < "${WORKDIR}/integration-tests-common-virtual-funcs.sh" \
        > "${D}/${TEST_COMMON_DIR}/integration-tests-common-virtual-funcs.sh"

}

FILES:${PN} += "${TEST_COMMON_DIR}"
