# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "This recipe packages the VM configuration, disk and kernel image \
           provided in PREBUILT_VM* variables to the Host rootfs"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "\
    file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302 \
    "

PREBUILT_VM_INSTANCES ??= "0"

python () {
    prebuilt_vm_instances = d.getVar("PREBUILT_VM_INSTANCES")

    if d.getVar('INCLUDE_PREBUILT_VM') != 'True':
        raise bb.parse.SkipRecipe("INCLUDE_PREBUILT_VM must be 'True'"
                                  "to proceed!")

    for idx in range(1, int(prebuilt_vm_instances) + 1):
        for var in ["CFG", "KERNEL", "DISK"]:

            value = d.getVar(f"PREBUILT_VM{idx}_{var}_SRC")
            if not value:
                bb.fatal(f"No {var} for prebuilt VM{idx} provided!")
            d.appendVar('SRC_URI', f"{value} ")
            d.appendVar(f"PREBUILT_VM_LIST_{var}",
                        os.path.basename(value.split(';')[0]))
}

inherit allarch
inherit features_check
REQUIRED_DISTRO_FEATURES += "ewaol-virtualization"

do_configure[noexec] = "1"
do_compile[noexec] = "1"

do_install() {

    error=0
    for vm_instance in $(seq 1 ${PREBUILT_VM_INSTANCES})
    do
        bbdebug 1 "Generating Pre-Built VM ${vm_instance}"
        CFG_NAME=$(echo "${PREBUILT_VM_LIST_CFG}" | cut -d " " -f $vm_instance)
        KERNEL_NAME=$(echo "${PREBUILT_VM_LIST_KERNEL}" | cut -d " " -f $vm_instance)
        DISK_NAME=$(echo "${PREBUILT_VM_LIST_DISK}" | cut -d " " -f $vm_instance)

        install -d ${D}${sysconfdir}/xen/auto
        install -Dm 0644 ${WORKDIR}/${CFG_NAME} ${D}${sysconfdir}/xen/auto/${CFG_NAME}

        KERNEL_DST=$(grep -oP '(?<=kernel = ")[^"]*' ${WORKDIR}/${CFG_NAME})
        DISK_DST=$(grep -oP "(?<=target=)[^'\] ]*" ${WORKDIR}/${CFG_NAME})

        DISK_DIRNAME=$(dirname ${DISK_DST})
        case "${DISK_DIRNAME}" in
            ${datadir}/*);;

            *)
                bberror "Config file '${CFG_NAME}' for VM${vm_instance}" \
                        "contains invalid disk path: '${DISK_DST}'"
                bberror "Wrong disk destination parrent directory:" \
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
                bberror "Config file '${CFG_NAME}' for VM${vm_instance}" \
                        "contains invalid kernel path: '${KERNEL_DST}'"
                bberror "Wrong kernel destination parrent directory:" \
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
