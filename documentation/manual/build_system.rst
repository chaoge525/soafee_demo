..
 # Copyright (c) 2022, Arm Limited.
 #
 # SPDX-License-Identifier: MIT

############
Build System
############

An EWAOL build can be configured by setting the target platform via the
``MACHINE`` Bitbake variable, the desired distribution image features via the
``DISTRO_FEATURES`` Bitbake variable, and customizing those features via
feature-specific modifiable variables.

This page first overviews EWAOL's support for the kas build tool. Each
available distribution image feature and each supported target platform is then
defined together with their associated kas configuration files, followed by any
other additional customization options. The process for building without kas is
then briefly described.

**********************
kas Build Tool Support
**********************

The kas build tool enables automatic fetch and inclusion of layer sources, as
well as parameter and feature specification for building target images. To
enable this, kas configuration files in the YAML format are passed to the tool
to provide the necessary definitions.

These kas configuration files are modular, where passing multiple files will
result in an image produced with their combined configuration. Further, kas
configuration files can extend other kas configuration files, thereby enabling
specialized configurations that inherit common configurations.

The ``meta-ewaol-config/kas`` directory contains kas configuration files that
support building images via kas for the EWAOL project. and fall into three
ordered categories:

* Architecture Configs
* Build Modifier Configs
* Target Platform Configs

To build an EWAOL distribution image via kas, it is required to provide one
Architecture Config and one Target Platform Config, unless otherwise stated in
their descriptions below. Additional Build Modifiers are optional, and depend on
the target use-case. Currently, it is necessary that kas configuration files are
provided in order: the Architecture Config is defined first, then additional
build features via zero or more Build Modifier Configs, and finally the Target
Platform Config.

The kas configuration files to enable builds for a supported target platform or
to configure each EWAOL distribution image feature, are described in their
relevant sections below: `Target Platforms`_ and `Distribution Image Features`_,
respectively. Example usage of these kas configuration files can be found in the
:ref:`user_guide_reproduce_build` section of the User Guide.

.. note::
  If a kas configuration file does not set a particular build parameter, the
  parameter will take its default value.

****************
Target Platforms
****************

There is currently one supported target platform (corresponding to the
``MACHINE`` Bitbake variable) with an associated kas configuration file, as
follows.

N1SDP
=====

  * **Corresponding value for** ``MACHINE`` **variable**: ``n1sdp``.
  * **Target Platform Config**: ``meta-ewaol-config/kas/n1sdp.yml``.

  This supported target platform is the Neoverse N1 System Development Platform
  (N1SDP), implemented in |meta-arm-bsp|_.

  To enable this, the ``n1sdp.yml`` Target Platform Config includes common
  configuration from the ``meta-ewaol-config/kas/include/arm-machines.yml`` kas
  configuration file, which defines the BSPs, layers, and dependencies required
  when building for the ``n1sdp``.

***************************
Distribution Image Features
***************************

For a particular target platform, the available EWAOL distribution image
features (corresponding to the contents of the ``DISTRO_FEATURES`` Bitbake
variable) are detailed in this section, along with any associated kas
configuration files, and any associated customization options relevant for that
feature.

.. _manual_build_system_ewaol_architectures:

EWAOL Architectures
===================

EWAOL distribution images can be configured via kas using Architecture Configs.
These include a set of common configuration from a base EWAOL kas configuration
file:

  * ``meta-ewaol-config/kas/include/ewaol-base.yml``

This kas configuration file defines the base EWAOL layer dependencies and their
software sources, as well as additional build configuration variables. It also
includes the ``meta-ewaol-config/kas/include/ewaol-release.yml`` kas
configuration file, where the layers dependencies are pinned for any
corresponding EWAOL release.

.. _manual_build_system_baremetal_architecture:

