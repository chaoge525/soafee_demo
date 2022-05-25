# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

CASSINI_PROCPS_INC := "\
${@ "${BPN}-cassini.inc" \
    if (d.getVar('DISTRO_FEATURES').find("sdk") == -1) \
    else "" }"

require ${CASSINI_PROCPS_INC}
