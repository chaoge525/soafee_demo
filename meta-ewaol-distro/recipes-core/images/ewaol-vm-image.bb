# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL Xen VM (Guest) Image with common packages"

require ewaol-image-core.inc

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

IMAGE_FSTYPES = "wic.qcow2"

EWAOL_VM_ROOTFS_EXTRA_SPACE ?= ""
IMAGE_ROOTFS_EXTRA_SPACE:append = "${@ ' + ${EWAOL_VM_ROOTFS_EXTRA_SPACE}' \
                                      if '${EWAOL_VM_ROOTFS_EXTRA_SPACE}' \
                                      else ''}"

WKS_FILE = "ewaol-vm.wks"
vm_hostname ?= "${EWAOL_VM_HOSTNAME}"

vm_image_tweaks() {

   # replace default guest HOSTNAME with a VM specific one
   echo ${vm_hostname} > ${IMAGE_ROOTFS}/${sysconfdir}/hostname
   sed -i "s/127.0.1.1 ${MACHINE}/127.0.1.1 ${vm_hostname}/g" \
       ${IMAGE_ROOTFS}/${sysconfdir}/hosts
}

ROOTFS_POSTPROCESS_COMMAND += "vm_image_tweaks; "
