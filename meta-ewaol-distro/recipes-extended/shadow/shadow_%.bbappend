# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

OVERRIDES:append = "${EWAOL_OVERRIDES}"

do_install:append:ewaol() {

    # Make sure that users cannot access to each other HOME directory
    sed -i 's/#HOME_MODE/HOME_MODE/g' ${D}${sysconfdir}/login.defs
}

EWAOL_SECURITY_UMASK ??= "0027"

do_install:append:ewaol-security() {
    # set more secure UMASK
    sed -i "s/UMASK.*/UMASK\t\t${EWAOL_SECURITY_UMASK}/g" \
        ${D}${sysconfdir}/login.defs
}
