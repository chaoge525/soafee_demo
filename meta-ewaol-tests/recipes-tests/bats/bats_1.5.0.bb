# Based on: https://cgit.openembedded.org/meta-openembedded/tree/meta-oe/recipes-test/bats/bats_1.5.0.bb?h=master&id=f16f628d1f8c2ca37df10b2d84dea05d6b9ebab1
# In open-source project: https://git.openembedded.org/meta-openembedded
#
# Original file: Copyright (c) 2022 wangmy <wangmy@fujitsu.com>
# Modifications: Copyright (c) 2022 Arm Limited and Contributors. All rights reserved.
#
# SPDX-License-Identifier: MIT

SUMMARY = "Bash Automated Testing System"
DESCRIPTION = "Bats is a TAP-compliant testing framework for Bash. It \
provides a simple way to verify that the UNIX programs you write behave as expected."
AUTHOR = "Sam Stephenson & bats-core organization"
HOMEPAGE = "https://github.com/bats-core/bats-core"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE.md;md5=2970203aedf9e829edb96a137a4fe81b"

SRC_URI = "git://github.com/bats-core/bats-core.git;branch=master;protocol=https"
# v1.5.0
SRCREV = "99d64eb017abcd6a766dd0d354e625526da69cb3"

S = "${WORKDIR}/git"

do_configure:prepend() {
	sed -i 's:\$BATS_ROOT/lib:\$BATS_ROOT/${baselib}:g' ${S}/libexec/bats-core/bats
	sed -i 's:\$BATS_ROOT/lib:\$BATS_ROOT/${baselib}:g' ${S}/libexec/bats-core/bats-exec-file
	sed -i 's:\$BATS_ROOT/lib:\$BATS_ROOT/${baselib}:g' ${S}/libexec/bats-core/bats-exec-test
}

do_install() {
	# Just a bunch of bash scripts to install
	${S}/install.sh ${D}${prefix} ${baselib}
}

RDEPENDS:${PN} = "bash"
FILES:${PN} += "${libdir}/bats-core/*"

PACKAGECONFIG ??= "pretty"
PACKAGECONFIG[pretty] = ",,,ncurses"

inherit features_check
REQUIRED_DISTRO_FEATURES = "ewaol-test"
