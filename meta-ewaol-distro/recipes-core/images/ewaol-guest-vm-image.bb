# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL Guest VM image with common packages, providing Xen DomU"

require ewaol-image-core.inc

inherit ewaol_guest_vm_image

inherit features_check
REQUIRED_DISTRO_FEATURES += "ewaol-virtualization"

IMAGE_INSTALL:remove = "k3s-server"
IMAGE_INSTALL += "k3s-agent"

# These integration tests should only execute on the Control VM, so make them
# unavailable on the Guest VM
IMAGE_INSTALL:remove = "${@bb.utils.contains('DISTRO_FEATURES', \
    'ewaol-test', \
    'k3s-integration-tests-ptest virtualization-integration-tests-ptest', \
    '', d)}"