Baremetal Architecture
----------------------

  * **Corresponding value in** ``DISTRO_FEATURES`` **variable**:
    ``ewaol-baremetal``.
  * **Architecture Config**: ``meta-ewaol-config/kas/baremetal.yml``.

    This EWAOL distribution image feature:

      * Enables the ``ewaol-baremetal-image`` build target, to build an EWAOL
        baremetal distribution image.
      * Is incompatible with the ``ewaol-virtualization`` distribution image
        feature.

    The Architecture Config for this distribution image feature automatically
    appends ``ewaol-baremetal`` to ``DISTRO_FEATURES`` and sets the sets the
    build target to ``ewaol-baremetal-image``.

    To build EWAOL baremetal distribution image, provide the Baremetal
    Architecture Config to the kas build command. For example, to build an EWAOL
    baremetal distribution image for the N1SDP hardware target platform, run the
    following command:

      .. code-block:: console

        kas build meta-ewaol-config/kas/baremetal.yml:meta-ewaol-config/kas/n1sdp.yml

.. _manual_build_system_virtualization_architecture:

Virtualization Architecture
---------------------------

  * **Corresponding value in** ``DISTRO_FEATURES`` **variable**:
    ``ewaol-virtualization``.
  * **Architecture Config**: ``meta-ewaol-config/kas/virtualization.yml``.

    This EWAOL distribution image feature:

      * Enables the ``ewaol-virtualization-image`` build target, to build an
        EWAOL virtualization distribution image.
      * Includes the Xen hypervisor into the software stack.
      * Enables Xen specific configs required by kernel.
      * Includes all necessary packages and adjustments to the Control VM's root
        filesystem to support management of Xen Guest VMs.
      * Uses Bitbake |Multiple Configuration Build|_.
      * Includes a single Guest VM based on the ``generic-arm64`` ``MACHINE``,
        by default.
      * Is incompatible with the ``ewaol-baremetal`` distribution image feature.

    The Architecture Config for this distribution image feature automatically
    appends ``ewaol-virtualization`` to ``DISTRO_FEATURES`` and sets the sets
    the build target to ``ewaol-virtualization-image``.

    To build EWAOL virtualization distribution image, provide the Virtualization
    Architecture Config to the kas build command. For example, to build an EWAOL
    virtualization distribution image for the N1SDP hardware target platform,
    run the following command:

      .. code-block:: console

        kas build meta-ewaol-config/kas/virtualization.yml:meta-ewaol-config/kas/n1sdp.yml

.. _manual_build_system_virtualization_customization:

Customization
^^^^^^^^^^^^^

Configurable build-time variables for the Guest VM are defined
within the ``meta-ewaol-distro/conf/multiconfig/ewaol-guest-vm.conf`` file and
the ``meta-ewaol-distro/conf/distro/include/ewaol-guest-vm.inc`` which it
includes.

The following list shows the available variables for the Control VM and the
single default Guest VM, together with the default values (where ``MB`` and
``KB`` refer to Megabytes and Kilobytes, respectively):

  .. code-block:: yaml
    :substitutions:

    |virtualization customization yaml|

The variables may be set either within an included kas configuration file
(see ``meta-ewaol-config/kas/virtualization.yml`` for example usage), the
environment, or manually via, for example, ``local.conf``. The
``EWAOL_*_ROOTFS_EXTRA_SPACE`` variables apply their values to the relevant
``IMAGE_ROOTFS_EXTRA_SPACE`` bitbake variable.

Adding Extra EWAOL Guest VM Instances
"""""""""""""""""""""""""""""""""""""

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

Other EWAOL Features
====================

Developer Support
-----------------

  * **Corresponding value in** ``DISTRO_FEATURES`` **variable**:
    ``ewaol-devel``.

    This EWAOL distribution image feature:

      * Is default if not set with any other EWAOL-specific ``DISTRO_FEATURES``.
      * Includes packages appropriate for development image builds, such as the
        ``debug-tweaks`` package, which sets an empty root password for
        simplified development access.

.. _manual_build_system_run_time_integration_tests:

