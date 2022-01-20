# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# To add more instances of a VM based on this recipe with different HOSTNAMEs
# and storage sizes, set the desired instances number in EWAOL_VM_INSTANCES
# variable  and include all required VM settings to local.conf,
# like:
# EWAOL_VM_INSTANCES = "2"                 # number of VM instances
# EWAOL_VM2_ROOTFS_EXTRA_SPACE = "100000"  # additional 100MB of storage space
# EWAOL_VM2_MEMORY_SIZE = "1024"           # sets VM memory to 1024MB
# EWAOL_VM2_NUMBER_OF_CPUS = "2"           # sets number of vcpus to 2
# Currently the HOSTNAME is being set to "${EWAOL_VM_HOSTNAME}${IDX}", where
# EWAOL_VM_HOSTNAME is common for all VMs, and ${IDX} is set according to the
# VMs instance number, 1 for the first, 2 for the second, etc.
# All of the VMs share the same Kernel image.

inherit ewaol_vm_config

inherit features_check
REQUIRED_DISTRO_FEATURES += "ewaol-virtualization"

IMAGE_FSTYPES = "wic.qcow2"

IMAGE_BASENAME = "ewaol-vm1-image"
EWAOL_VM_IMAGE_NAME = "${EWAOL_VM_IMAGE_BASENAME}-${MACHINE}${IMAGE_VERSION_SUFFIX}"

WKS_FILE = "ewaol-vm.wks"
WIC_CREATE_EXTRA_ARGS = " --vars ${IMGDEPLOYDIR} -e ${EWAOL_VM_IMAGE_BASENAME}"

do_ewaol_vm_image_wic () {
    # generate each vm with custom HOSTNAME
    # make sure that hostname substitution won't fail by appending
    # #EWAOL_VM_HOSTNAME to the line ending
    sed -i "s/127.0.1.1 ${MACHINE}/127.0.1.1 ${MACHINE} #EWAOL_VM_HOSTNAME/g" \
       ${IMAGE_ROOTFS}/${sysconfdir}/hosts

    # make sure that old images will not be included into Host rootfs:
    rm -fv ${IMGDEPLOYDIR}/*${MACHINE}*.wic.qcow2

    # generate images in reverced order to simplify the for loop
    for ewaol_vm_instance in $(seq 1 ${EWAOL_VM_INSTANCES})
    do
        bbdebug 1 "Generating VM ${ewaol_vm_instance}"
        export VM_HOSTNAME=$(grep -oP "(?<=EWAOL_VM${ewaol_vm_instance}_HOSTNAME=\")[^\"]*" \
                             ${IMGDEPLOYDIR}/${EWAOL_VM_IMAGE_BASENAME}.env)

        echo ${VM_HOSTNAME} > ${IMAGE_ROOTFS}/${sysconfdir}/hostname
        sed -i "s/127.0.1.1.*#EWAOL_VM_HOSTNAME/127.0.1.1 ${VM_HOSTNAME} #EWAOL_VM_HOSTNAME/g"\
           ${IMAGE_ROOTFS}/${sysconfdir}/hosts

        do_image_wic
    done
}

CONVERSION_CMD:qcow2 = "qemu-img convert -O qcow2 \
                            ${IMAGE_NAME}${IMAGE_NAME_SUFFIX}.${type} \
                            ${EWAOL_VM_IMAGE_NAME}${IMAGE_NAME_SUFFIX}.${type}.qcow2"

python () {
    d.setVarFlags('do_ewaol_vm_image_wic', d.getVarFlags('do_image_wic'))
    bb.build.addtask('do_ewaol_vm_image_wic', 'do_image_complete', None, d)
    bb.build.deltask('do_image_wic', d)
}

#
# Create symlinks to the newly created VM images
# Based on create_symlinks() from images.bbclass
#
python create_symlinks() {

    deploy_dir = d.getVar('IMGDEPLOYDIR')
    manifest_name = d.getVar('IMAGE_MANIFEST')
    taskname = d.getVar("BB_CURRENTTASK")
    subimages = (d.getVarFlag("do_" + taskname, 'subimages', False) or "").split()
    imgsuffix = d.getVarFlag("do_" + taskname, 'imgsuffix') or d.expand("${IMAGE_NAME_SUFFIX}.")
    vm_instances = d.getVar('EWAOL_VM_INSTANCES')

    if not vm_instances:
        return

    for idx in range(1, int(vm_instances) + 1):
        link_name = f"ewaol-vm{idx}-image-{d.getVar('MACHINE')}"
        img_name = link_name + d.getVar('IMAGE_VERSION_SUFFIX')
        for type in subimages:
            dst = os.path.join(deploy_dir, link_name + "." + type)
            src = img_name + imgsuffix + type
            if os.path.exists(os.path.join(deploy_dir, src)):
                bb.note("Creating symlink: %s -> %s" % (dst, src))
                if os.path.islink(dst):
                    os.remove(dst)
                os.symlink(src, dst)
            else:
                bb.note("Skipping symlink, source does not exist: %s -> %s" % (dst, src))
}

#
# Write environment variables used by wic
# to <tmp>/sysroots/<machine>/imgdata/<EWAOL_VM_IMAGE_BASENAME>.env
# Based on do_rootfs_wicenv from image_types_wic.bbclass
#
python do_rootfs_wicenv () {
    wicvars = d.getVar('WICVARS')
    if not wicvars:
        return

    stdir = d.getVar('STAGING_DIR')
    outdir = os.path.join(stdir, d.getVar('MACHINE'), 'imgdata')
    depdir = d.getVar('IMGDEPLOYDIR')

    bb.utils.remove(f"{outdir}/*.env", False, True)
    bb.utils.remove(f"{depdir}/*.env", False, True)

    bb.utils.mkdirhier(outdir)
    vm_instances = d.getVar('EWAOL_VM_INSTANCES')

    if not vm_instances:
        return

    import re

    for idx in range(1, int(vm_instances) + 1):
        link_name = f"ewaol-vm{idx}-image"
        with open(os.path.join(outdir, link_name) + '.env', 'w') as envf:
            for var in wicvars.split():
                value = d.getVar(var)
                if re.match(rf"EWAOL_VM[^\D{idx}]_.*", var):
                    continue
                if var == 'ROOTFS_SIZE':
                    extra = d.getVar(f"EWAOL_VM{idx}_ROOTFS_EXTRA_SPACE")
                    value = str(int(value) + int(extra))
                if value:
                    envf.write('%s="%s"\n' % (var, value.strip()))
        envf.close()
        # Copy .env file to deploy directory for later use with stand alone wic
        bb.utils.copyfile(os.path.join(outdir, link_name) + '.env', os.path.join(depdir, link_name) + '.env')
}
