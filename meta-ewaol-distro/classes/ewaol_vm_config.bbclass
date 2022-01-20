# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# This class adds configuration parameters for EWAOL VMs. Number of VMs
# instances is defined in EWAOL_VM_INSTANCES. List of configurable parameters
# (${IDX} is the VM instance, e.g. 2):
#   (*) EWAOL_VM${IDX}_HOSTNAME
#   (*) EWAOL_VM${IDX}_MEMORY_SIZE
#   (*) EWAOL_VM${IDX}_ROOTFS_EXTRA_SPACE
#   (*) EWAOL_VM${IDX}_NUMBER_OF_CPUS
# If no custom value for any of the above parameters is provided, the default
# value is used. Default parameters are defined in:
# 'meta-ewaol-distro/conf/distro/include/ewaol-vm.inc'

python () {
    vm_instances = d.getVar("EWAOL_VM_INSTANCES")

    if d.getVar('BUILD_EWAOL_VM') != 'True':
        raise bb.parse.SkipRecipe("BUILD_EWAOL_VM must be 'True' to proceed!")

    for idx in range(1, int(vm_instances) + 1):
        for var_sufix in ["_HOSTNAME", "_MEMORY_SIZE", "_ROOTFS_EXTRA_SPACE", "_NUMBER_OF_CPUS"]:
            var = f"EWAOL_VM{idx}{var_sufix}"
            value = d.getVar(var)
            if not value:
                if var_sufix == "_HOSTNAME":
                    value = f"{d.getVar('EWAOL_VM_HOSTNAME')}{idx}"
                else:
                    value = d.getVar(f"EWAOL_VM{var_sufix}_DEFAULT")
                d.setVar(var, value)
            d.appendVar('WICVARS', f"{var} ")
    d.appendVar('WICVARS', "EWAOL_VM_INSTANCES ")
}
