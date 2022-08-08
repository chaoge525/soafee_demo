# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "EWAOL Virtualization image, providing a Control VM as Xen Dom0."

require ewaol-image-core.inc

inherit features_check
REQUIRED_DISTRO_FEATURES = "ewaol-virtualization"
CONFLICT_DISTRO_FEATURES = "ewaol-baremetal"

EXTRA_IMAGEDEPENDS:append = " xen"

# Calculate sum of all Guest VMs rootfs sizes, to increase the Control VM rootfs
# size accordingly
python compute_summed_guest_vms_rootfs_sizes() {

    if d.getVar('BB_CURRENT_MC') == 'ewaol-guest-vm':
        return

    guest_vm_instances = d.getVar("EWAOL_GUEST_VM_INSTANCES")
    guest_vm_deploy_dir = d.getVar("EWAOL_GUEST_VM_DEPLOY_DIR")
    guest_vm_image_basename = d.getVar("EWAOL_GUEST_VM_IMAGE_BASENAME")

    summed_guest_vms_rootfs_sizes = 0

    for idx in range(1, int(guest_vm_instances) + 1):

        guest_vm_image_name = guest_vm_image_basename.replace(
                                  "${ewaol_guest_vm_instance}",
                                  str(idx))

        with open(f"{guest_vm_deploy_dir}/{guest_vm_image_name}.env") as f:
            for line in f:

                key = line.split("=")[0]
                if key == "ROOTFS_SIZE":
                    value = line.split("=")[1].strip().strip("\"")
                    summed_guest_vms_rootfs_sizes += int(value)
                    bb.debug(1, f"Found Guest VM{idx} ROOTFS_SIZE: {value}."
                                " The Control VM rootfs size will be increased"
                                f" by {value} to account for this Guest VM.")
                    break

    bb.debug(1, "Sum of all Guest VMs rootfs sizes:"
                f"{summed_guest_vms_rootfs_sizes}")

    control_vm_rootfs_extra_space = d.getVar("IMAGE_ROOTFS_EXTRA_SPACE")
    updated_extra_space = (f"{control_vm_rootfs_extra_space} +"
                           f" {summed_guest_vms_rootfs_sizes}")

    d.setVar("IMAGE_ROOTFS_EXTRA_SPACE", updated_extra_space)

    bb.debug(1, "The Control VM's IMAGE_ROOTFS_EXTRA_SPACE was set to:"
                f" '{updated_extra_space}'")
}

do_image_wic[prefuncs] =. "compute_summed_guest_vms_rootfs_sizes "
do_rootfs_wicenv[prefuncs] =. "compute_summed_guest_vms_rootfs_sizes "

# Ensure the Guest VM wicenvs which this package depends on are created
# (even if the Guest VM package can be retrieved from cache)
do_image_wic[mcdepends] += " \
    ${@ ('mc::${EWAOL_GUEST_VM_MC}:${EWAOL_GUEST_VM_IMAGE_RECIPE}:do_rootfs_wicenv' \
         if d.getVar('BUILD_EWAOL_GUEST_VM') == 'True' \
         else '') } \
    "

EWAOL_CONTROL_VM_ROOTFS_EXTRA_SPACE ?= "0"

IMAGE_ROOTFS_EXTRA_SPACE:append = " \
    ${@ ' + ${EWAOL_CONTROL_VM_ROOTFS_EXTRA_SPACE}' \
    if '${EWAOL_CONTROL_VM_ROOTFS_EXTRA_SPACE}' \
    else ''} \
    "

IMAGE_INSTALL:append = " \
    ${@ 'ewaol-guest-vm-package' if d.getVar('BUILD_EWAOL_GUEST_VM') == 'True' else ''} \
    ${@ 'prebuilt-guest-vm-package' if d.getVar('INCLUDE_PREBUILT_GUEST_VM') == 'True' else ''} \
    kernel-module-xen-blkback \
    kernel-module-xen-gntalloc \
    kernel-module-xen-gntdev \
    kernel-module-xen-netback \
    qemu-keymaps \
    qemu-system-i386 \
    xen-tools \
    "
