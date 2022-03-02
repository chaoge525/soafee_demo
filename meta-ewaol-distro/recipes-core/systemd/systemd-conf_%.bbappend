# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Include systemd-conf_ewaol-virtualization.inc only for the Control VM

require ${@bb.utils.contains('DISTRO_FEATURES', 'ewaol-virtualization', \
               bb.utils.contains('BB_CURRENT_MC', 'ewaol-guest-vm', '', \
                   'systemd-conf_ewaol-virtualization.inc', d), '', d)}