Run-Time Integration Tests
--------------------------

  * **Corresponding value in** ``DISTRO_FEATURES`` **variable**:
    ``ewaol-test``.
  * **Build Modifier Config**: ``meta-ewaol-config/kas/tests.yml``.

    This EWAOL distribution image feature:

      * Includes the EWAOL test suites provided to validate the image is running
        successfully with the expected EWAOL functionalities.

    The Build Modifier for this distribution image feature automatically
    includes the Yocto Package Test (ptest) framework in the image, configures
    the inclusion of ``meta-ewaol-tests`` as a Yocto layer source for the build,
    and appends the ``ewaol-test`` feature to ``DISTRO_FEATURES`` for the build.

    To include run-time integration tests on an EWAOL distribution image,
    provide the Build Modifier Config to the kas build command. For example, to
    include the tests on an EWAOL distribution image for the N1SDP hardware
    target platform, run the following commands depending on the target
    architecture:

    * Baremetal architecture:

      .. code-block:: console

        kas build meta-ewaol-config/kas/baremetal.yml:meta-ewaol-config/kas/tests.yml:meta-ewaol-config/kas/n1sdp.yml

    * Virtualization architecture:

      .. code-block:: console

        kas build meta-ewaol-config/kas/virtualization.yml:meta-ewaol-config/kas/tests.yml:meta-ewaol-config/kas/n1sdp.yml

    Each suite of run-time integration tests and specific customizable variables
    associated with each suite are detailed separately, at
    :ref:`validation_run-time_integration_tests`.

.. _manual_build_system_security_hardening:

Security Hardening
------------------

  * **Corresponding value in** ``DISTRO_FEATURES`` **variable**:
    ``ewaol-security``.
  * **Build Modifier Config**: ``meta-ewaol-config/kas/security.yml``.

    This EWAOL distribution image feature:

      * Configures user accounts, packages, remote access controls and other
        image features to provide extra security hardening for the EWAOL
        distribution image.

    To include extra security hardening on an EWAOL distribution image, provide
    the Build Modifier Config to the kas build command, which appends the
    ``ewaol-security`` feature to ``DISTRO_FEATURES`` for the build. For
    example, to include it on the EWAOL distribution image for the N1SDP
    hardware target platform, run the following commands depending on the
    target architecture:

    * Baremetal architecture:

      .. code-block:: console

        kas build meta-ewaol-config/kas/baremetal.yml:meta-ewaol-config/kas/security.yml:meta-ewaol-config/kas/n1sdp.yml

    * Virtualization architecture:

      .. code-block:: console

        kas build meta-ewaol-config/kas/virtualization.yml:meta-ewaol-config/kas/security.yml:meta-ewaol-config/kas/n1sdp.yml

    The security hardening is described in more detail at
    :ref:`Security Hardening<manual/hardening:Security Hardening>`.

.. _manual_build_system_sdk:

Software Development Kit (SDK)
------------------------------

  * **Corresponding value in** ``DISTRO_FEATURES`` **variable**:
    ``ewaol-sdk``.
  * **Build Modifier Config**: ``meta-ewaol-config/kas/baremetal-sdk.yml`` and
    ``meta-ewaol-config/kas/virtualization-sdk.yml``, for the baremetal
    architecture and virtualization architecture, respectively.

    This EWAOL distribution image feature:

      * Adds the EWAOL Software Development Kit (SDK) which includes packages
        and image features to support on-target software development activites.
      * Enables two additional SDK build targets, ``ewaol-baremetal-sdk-image``
        and ``ewaol-virtualization-sdk-image``, each only compatible with the
        corresponding architecture's distribution image feature.

    The Build Modifier for this distribution image feature automatically appends
    ``ewaol-sdk`` to ``DISTRO_FEATURES``, and sets the appropriate build target
    with the necessary configuration from the relevant Architecture Config
    included by default, meaning it is not necessary to explicitly supply an
    Architecture Config to the kas build tool if passing an SDK Build Modifier
    Config.

    To include the SDK on an EWAOL distribution image, provide the appropriate
    SDK Build Modifier Config to the kas build command. For example, to include
    the SDK on an EWAOL distribution image for the N1SDP hardware target
    platform, run the following commands depending on the target architecture:

    * Baremetal architecture:

      .. code-block:: console

        kas build meta-ewaol-config/kas/baremetal-sdk.yml:meta-ewaol-config/kas/n1sdp.yml

    * Virtualization architecture:

      .. code-block:: console

        kas build meta-ewaol-config/kas/virtualization-sdk.yml:meta-ewaol-config/kas/n1sdp.yml

    The SDK itself is described in more detail at
    :ref:`Software Development Kit (SDK)<manual/sdk:Software Development Kit (SDK)>`.

