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

This page details EWAOL's available distribution image features and its
supported target platform via the Bitbake ``MACHINE`` configuration, before
describing the kas configuration files provided in ``meta-ewaol-config/kas`` to
support building and configuring the EWAOL distribution. The process for
building without kas is then briefly described.

*********************************
EWAOL Distribution Image Features
*********************************

For a particular ``MACHINE`` target platform, the available ``DISTRO_FEATURES``
to configure the image are as follows:

  * ``ewaol-baremetal``:

    * Enables the ``ewaol-baremetal-image`` build target, to build an EWAOL
      baremetal distribution image.
    * Incompatible with the ``ewaol-virtualization`` distribution image feature.

  * ``ewaol-virtualization``:

    * Enables the ``ewaol-virtualization-image`` build target, to build an EWAOL
      virtualization distribution image.
    * Includes the Xen hypervisor into the software stack.
    * Enables Xen specific configs required by kernel.
    * Includes all necessary packages and adjustments to the Control VM's root
      filesystem to support management of Xen Guest VMs.
    * Uses Bitbake |Multiple Configuration Build|_.
    * Guest VM based on the ``generic-arm64`` ``MACHINE`` by default.
    * Incompatible with the ``ewaol-baremetal`` distribution image feature.

    Customization of the Control VM and Guest VMs is detailed as part of the
    virtualization architecture description at
    :ref:`System Architectures<manual/architectures:System Architectures>`.

  * ``ewaol-devel``:

    * Default if not set with any other EWAOL-specific ``DISTRO_FEATURES``
    * Includes packages appropriate for development image builds, such as the
      ``debug-tweaks`` package, which sets an empty root password for simplified
      development access.

  * ``ewaol-test``:

    * Includes the EWAOL test suites provided to validate the image is running
      successfully with the expected EWAOL functionalities.

    The run-time integration tests and specific customizable variables for those
    tests are detailed separately, at
    :ref:`Validation <manual/validation:Validation>`.

  * ``ewaol-sdk``:

    * Adds the EWAOL Software Development Kit (SDK) which includes packages
      and image features to support on-target software development activites.
    * Enables two additional SDK build targets, ``ewaol-baremetal-sdk-image``
      and ``ewaol-virtualization-sdk-image``, each only compatible with the
      corresponding architecture's distribution image feature.

    The SDK is detailed separately, at
    :ref:`Software Development Kit (SDK)<manual/sdk:Software Development Kit (SDK)>`.

*****************************
EWAOL kas Configuration Files
*****************************

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

.. note::
  Example usage of these kas configuration files can be found in the
  :ref:`User Guide <user_guide/index:User Guide>`.

The three categories and their kas config files as provided in
``meta-ewaol-config/kas`` are as follows.

Architecture Configs
====================

Architecture Configs specify the target EWAOL architecture.

There are therefore two Architecture Configs provided in
``meta-ewaol-config/kas``:

  * ``baremetal.yml``

    Appends ``ewaol-baremetal`` to ``DISTRO_FEATURES`` and sets the build target
    to ``ewaol-baremetal-image`` in order to build an EWAOL distribution image
    for the baremetal architecture.

  * ``virtualization.yml``

    Appends ``ewaol-virtualization`` to ``DISTRO_FEATURES`` and sets the build
    target to ``ewaol-virtualization-image`` in order to build an EWAOL
    distribution image for the virtualization architecture.

Each Architecture Config includes a set of common configuration from a base
EWAOL kas configuration file:

  * ``include/ewaol-base.yml``

    Defines the base EWAOL layer dependencies and their software sources, as
    well as additional build configuration variables. It also includes the
    ``include/ewaol-release.yml`` kas configuration file, where the layers
    dependencies are pinned for the specific EWAOL release.

Build Modifier Configs
======================

Build Modifier Configs specify additional sources and parameter customizations
relevant to a particular EWAOL distribution image feature.

These are the current Build Modifier Configs:

  * ``tests.yml``

    Includes the Yocto Package Test (ptest) framework in the image, configures
    the inclusion of ``meta-ewaol-tests`` as a Yocto layer source for the
    build, and appends the ``ewaol-test`` feature to ``DISTRO_FEATURES`` for
    the build. Additional documentation for the EWAOL tests layer is given in
    :ref:`Validation <manual/validation:Validation>`.

  * ``baremetal-sdk.yml``

    Appends ``ewaol-sdk`` to ``DISTRO_FEATURES``, sets the build target to
    ``ewaol-baremetal-sdk-image``, and includes the necessary configuration
    from ``baremetal.yml`` to build an SDK image for the Baremetal
    architecture (meaning it is not necessary to explicitly supply kas with that
    Architecture Config). Documentation for the EWAOL SDK is given in
    :ref:`Software Development Kit (SDK)<manual/sdk:Software Development Kit (SDK)>`.
    This Build Modifier is not compatible with the ``virtualization.yml``
    Architecture Config.

  * ``virtualization-sdk.yml``

    Appends ``ewaol-sdk`` to ``DISTRO_FEATURES``, sets the build target to
    ``ewaol-virtualization-sdk-image``, and includes the necessary configuration
    from ``virtualization.yml`` to build an SDK image for the Virtualization
    architecture (meaning it is not necessary to explicitly supply kas with this
    Architecture Config). Documentation for the EWAOL SDK is given in
    :ref:`Software Development Kit (SDK)<manual/sdk:Software Development Kit (SDK)>`.
    This Build Modifier is not compatible with the ``baremetal.yml``
    Architecture Config.

Target Platform Configs
=======================

Target Platform Configs define the ``MACHINE`` Bitbake variable for the build,
and all associated layers and configurations required to build an EWAOL
distribution image to run on that target platform.

``meta-ewaol-config`` currently provides a single Machine Config:

  * ``n1sdp.yml``

    This Target Platform Config prepares an EWAOL distribution image build that
    targets the Neoverse N1 System Development Platform (N1SDP), corresponding
    to the ``n1sdp`` ``MACHINE`` implemented in |meta-arm-bsp|_.
    To enable this, the ``n1sdp.yml`` Target Platform Config includes common
    configuration from the ``include/arm-machines.yml`` kas configuration file,
    which defines the BSPs, layers, and dependencies required when building for
    the ``n1sdp``.

.. note::
  If a kas configuration file does not set a particular build parameter, the
  parameter will take its default value.

**************************
Manual Bitbake Build Setup
**************************

In order to build an EWAOL distribution image without the kas build tool
directly via bitbake, it is necessary to prepare a bitbake project as follows:

  * Configure dependent Yocto layers in ``bblayers.conf``
  * Configure the ``DISTRO`` as ``ewaol`` in ``local.conf``
  * Configure the image ``DISTRO_FEATURES`` in ``local.conf``

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
