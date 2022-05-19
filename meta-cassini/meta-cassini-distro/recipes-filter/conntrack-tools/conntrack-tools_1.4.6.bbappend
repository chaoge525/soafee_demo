# Based on: http://cgit.openembedded.org/meta-openembedded/tree/meta-networking/recipes-filter/conntrack-tools/conntrack-tools_1.4.6.bb?id=71e87a5dbc4a09544e0cf2ad42e50064240d73f3
# In open-source project: https://git.openembedded.org/meta-openembedded
#
# Original file: Copyright (c) 2022 Kai Kang <kai.kang@windriver.com>
# Modifications: Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

# Fix based on http://cgit.openembedded.org/meta-openembedded/commit/?id=71e87a5dbc4a09544e0cf2ad42e50064240d73f3
pkg_postinst:${PN}:cassini () {
    setcap cap_net_admin+ep "$D/${sbindir}/conntrack"
}
