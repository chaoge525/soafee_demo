# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# This class adds configuration parameters for EWAOL Guest VMs.
#
# The number of Guest VMs instances is defined in EWAOL_GUEST_VM_INSTANCES. Each
# Guest VM can then be independently configured via Bitbake variables that
# reference the Guest VM's integer instance index, from 1 to the value of
# EWAOL_GUEST_VM_INSTANCES, inclusive. The available variables are as follows,
# where ${IDX} corresponds to a target Guest VM's integer instance index:
#
#   (*) EWAOL_GUEST VM${IDX}_HOSTNAME
#   (*) EWAOL_GUEST_VM${IDX}_MEMORY_SIZE
#   (*) EWAOL_GUEST_VM${IDX}_ROOTFS_EXTRA_SPACE
#   (*) EWAOL_GUEST_VM${IDX}_NUMBER_OF_CPUS
#
# If no custom value for any of the above parameters is provided, the default
# value is used. Default parameters are defined in:
# 'meta-ewaol-distro/conf/distro/include/ewaol-guest-vm.inc'

python () {
    guest_vm_instances = d.getVar("EWAOL_GUEST_VM_INSTANCES")

    if d.getVar('BUILD_EWAOL_GUEST_VM') != 'True':
        raise bb.parse.SkipRecipe("BUILD_EWAOL_GUEST_VM must be 'True' to proceed!")

    for idx in range(1, int(guest_vm_instances) + 1):
        for var_sufix in ["_HOSTNAME", "_MEMORY_SIZE", "_ROOTFS_EXTRA_SPACE", "_NUMBER_OF_CPUS"]:
            var = f"EWAOL_GUEST_VM{idx}{var_sufix}"
            value = d.getVar(var)
            if not value:
                if var_sufix == "_HOSTNAME":
                    value = f"{d.getVar('EWAOL_GUEST_VM_HOSTNAME')}{idx}"
                else:
                    value = d.getVar(f"EWAOL_GUEST_VM{var_sufix}_DEFAULT")
                d.setVar(var, value)
            d.appendVar('WICVARS', f"{var} ")
    d.appendVar('WICVARS', "EWAOL_GUEST_VM_INSTANCES ")
}
