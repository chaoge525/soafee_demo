# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

INCLUDE_FOR = "${EWAOL_DISTRO_FEATURES}"
INCLUDE_FOR:remove = "ewaol-sdk"

require ${@bb.utils.contains_any('DISTRO_FEATURES', \
                                 d.getVar("INCLUDE_FOR"), \
                                 '${BPN}-ewaol.inc', '', d)}
