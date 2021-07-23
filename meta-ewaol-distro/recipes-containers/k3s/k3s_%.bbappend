# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS_prepend_ewaol := "${THISDIR}/files:"

SRC_URI_append_ewaol = " file://01-k3s-service-rancher-config.conf \
                         file://02-k3s-service-fixups.conf \
                         file://k3s-killall.sh \
                       "

RRECOMMENDS_${PN}_append_ewaol = " kernel-module-xt-statistic"

K3S_OVERRIDE_DIR = "${sysconfdir}/systemd/system/k3s.service.d"

do_install_append_ewaol() {
    install -m 755 "${WORKDIR}/k3s-killall.sh" "${D}${BIN_PREFIX}/bin"

    if ${@bb.utils.contains('DISTRO_FEATURES','systemd','true','false',d)};
    then
        install -D -m 0644 \
            "${WORKDIR}/01-k3s-service-rancher-config.conf" \
            "${D}${K3S_OVERRIDE_DIR}/01-k3s-service-rancher-config.conf"

        install -D -m 0644 \
            "${WORKDIR}/02-k3s-service-fixups.conf" \
            "${D}${K3S_OVERRIDE_DIR}/02-k3s-service-fixups.conf"
    fi
}

FILES_${PN}_append_ewaol = " ${K3S_OVERRIDE_DIR}"
