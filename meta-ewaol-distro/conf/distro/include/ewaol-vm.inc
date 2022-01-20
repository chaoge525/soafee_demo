# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Guest multiconfig build configuration file basename without the ".conf"
# suffix.
EWAOL_VM_MC ?= "${@ 'ewaol-vm' if d.getVar('BUILD_EWAOL_VM') == 'True' else ''}"

EWAOL_VM_HOSTNAME ?= "ewaol-vm"

# The variable 'ewaol_vm_instance' remains empty in each recipe
# until it is set as a for loop iterator in particular task.
EWAOL_VM_IMAGE_BASENAME = "ewaol-vm${ewaol_vm_instance}-image"
EWAOL_VM_IMAGE_RECIPE ?= "ewaol-vm-image"
EWAOL_VM_KERNEL_IMAGETYPE ?= "Image"
EWAOL_VM_MACHINE ?= "generic-arm64"
EWAOL_VM_TMPDIR = "${TOPDIR}/tmp_${EWAOL_VM_MC}"

EWAOL_VM_MEMORY_SIZE_DEFAULT = "6144"
EWAOL_VM_ROOTFS_EXTRA_SPACE_DEFAULT = "0"
EWAOL_VM_NUMBER_OF_CPUS_DEFAULT = "4"

EWAOL_VM_INSTANCES ?= "1"

BUILD_EWAOL_VM = "${@ 'False' if (not d.getVar('EWAOL_VM_INSTANCES') \
                                or int(d.getVar('EWAOL_VM_INSTANCES')) < 1) \
                              else 'True'}"

PREBUILT_VM_INSTANCES ?= "0"

INCLUDE_PREBUILT_VM = "${@ 'False' if (not d.getVar('PREBUILT_VM_INSTANCES') \
                                or int(d.getVar('PREBUILT_VM_INSTANCES')) < 1) \
                              else 'True'}"
