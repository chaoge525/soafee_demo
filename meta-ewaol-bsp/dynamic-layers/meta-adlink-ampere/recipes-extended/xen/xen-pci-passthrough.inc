# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI:append = " \
    file://0003-xen-arm-rename-DEVICE_PCI-to-DEVICE_PCI_HOSTBRIDGE.patch \
    file://0004-xen-arm-do-not-use-void-pointer-in-pci_host_common_p.patch \
    file://0005-xen-arm-process-pending-vPCI-map-unmap-operations.patch \
    file://0006-vpci-fix-function-attributes-for-vpci_process_pendin.patch \
    file://0007-xen-arm-add-pci-domain-for-disabled-devices.patch \
    file://0008-xen-arm-setup-MMIO-range-trap-handlers-for-hardware-.patch \
    file://0009-xen-arm-account-IO-handler-for-emulated-PCI-host-bri.patch \
    file://0010-xen-arm-do-not-map-PCI-ECAM-and-MMIO-space-to-Domain.patch \
    file://0011-rangeset-add-RANGESETF_no_print-flag.patch \
    file://0012-vpci-move-lock-outside-of-struct-vpci.patch \
    file://0013-vpci-cancel-pending-map-unmap-on-vpci-removal.patch \
    file://0014-vpci-add-hooks-for-PCI-device-assign-de-assign.patch \
    file://0015-vpci-header-implement-guest-BAR-register-handlers.patch \
    file://0016-vpci-header-handle-p2m-range-sets-per-BAR.patch \
    file://0017-vpci-header-program-p2m-with-guest-BAR-view.patch \
    file://0018-vpci-header-emulate-PCI_COMMAND-register-for-guests.patch \
    file://0019-vpci-header-reset-the-command-register-when-adding-d.patch \
    file://0020-vpci-add-initial-support-for-virtual-PCI-bus-topolog.patch \
    file://0021-xen-arm-translate-virtual-PCI-bus-topology-for-guest.patch \
    file://0022-xen-arm-account-IO-handlers-for-emulated-PCI-MSI-X.patch \
    file://0023-xen-arm-Move-is_protected-flag-to-struct-device.patch \
    file://0024-iommu-arm-Add-dt_iommu_xlate.patch \
    file://0025-iommu-arm-Introduce-iommu_add_pci_device-API.patch \
    file://0026-pci-arm-Use-iommu_add_pci_device-instead-of-arch-hoo.patch \
    file://0027-arm-libxl-Emulated-ITS-device-tree-node-in-libxl.patch \
    file://0028-xen-arm-Add-mapping-for-ITS-translation-register-whe.patch \
    file://0029-xen-arm-Modify-VITS-code-to-support-MSI-MSIX-interru.patch \
    file://0030-xen-vpci-msix-move-x86-specific-code-to-x86-file.patch \
    file://0031-xen-vpci-msix-change-return-value-of-vpci_msix_-read.patch \
    file://0032-Revert-xen-arm-Transitional-change-to-build-HAS_VPCI.patch \
    file://0033-xen-arm-Enable-the-existing-MSI-X-and-MSI-handlers-s.patch \
    file://0034-xen-vpci-Fix-remove-msix-region-logic.patch \
    file://0035-xen-arm-smmuv3-Add-PCI-devices-support-for-SMMUv3.patch \
    file://0036-xen-arm-pci-Add-support-for-pci_generic_config_-read.patch \
    file://0037-xen-arm-vpci-remove-PCI-I-O-ranges-property-value.patch \
    file://0038-xen-pci-arm-add-stub-for-is_memory_hole.patch \
    file://0039-xen-arm-vpci-Enable-vpci-for-ARM.patch \
    file://0040-xen-arm-pci-Enable-PCI-passthrough-code.patch \
    file://0041-xen-arm-Add-quirks-for-PCIE-N1SDP.patch \
    file://0042-xen-arm-Fix-some-temporary-issues-to-build-and-run-P.patch \
    file://0043-arm-pci-Add-pci-scan-boot-argument.patch \
    file://0044-xen-pci-modify-pci_add_device-to-handle-device-add-b.patch \
    file://0045-xen-pci-add-discovered-PCI-device-at-boot.patch \
    file://0046-xen-arm-add-emulated-ITS-node-to-gicv3-for-domUs-usi.patch \
    file://0047-xen-pci-helper-function-for-hwdom-using-vpci.patch \
    file://0048-xen-pci-disable-pci_device_-add-remove-when-hwdom-us.patch \
    file://0049-xen-pci-Update-conditions-to-handle-hwdom-using-vpci.patch \
    file://0050-xen-pci-update-DT-for-hwdom-when-it-uses-vpci.patch \
    file://0051-xen-pci-assign-pci-devices-to-hardware-domain.patch \
    file://0052-xen-pci-Create-pci_assign_device.patch \
    file://0053-xen-arm-pci-device-passthrough-for-dom0less-guests.patch \
    file://0054-xen-vpci-modify-pci_get_pdev_by_domain-pci_get_pdev.patch \
    file://0055-xen-vpci-Initialize-guest-bar-register-memory-type.patch \
    file://0056-xen-arm-Move-iommu_add_pci_device-from-dt-to-iommu.patch \
    file://0057-xen-arm-Parse-and-print-MMCFG-for-PCI.patch \
    file://0058-xen-arm-Parse-and-print-IORT-PCI-configuration.patch \
    file://0059-xen-arm-Parse-and-print-SSDT-DSDT-for-PCI.patch \
    file://0060-xen-arm-Prepare-IORT-for-SMMUv3-ACPI-support.patch \
    file://0061-xen-arm-Support-SMMUv3-IORT-nodes.patch \
    file://0062-xen-arm-Add-ACPI-to-SMMUv3-driver.patch \
    file://0063-arm-iommu-Support-ACPI-setup.patch \
    file://0064-xen-arm-Prepare-for-PCI-detection-with-ACPI.patch \
    file://0065-xen-arm-Add-ACPI-PCI-host-bridge-detection.patch \
    file://0066-xen-arm-Add-N1SDP-host-bridge-ACPI-device.patch \
    file://0067-xen-arm-Enable-PCI-passthrough-with-ACPI.patch \
    file://0068-xen-arm-Find-IORT-root-bridge-node-from-PCI-device.patch \
    file://0069-xen-arm-Add-id-mapping-and-translation-for-IORT.patch \
    file://0070-xen-arm-Add-acpi_xlate-member-to-iommu_ops.patch \
    file://0071-xen-arm-Add-ACPI-support-for-adding-PCI-devices.patch \
    file://0072-xen-arm-msix-add-vpci-msix-msi-support-for-ACPI-boot.patch \
    file://0073-xen-pci-acpi-add-acpi-support-for-pci-host-generic-h.patch \
    file://0074-xen-arm-acpi-Map-a-ITS-guest-devid-to-host-devid.patch \
    file://0075-xen-arm-increase-vmalloc-size-for-IO-virtual-address.patch \
    file://0076-xen-arm-xc_domain_ioport_permission-.-not-supported-.patch \
    file://0077-xen-arm-libxl-Add-interrupt-map-property-node-for-vp.patch \
    file://0078-xen-arm-iort-Handle-SMMUv3-type-hack.patch \
    "

SRC_URI:remove = " \
    file://xen-fix-gcc12-build-issues.patch \
    "
