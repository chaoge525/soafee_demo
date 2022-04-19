# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

RRECOMMENDS:${PN}:append:cassini = " kernel-module-ip-vs \
                                   kernel-module-ip-vs-rr \
                                   kernel-module-ip-vs-wrr \
                                   kernel-module-ip-vs-sh \
                                 "
