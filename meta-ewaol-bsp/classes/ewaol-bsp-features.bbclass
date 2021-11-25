# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Used to apply configs for machine specific features of the EWAOL distro,
# based on the contents of DISTRO_FEATURES and selected MACHINE.

# Require inc file for ewaol-virtualization DISTRO_FEATURE
require ${@bb.utils.contains('DISTRO_FEATURES', \
                             'ewaol-virtualization', \
                             'conf/distro/include/ewaol-bsp.inc', '', d)}
