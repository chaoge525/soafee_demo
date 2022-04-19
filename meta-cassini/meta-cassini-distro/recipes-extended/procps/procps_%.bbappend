# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

INCLUDE_FOR = "${CASSINI_DISTRO_FEATURES}"
INCLUDE_FOR:remove = "cassini-sdk"

require ${@bb.utils.contains_any('DISTRO_FEATURES', \
                                 d.getVar("INCLUDE_FOR"), \
                                 '${BPN}-cassini.inc', '', d)}
