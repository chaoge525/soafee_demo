# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend := "${@bb.utils.contains('DISTRO_FEATURES', \
                                                 'cassini-test', \
                                                 '${THISDIR}/files:', \
                                                 '', \
                                                 d)}"

# As Bats requires the nl utility, configure CONFIG_NL=y for busybox if we are
# using Bats
SRC_URI:append := "${@bb.utils.contains('DISTRO_FEATURES', \
                                        'cassini-test', \
                                        ' file://nl.cfg', \
                                        '', \
                                        d)}"
