# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Config specifc to the ewaol-security distro feature, enabled using
# DISTRO_FEATURES

EWAOL_OVERRIDES:append = ":ewaol-security"

DISTRO_FEATURES:append = " cassini-security"

# With `cassini-security` distro feature, we do not this here because
# `CASSINI_SECURITY_UMASK` is defined in
# `meta-cassini/meta-cassini-distro/conf/distro/include/cassini-security.inc`.
# However, meta-ewaol-tests layer is still using `EWAOL_SECURITY_UMASK` which is
# not set. Therefore, temporarily set `EWAOL_SECURITY_UMASK` here, remove it when
# meta-ewaol-tests extends meta-cassini-tests.
EWAOL_SECURITY_UMASK = "0027"
