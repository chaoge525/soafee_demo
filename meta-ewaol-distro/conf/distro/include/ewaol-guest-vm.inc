# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Guest multiconfig build configuration file basename without the ".conf"
# suffix.
EWAOL_GUEST_VM_MC ?= "${@ 'ewaol-guest-vm' if d.getVar('BUILD_EWAOL_GUEST_VM') == 'True' else ''}"

# By default, a Guest VM's hostname will be "${EWAOL_GUEST_VM_HOSTNAME}${IDX}"
# where EWAOL_GUEST_VM_HOSTNAME is common for all VMs, and ${IDX} is the Guest
# VM's integer instance index.
EWAOL_GUEST_VM_HOSTNAME ?= "ewaol-guest-vm"

# The variable 'ewaol_guest_vm_instance' remains empty in each recipe
# until it is set as a for-loop iterator in particular task.
EWAOL_GUEST_VM_IMAGE_BASENAME = "ewaol-guest-vm${ewaol_guest_vm_instance}-image"
EWAOL_GUEST_VM_IMAGE_RECIPE ?= "ewaol-guest-vm-image"
EWAOL_GUEST_VM_KERNEL_IMAGETYPE ?= "Image"
EWAOL_GUEST_VM_MACHINE ?= "generic-arm64"
EWAOL_GUEST_VM_TMPDIR = "${TOPDIR}/tmp_${EWAOL_GUEST_VM_MC}"

EWAOL_GUEST_VM_MEMORY_SIZE_DEFAULT = "6144"
EWAOL_GUEST_VM_ROOTFS_EXTRA_SPACE_DEFAULT = "0"
EWAOL_GUEST_VM_NUMBER_OF_CPUS_DEFAULT = "4"

EWAOL_GUEST_VM_INSTANCES ?= "1"

BUILD_EWAOL_GUEST_VM = "${@ \
    'False' if (not d.getVar('EWAOL_GUEST_VM_INSTANCES') \
                or int(d.getVar('EWAOL_GUEST_VM_INSTANCES')) < 1) \
            else 'True'}"

PREBUILT_GUEST_VM_INSTANCES ?= "0"

INCLUDE_PREBUILT_GUEST_VM = "${@ \
    'False' if (not d.getVar('PREBUILT_GUEST_VM_INSTANCES') \
                or int(d.getVar('PREBUILT_GUEST_VM_INSTANCES')) < 1) \
            else 'True'}"
