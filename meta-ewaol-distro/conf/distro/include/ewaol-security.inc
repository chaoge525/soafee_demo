# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Config specifc to the ewaol-security distro feature, enabled using
# DISTRO_FEATURES

# Force password change after user first log in for:
# 'EWAOL_USER_ACCOUNT', 'EWAOL_ADMIN_ACCOUNT' & root
EXTRA_USERS_PARAMS:append = "\
    usermod -p '' root; \
    passwd-expire ${EWAOL_ADMIN_ACCOUNT}; \
    passwd-expire ${EWAOL_USER_ACCOUNT}; \
    passwd-expire root; \
    ${@bb.utils.contains('DISTRO_FEATURES', 'ewaol-test', \
                        'passwd-expire ${EWAOL_TEST_ACCOUNT};', '', d)} \
    "
IMAGE_FEATURES:remove = "empty-root-password debug-tweaks"

# Allow users to ssh on first ewaol image boot,
# if users have empty password preset
IMAGE_FEATURES:append = " allow-empty-password"

DISTRO_FEATURES:append = " seccomp"

KERNEL_FEATURES:append = " features/security/security.scc"

# Make sure that libcap[-ng] is enabled for all below packages:
# meta-openembedded/meta-networking
PACKAGECONFIG:append:pn-freeradius = " libcap"
PACKAGECONFIG:append:pn-libtalloc = " libcap"
PACKAGECONFIG:append:pn-libtevent = " libcap"
PACKAGECONFIG:append:pn-libldb = " libcap"
PACKAGECONFIG:append:pn-chrony = " libcap"
PACKAGECONFIG:append:pn-libtdb = " libcap"
PACKAGECONFIG:append:pn-wireshark = " libcap"
PACKAGECONFIG:append:pn-proftpd = " cap"
PACKAGECONFIG:append:pn-quagga = " cap"
PACKAGECONFIG:append:pn-cifs-utils = " cap"
PACKAGECONFIG:append:pn-ntp = " cap"
PACKAGECONFIG:append:pn-libgcrypt = " capabilities"
PACKAGECONFIG:append:pn-tcpdump = " libcap-ng"

# meta-openembedded/meta-oe
PACKAGECONFIG:append:pn-pax-utils = " libcap"
PACKAGECONFIG:append:pn-syslog-ng = " linux-caps"
PACKAGECONFIG:append:pn-smartmontools = " libcap-ng"

# poky/meta
PACKAGECONFIG:append:pn-iputils = " libcap"
PACKAGECONFIG:append:pn-pinentry = " libcap"
PACKAGECONFIG:append:pn-perf = " cap"
PACKAGECONFIG:append:pn-gstreamer1.0 = " setcap"
PACKAGECONFIG:append:pn-qemu = " libcap-ng"

# meta-virtualization
PACKAGECONFIG:append:pn-libvirt = " libcap-ng"
PACKAGECONFIG:append:pn-irqbalance = " libcap-ng"
PACKAGECONFIG:append:pn-openvswitch = " libcap-ng"
