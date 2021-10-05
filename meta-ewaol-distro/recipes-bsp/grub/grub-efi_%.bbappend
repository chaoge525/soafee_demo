# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

GRUB_BUILDIN:append:ewaol = "${@bb.utils.contains('DISTRO_FEATURES', 'xen', ' xen_boot', '', d)}"
