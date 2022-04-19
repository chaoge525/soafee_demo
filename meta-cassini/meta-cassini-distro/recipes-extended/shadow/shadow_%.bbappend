# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

OVERRIDES:append = "${CASSINI_OVERRIDES}"

do_install:append:cassini() {

    # Make sure that users cannot access to each other HOME directory
    sed -i 's/#HOME_MODE/HOME_MODE/g' ${D}${sysconfdir}/login.defs
}

CASSINI_SECURITY_UMASK ??= "0027"

do_install:append:cassini-security() {
    # set more secure UMASK
    sed -i "s/UMASK.*/UMASK\t\t${CASSINI_SECURITY_UMASK}/g" \
        ${D}${sysconfdir}/login.defs
}
