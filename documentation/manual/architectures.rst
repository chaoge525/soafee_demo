..
 # Copyright (c) 2022, Arm Limited.
 #
 # SPDX-License-Identifier: MIT

####################
System Architectures
####################

************
Introduction
************

This page describes the two target architectures supported by the EWAOL project.

**********************
Baremetal Architecture
**********************

.. image:: ../images/baremetal_architecture.png

An EWAOL baremetal distribution image (``ewaol-baremetal-image``) is enabled if
``ewaol-baremetal`` is included in ``DISTRO_FEATURES``. The image includes the
following image features by default:

  * Container engine and runtime with Docker and runc-opencontainers
  * Container workload orchestration with the K3s kubernetes distribution

On a baremetal distribution image system boot, a K3s Systemd service
(``k3s.service``) provides a container orchestration environment consisting of a
single K3s control plane and a single built-in K3s agent, communicating via the
local loopback network interface. This enables the orchestration and execution
of containerized application workloads on the baremetal distribution image,
operating as a single-node K3s cluster.

***************************
Virtualization Architecture
***************************

.. image:: ../images/virtualization_architecture.png

An EWAOL virtualization distribution image (``ewaol-virtualization-image``) is
enabled if ``ewaol-virtualization`` is included in ``DISTRO_FEATURES``. The
image includes the following image features by default:

  * Hardware virtualization support with the Xen type-1 hypervisor
  * Container engine and runtime with Docker and runc-opencontainers
  * Container workload orchestration with the K3s kubernetes distribution

On an EWAOL virtualization distribution image, the software stack includes the
Xen type-1 hypervisor and provides a Control VM (Dom0) and a single bundled
Guest VM (DomU), by default. Virtualization support also includes Xen-related
configurations and necessary Xen-management packages into the Control VM root
filesystem.

The Control VM includes the ``xen-tools`` package along with network
configuration for the ``xenbr0`` bridge, to allow the Guest VM to access the
external network. By default, the bundled Guest VM image is based on the
``generic-arm64`` ``MACHINE``.

A Guest VM is included into the EWAOL virtualization distribution image via the
``ewaol-guest-vm-package`` recipe, with the Guest VM's rootfs stored as a raw
image file in ``*.qcow2`` format. In addition, this package includes a sample
Xen domain configuration file, which holds Xen-specific Guest VM settings as
detailed in `xl domain configuration`_. By default one Guest VM (with hostname
``ewaol-guest-vm1``) is built and included on the virtualization distribution
image, but this number can be customized, as described later in this page.

Configurable build-time variables for the Guest VM are defined
within the ``meta-ewaol-distro/conf/multiconfig/ewaol-guest-vm.conf`` file and
the ``meta-ewaol-distro/conf/distro/include/ewaol-guest-vm.inc`` which it
includes.

The following list shows the available variables for the Control VM and the
single default Guest VM, together with the default values:

  .. code-block:: yaml
    :substitutions:

    |virtualization customization yaml|

The variables may be set either within an included kas configuration file
(see ``meta-ewaol-config/kas/virtualization.yml`` for example usage), the
environment, or manually via, for example, ``local.conf``. The
``EWAOL_*_ROOTFS_EXTRA_SPACE`` variables apply their values to the relevant
``IMAGE_ROOTFS_EXTRA_SPACE`` bitbake variable.

It is possible to deploy multiple EWAOL Guest VM instances on the virtualization
distribution image, each one based on the same kernel and image recipe. The
number of Guest VM instances built for and included on the virtualization
distribution image can be set via the ``EWAOL_GUEST_VM_INSTANCES`` variable.

Guest VM instances can be independently configured via Bitbake variables which
reference the Guest VM's integer instance index, from 1 to the value of
``EWAOL_GUEST_VM_INSTANCES``, inclusive. For example, variables with a prefix
``EWAOL_GUEST_VM1_`` apply to the first Guest VM, variables with a prefix
``EWAOL_GUEST_VM2_`` apply to the second Guest VM, and so on. All Guest VM
instances use the same default configuration, apart from the hostname, which is
generated for each Guest VM by appending the instance index to the
``EWAOL_GUEST_VM_HOSTNAME`` Bitbake variable. By default, the first Guest VM
will have a hostname ``ewaol-guest-vm1``, the second will have a hostname
``ewaol-guest-vm2``, and so on. An example of configuring a second Guest VM
instance using the kas tool is given in
``meta-ewaol-config/kas/second-vm-parameters.yml``, although these variables
will only be used if ``EWAOL_GUEST_VM_INSTANCES`` is set to build two or more
Guest VMs.
