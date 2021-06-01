# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS_prepend := "${@bb.utils.contains('DISTRO_FEATURES', \
                                                 'ewaol-test', \
                                                 '${THISDIR}/files:', \
                                                 '', \
                                                 d)}"

# As Bats requires the nl utility, configure CONFIG_NL=y for busybox if we are
# using Bats
SRC_URI_append := "${@bb.utils.contains('DISTRO_FEATURES', \
                                        'ewaol-test', \
                                        ' file://nl.cfg', \
                                        '', \
                                        d)}"
