# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend:cassini := "${THISDIR}/files:"

OVERRIDES:append = "${CASSINI_OVERRIDES}"

SRC_URI:append:cassini = " file://cassini_profile.sh"

CASSINI_SECURITY_UMASK ??= "0027"

do_install:append:cassini() {
    # PS1 is set inside cassini_profile.sh
    sed -i '/PS1/d' ${D}${sysconfdir}/skel/.bashrc

    install -d ${D}${sysconfdir}/profile.d
    install -m 0644 ${WORKDIR}/cassini_profile.sh \
        ${D}${sysconfdir}/profile.d/cassini_profile.sh
}

do_install:append:cassini-security() {
    # set more secure umask
    sed -i "s/umask.*/umask ${CASSINI_SECURITY_UMASK}/g" \
        ${D}${sysconfdir}/profile

    sed -i "s/umask.*/umask ${CASSINI_SECURITY_UMASK}/g" \
        ${D}${sysconfdir}/skel/.bashrc
}
