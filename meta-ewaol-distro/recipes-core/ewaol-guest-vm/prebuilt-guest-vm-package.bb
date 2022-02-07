# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# A number of prebuilt Guest VMs can be added to the virtualization image,
# according to the value configured for the PREBUILT_GUEST_VM_INSTANCES
# variable. By default the variable is set to 0, and no prebuilt Guest VMs are
# included.
# Each prebuilt Guest VM can be defined using Bitbake variables which share a
# reference to a unique integer instance index (represented here as ${IDX}) from
# 1 to PREBUILT_GUEST_VM_INSTANCES, inclusive:
#
#   (*) PREBUILT_GUEST_VM${IDX}_CFG_SRC
#       - Path to the Guest VM's Xen Domain configuration file
#   (*) PREBUILT_GUEST_VM${IDX}_KERNEL_SRC
#       - Path to the Kernel image to use for the Guest VM
#   (*) PREBUILT_GUEST_VM${IDX}_DISK_SRC
#       - Path to the rootfs disk image to use for the Guest VM
#
# These variables are evaluated using standard Bitbake fetchers. For example,
# local disk paths can be configured via the 'file://' prefix, network paths via
# the 'http://' or 'https://' prefixes, and so on. If using http(s), it is
# necessary to specify the file's sha256sum. For example:
#
# PREBUILT_VM1_CFG_SRC =
# "https://myserver.com/prebuilt-images/prebuilt-vm1.cfg;sha256sum=88003544af73f0f90dda75df0d7893ef7626d3c5d06691257c89afdfc594eb2c"
# PREBUILT_VM1_KERNEL_SRC =
# "https://myserver.com/prebuilt-images/Image;sha256sum=72414b6df42092a3b3a675e781fa4bcf9c432e81612b07bff37cc5ddb878abf2"
# PREBUILT_VM1_DISK_SRC =
# "https://myserver.com/prebuilt-images/prebuilt-vm1-image.wic.qcow2;sha256sum=3fe79156eb9d89318b329b6647d855b53ee14c9462232a3b10e84f1ab58dea89"

SUMMARY = "This recipe packages the Guest VM configuration, disk, and kernel \
           image, as defined in the PREBUILT_GUEST_VM* variables, into the \
           virtualization image"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "\
    file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302 \
    "

PREBUILT_GUEST_VM_INSTANCES ??= "0"

python () {
    prebuilt_guest_vm_instances = d.getVar("PREBUILT_GUEST_VM_INSTANCES")

    if d.getVar('INCLUDE_PREBUILT_GUEST_VM') != 'True':
        raise bb.parse.SkipRecipe("INCLUDE_PREBUILT_GUEST_VM must be 'True'"
                                  "to proceed!")

    for idx in range(1, int(prebuilt_guest_vm_instances) + 1):
        for var in ["CFG", "KERNEL", "DISK"]:

            value = d.getVar(f"PREBUILT_GUEST_VM{idx}_{var}_SRC")
            if not value:
                bb.fatal(f"PREBUILT_GUEST_VM{idx}_{var}_SRC was not set.")
            d.appendVar('SRC_URI', f"{value} ")
            d.appendVar(f"PREBUILT_GUEST_VM_LIST_{var}",
                        os.path.basename(value.split(';')[0]))
}

inherit allarch
inherit features_check
REQUIRED_DISTRO_FEATURES += "ewaol-virtualization"

do_configure[noexec] = "1"
do_compile[noexec] = "1"

do_install() {

    error=0
    for guest_vm_instance in $(seq 1 ${PREBUILT_GUEST_VM_INSTANCES})
    do
        bbdebug 1 "Generating Pre-Built Guest VM${guest_vm_instance}"
        CFG_NAME=$(echo "${PREBUILT_GUEST_VM_LIST_CFG}" | cut -d " " -f $guest_vm_instance)
        KERNEL_NAME=$(echo "${PREBUILT_GUEST_VM_LIST_KERNEL}" | cut -d " " -f $guest_vm_instance)
        DISK_NAME=$(echo "${PREBUILT_GUEST_VM_LIST_DISK}" | cut -d " " -f $guest_vm_instance)

        install -d ${D}${sysconfdir}/xen/auto
        install -Dm 0644 ${WORKDIR}/${CFG_NAME} ${D}${sysconfdir}/xen/auto/${CFG_NAME}

        KERNEL_DST=$(grep -oP '(?<=kernel = ")[^"]*' ${WORKDIR}/${CFG_NAME})
        DISK_DST=$(grep -oP "(?<=target=)[^'\] ]*" ${WORKDIR}/${CFG_NAME})

        DISK_DIRNAME=$(dirname ${DISK_DST})
        case "${DISK_DIRNAME}" in
            ${datadir}/*);;

            *)
                bberror "Config file '${CFG_NAME}' for Guest " \
                        "VM${guest_vm_instance} contains invalid disk path: " \
                        "'${DISK_DST}'"
                bberror "Wrong disk destination parent directory:" \
                        "'${DISK_DIRNAME}', please use '${datadir}/'"
                error=1
                ;;
        esac

        install -d ${D}${DISK_DIRNAME}
        install -Dm 0644 ${WORKDIR}/${DISK_NAME} ${D}${DISK_DST}

        KERNEL_DIRNAME=$(dirname ${KERNEL_DST})
        case "${KERNEL_DIRNAME}" in
            ${datadir}/*);;

            *)
                bberror "Config file '${CFG_NAME}' for Guest " \
                        "VM${guest_vm_instance} contains invalid kernel path:" \
                        " '${KERNEL_DST}'"
                bberror "Wrong kernel destination parent directory:" \
                        "'${KERNEL_DIRNAME}', please use '${datadir}/'"
                error=1
                ;;
        esac

        install -d ${D}${KERNEL_DIRNAME}
        install -Dm 0644 ${WORKDIR}/${KERNEL_NAME} ${D}${KERNEL_DST}
    done

    if [ ${error} -ne 0 ]; then
        bbfatal_log "Invalid configuration detected!"
    fi
}

FILES:${PN} = "${datadir} ${sysconfdir}"
