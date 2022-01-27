# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

RRECOMMENDS:${PN}:append:ewaol = " kernel-module-ip-vs \
                                   kernel-module-ip-vs-rr \
                                   kernel-module-ip-vs-wrr \
                                   kernel-module-ip-vs-sh \
                                 "
