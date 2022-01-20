# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Guest multiconfig build configuration file basename without the ".conf"
# suffix.
EWAOL_VM_MC ?= "ewaol-vm"

EWAOL_VM_HOSTNAME ?= "ewaol-vm"
EWAOL_VM_IMAGE_RECIPE ?= "ewaol-vm-image"
EWAOL_VM_MACHINE ?= "generic-arm64"
EWAOL_VM_TMPDIR = "${TOPDIR}/tmp_${EWAOL_VM_MC}"

EWAOL_VM_MEMORY_SIZE ?= "6144"
EWAOL_VM_NUMBER_OF_CPUS ?= "4"
