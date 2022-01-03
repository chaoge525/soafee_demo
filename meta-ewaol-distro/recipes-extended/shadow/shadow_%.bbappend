# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

do_install:append:ewaol() {

    # Make sure that users cannot access to each other HOME directory
    sed -i 's/#HOME_MODE/HOME_MODE/g' ${D}${sysconfdir}/login.defs
}