********************************************
Additional Distribution Image Customizations
********************************************

An additional set of customization options are available for EWAOL distribution
images, which don't fall under a distinct distribution image feature. These
customizations are listed below, grouped by the customization target.

Filesystem Customization
========================

Adding Extra Rootfs Space
-------------------------

The size of the root filesystem can be extended via the
``EWAOL_ROOTFS_EXTRA_SPACE`` Bitbake variable, which defaults to ``2000000``
Kilobytes. The value of this variable is appended to the
``IMAGE_ROOTFS_EXTRA_SPACE`` Bitbake variable. For an EWAOL virtualization
distribution image, the root filesystems of both the Control VM and the Guest
VM(s) are extended via this variable, in addition to any other parameters which
affect those filesystems as described in
:ref:`Virtualization Architecture Customization <manual_build_system_virtualization_customization>`.

Filesystem Compilation Tuning
-----------------------------

The EWAOL filesystem by default uses the generic ``armv8a-crc`` tune for
``aarch64`` based target platforms. This reduces build times by increasing the
sstate-cache reused between different image types and target platforms. This
optimization can be disabled by setting ``EWAOL_GENERIC_ARM64_FILESYSTEM`` to
``"0"``. The tune used when ``EWAOL_GENERIC_ARM64_FILESYSTEM`` is enabled can
be changed by setting ``EWAOL_GENERIC_ARM64_DEFAULTTUNE``, which configures the
``DEFAULTTUNE`` Bitbake variable for the ``aarch64`` based target platforms
builds. See |DEFAULTTUNE|_ for more information.

In summary, the relevant variables and their default values are:

  .. code-block:: yaml

    EWAOL_GENERIC_ARM64_FILESYSTEM: "1"             # Enable generic file system (1 or 0).
    EWAOL_GENERIC_ARM64_DEFAULTTUNE: "armv8a-crc"   # Value of DEFAULTTUNE if generic file system enabled.

Their values can be set by passing them as enviromental variables. For example,
the optimization can be disabled using:

  .. code-block:: console

        EWAOL_GENERIC_ARM64_FILESYSTEM="0" kas build meta-ewaol-config/kas/baremetal.yml:meta-ewaol-config/kas/n1sdp.yml

**************************
Manual Bitbake Build Setup
**************************

In order to build an EWAOL distribution image without the kas build tool
directly via bitbake, it is necessary to prepare a bitbake project as follows:

  * Configure dependent Yocto layers in ``bblayers.conf``.
  * Configure the ``DISTRO`` as ``ewaol`` in ``local.conf``.
  * Configure the image ``DISTRO_FEATURES`` in ``local.conf``.

Assuming correct environment configuration, the Bitbake build can then be run
for the desired image target corresponding to one of the following:

  * ``ewaol-baremetal-image``
  * ``ewaol-baremetal-sdk-image``
  * ``ewaol-virtualization-image``
  * ``ewaol-virtualization-sdk-image``

As the kas build configuration files within the ``meta-ewaol-config/kas/``
directory define the recommended build settings for each feature. Any additional
functionalities may therefore be enabled by reading these configuration files
and manually inserting their changes into the Bitbake build environment.
