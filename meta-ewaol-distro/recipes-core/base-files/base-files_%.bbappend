# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend:ewaol := "${THISDIR}/files:"

OVERRIDES:append = "${EWAOL_OVERRIDES}"

SRC_URI:append:ewaol = " file://ewaol_profile.sh"

EWAOL_SECURITY_UMASK ??= "0027"

do_install:append:ewaol() {
    # PS1 is set inside ewaol_profile.sh
    sed -i '/PS1/d' ${D}${sysconfdir}/skel/.bashrc

    install -d ${D}${sysconfdir}/profile.d
    install -m 0644 ${WORKDIR}/ewaol_profile.sh \
        ${D}${sysconfdir}/profile.d/ewaol_profile.sh
}

do_install:append:ewaol-security() {
    # set more secure umask
    sed -i "s/umask.*/umask ${EWAOL_SECURITY_UMASK}/g" \
        ${D}${sysconfdir}/profile

    sed -i "s/umask.*/umask ${EWAOL_SECURITY_UMASK}/g" \
        ${D}${sysconfdir}/skel/.bashrc
}
