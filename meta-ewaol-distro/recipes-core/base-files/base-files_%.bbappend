# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend:ewaol := "${THISDIR}/files:"

SRC_URI:append:ewaol = " file://ewaol_profile.sh"

do_install:append:ewaol() {
    # PS1 is set inside ewaol_profile.sh
    sed -i '/PS1/d' ${D}${sysconfdir}/skel/.bashrc

    install -d ${D}${sysconfdir}/profile.d
    install -m 0644 ${WORKDIR}/ewaol_profile.sh ${D}${sysconfdir}/profile.d/ewaol_profile.sh
}
