# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL Xen VM (Guest) Images with common packages"

require ewaol-image-core.inc

inherit ewaol_vm_image

inherit features_check
REQUIRED_DISTRO_FEATURES += "ewaol-virtualization"

IMAGE_INSTALL:remove = "k3s-server"
IMAGE_INSTALL += "k3s-agent"

# These integration tests should only execute on the Host, so make them
# unavailable on the VM
IMAGE_INSTALL:remove = "${@bb.utils.contains('DISTRO_FEATURES', \
    'ewaol-test', \
    'k3s-integration-tests-ptest virtualization-integration-tests-ptest', \
    '', d)}"
