Image Builds
============

The main image build targets are:

* ``ewaol-image-docker``
* ``ewaol-image-podman``

Each build target implements the EWAOL software stack, differing only on the
backend containerization technology: Docker or Podman.

To facilitate containerized workload orchestration on the edge, both build
targets include the K3S orchestration package provided by the
``meta-virtualization`` Yocto layer and extended in ``meta-ewaol``. This
package provides a K3S server wrapped as a systemd service which auto-starts on
image boot. The K3S server may be interacted with via the Kubernetes REST API
or via the Kubernetes command-line tool ``kubectl``, where the `Kubernetes API
Overview`_ and `kubectl Overview`_ may be referred to for usage instructions.
Enabling and disabling the systemd service via ``systemctl [start|stop] k3s``
will bring-up and shutdown the K3S server running on the image, meaning
containers may remain running (without orchestration) after stopping the
systemd service. If desired, containers may be stopped prior to shutting down
the server via the API or command-line tool, or alternatively they may be
stopped independently from the server status via the provided
``k3s-killall.sh`` script.

.. note::
    Example usage of the K3S orchestration package is provided in the form of
    the K3S integration test suite implementation, documented in
    :ref:`validations:Image Validation`.

.. _Kubernetes API Overview: https://kubernetes.io/docs/reference/using-api/
.. _kubectl Overview: https://kubernetes.io/docs/reference/kubectl/overview/

To prepare an EWAOL image build, it is necessary to define the target machine
for the build via the bitbake ``MACHINE`` parameter. The image build can then be
customized by defining the desired EWAOL features via the bitbake
``DISTRO_FEATURES`` parameter, which will enable particular recipes and
components within the ``meta-ewaol`` repository and any dependent Yocto layers
necessary to build those features. In addition, it is necessary to define the
``DISTRO`` for the bitbake build to be ``ewaol`` in order to activate
EWAOL-specific build configurations.

In this document, the available ``MACHINE`` and ``DISTRO_FEATURES`` options that
are currently supported by ``meta-ewaol`` are first stated below, before being
described in further detail in `Distribution Features`_. The kas configuration
YAML files provided for enabling those EWAOL features on the supported target
machines are described in `kas Build Configurations`_. If using the recommended
kas build tool is not possible, the manual approach for preparing and building
an EWAOL image via bitbake is briefly outlined in
`Manual Bitbake Build Preparation`_.

The currently supported ``MACHINE``\s are:

* ``fvp-base``
* ``n1sdp``

The currently supported ``DISTRO_FEATURES`` are:

* ``ewaol-devel``
* ``ewaol-test``
* ``ewaol-sdk``

In addition to kas build config files that enable the above build options, an
image build via kas may be further customized with extra optional config
files, currently:

* ``ci.yml``

The above features are now defined as follows.

Distribution Features
---------------------

For a particular target ``MACHINE``, the available ``DISTRO_FEATURES`` to
configure the image are as follows:

* ``ewaol-devel``

    * Default if not set with any other EWAOL-specific ``DISTRO_FEATURES``
    * Includes packages appropriate for development image builds, such as the
      ``debug-tweaks`` package, which sets an empty root password for simplified
      development access.

* ``ewaol-test``

    * Includes the EWAOL test suites provided to validate the image is running
      successfully and compliant with the expected EWAOL software
      functionalities. These tests are provided by the ``meta-ewaol-tests``
      Yocto layer, documented in :ref:`validations:Image Validation`.

* ``ewaol-sdk``

    * Adds the EWAOL Software Development Kit (SDK) which includes packages
      and image features to support software development on the target image.
      For more details on the SDK, see
      `Building EWAOL Software Development Kit (SDK) Image`_

Provided their Yocto layer sources can be found by bitbake via
``conf/bblayers.conf``, these features can be enabled by passing them as a
space-separated list into ``DISTRO_FEATURES`` within ``conf/local.conf``. This
build process is described in `Manual Bitbake Build Preparation`_.

For use with the recommended kas build tool, the ``meta-ewaol`` repository also
provides kas build config files that will enable automatic fetch and inclusion
of layer sources, as well as parameter and feature specification for building
the target images. Extra build config files are further provided that enable a
wider range of build options without manual configuration. These are as
follows.

kas Build Configurations
------------------------

The EWAOL quickstart guide illustrates how to build an EWAOL software image by
supplying build configuration YAML files to the kas build tool:
:ref:`quickstart_minimal_image_build_via_kas`.

The ``meta-ewaol-config/kas`` directory contains build configs to support
building images via kas for the EWAOL project.

Build configs are modular, where combining config files will result in an image
produced with their combined configuration. Further, build configs files can
extend other build configs files, thereby enabling specialized configurations
that inherit common and thus shared build configurations.

The kas build configs implemented for the EWAOL project fall into two
categories, as described below.

Machine Configs
^^^^^^^^^^^^^^^

Machine configs specify the target machine for the kas build. These define the
``MACHINE`` parameter in the bitbake ``local.conf`` file, and all associated
layers and configurations required to build a EWAOL project software image to
run on that machine.

``meta-ewaol-config`` currently provides two machine build configs:

* ``fvp-base.yml``
* ``n1sdp.yml``

The name of the machine config YAML file matches the ``MACHINE`` name for the
bitbake build.

Each machine config includes common configuration from:

* ``ewaol-base.yml``

    Defines the image targets, layer dependencies and their software sources
    and build configuration variables. It also includes the
    ``ewaol-release.yml`` where the layers dependencies are pinned for the
    specific EWAOL release tag.

* ``arm-machines.yml``

    Defines the BSPs, layers, and dependencies specific to the Arm reference
    platforms of the supported machines.

Build Modifiers
^^^^^^^^^^^^^^^

Build modifier config files specify additional sources and parameter
customizations relevant to a particular image feature.

These are the current build modifier YAML files:

* ``tests.yml``

    Includes the Yocto Package Test (ptest) framework in the image, configures
    the inclusion of ``meta-ewaol-tests`` as a Yocto layer source for the
    build, and appends the ``ewaol-test`` feature as a ``DISTRO_FEATURE`` for
    the build. Additional documentation for the EWAOL tests layer is given in
    :ref:`validations:Image Validation`.

* ``ci.yml``

    Considers the image build to be an image built as part of a Continuous
    Integration pipeline, causing the build process to delete its temporary
    work files following build completion.

* ``sdk.yml``

    Changes the default build targets to the SDK images, and appends
    ``ewaol-sdk`` as a ``DISTRO_FEATURE`` for the build. Documentation for
    the EWAOL SDK is given in
    `Building EWAOL Software Development Kit (SDK) Image`_.

.. note::
  If a kas build config does not set a build parameter, the parameter will
  take the default value. For example, if ``tests.yml`` is not included then
  the value of ``DISTRO_FEATURE`` will take its default value as specified
  earlier in this document.

Adding External Machines and BSP Layers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to add an external machine to be built with EWAOL, you need to add a
``my-machine.yml`` kas configuration file (where ``my-machine`` is the
``MACHINE`` name of the external machine) to your Yocto BSP layer:
``meta-my-bsp-layer``. This file should have the following structure:

.. code-block:: console

    header:
      version: 10
      includes:
        - repo: meta-ewaol
          file: meta-ewaol-config/kas/ewaol-base.yml
        - repo: meta-ewaol
          file: meta-ewaol-config/kas/tests.yml

    repos:
      meta-my-bsp-layer:

      meta-ewaol:
        url: https://git.gitlab.arm.com/ewaol/meta-ewaol.git
        refspec: v0.1.1

    machine: my-machine

To read more about how to customize this configuration file, check the
`Kas documentation`_. Images for ``my-machine`` can be built by running the
following kas command:

.. code-block:: console

    kas build meta-my-bsp-layer/my-machine.yml

Build Validation
----------------

Container Runtime Kernel Configuration Check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After the kernel configuration has been produced, it is checked to validate the
presence of the kernel config necessary for the resulting image to run
container instances. This is done using the kernel check bbclass available at
``meta-ewaol-distro/classes/containers_kernelcfg_check.bbclass``:

1. The kernel check function ensures that the ``docker.cfg`` config file is the
   same as the reference `Yocto docker config file`_.

2. If the hash comparison was a success, the list of kernel configs required
   for docker to run is retrieved. If the ``docker.cfg`` file is not identical
   to the reference file, a bitbake warning is displayed.

3. The list of required kernel configs is compared against the list of
   available configs in the kernel. They all need to be present either as module
   (=m) or built-in (=y). A bitbake warning is produced if the kernel is not
   configured correctly.

.. _Yocto docker config file: http://git.yoctoproject.org/cgit/cgit.cgi/yocto-kernel-cache/tree/features/docker/docker.cfg
.. _Kas documentation: https://kas.readthedocs.io/en/latest/userguide.html#including-configuration-files-from-other-repos

Manual Bitbake Build Preparation
--------------------------------

In order to build an EWAOL image without the kas build tool directly via
bitbake, it is necessary to prepare a bitbake project as follows:

* Configure dependent Yocto layers
    The source repositories in which the required Yocto layers can be found
    are listed in :ref:`readme_layer_dependencies`. ``conf/bblayers.conf``
    must then be configured to provide the paths to the following Yocto layers
    on the build system:

        * meta-openembedded/meta-filesystems
        * meta-openembedded/meta-networking
        * meta-openembedded/meta-oe
        * meta-openembedded/meta-perl
        * meta-openembedded/meta-python
        * meta-security
        * meta-virtualization
        * poky/meta
        * poky/meta-poky
        * meta-ewaol/meta-ewaol-distro

    If tests are required, the ``meta-ewaol/meta-ewaol-tests`` Yocto layer must
    also be included.

* Configure the image ``DISTRO``
    In order to activate EWAOL-specific build configurations, it is necessary
    for the bitbake ``DISTRO`` to be set to ``ewaol`` in the build directory's
    ``conf/local.conf`` file by appending:

        ``DISTRO = "ewaol"``

* (Optionally) Configure the image ``DISTRO_FEATURES``
    The image features as defined in `Distribution Features`_ can be configured
    to enable particular functionalities within the resulting EWAOL image. For
    example, as ``ewaol-devel`` is set by default, additional features such as
    EWAOL image validation tests may simply be added to the build by appending
    the following to ``conf/local.conf``:

        ``DISTRO_FEATURES_append = " ewaol-test"``

.. note::
  The kas build configuration YAML files within the ``meta-ewaol-config/kas/``
  directory define how the build will be prepared by the kas build tool. Any
  specific functionalities not described in this section may therefore be
  enabled by reading these configuration files and manually inserting their
  changes into the build configuration folder.

Building EWAOL Software Development Kit (SDK) Image
---------------------------------------------------

.. note::
  Please note that the SDK image requires at least 110 GBytes of free disk
  space to build!

The EWAOL SDK images enable users to perform common development tasks on the
target, such as:

  * Application and kernel module compilation

  * Remote debugging

  * Profiling

  * Tracing

  * Runtime package management

The precise list of packages and image features provided as part of the EWAOL
SDK can be found in ``meta-ewaol-distro/conf/distro/include/ewaol-sdk.inc``.

The Yocto project provides guidance for some of these common development tasks,
for example `kernel module compilation`_, `profiling and tracing`_, and
`runtime package management`_.

  .. _kernel module compilation:
      https://docs.yoctoproject.org/3.3.2/kernel-dev/common.html#building-out-of-tree-modules-on-the-target

  .. _profiling and tracing: https://docs.yoctoproject.org/3.3.2/profile-manual/index.html

  .. _runtime package management:
      https://docs.yoctoproject.org/3.3.2/dev-manual/common-tasks.html#using-runtime-package-management

To build SDK image append ``meta-ewaol-config/kas/sdk.yml`` configuration
file to the kas build command. This ``.yml`` file changes the default build
targets to ``ewaol-image-[docker|podman]-sdk``. For more details about
selecting configuration files for kas, see: :ref:`quickstart_build_host_setup`.

For example, to build the SDK images for the N1SDP via kas:

.. code-block::

  kas build meta-ewaol-config/kas/n1sdp.yml:meta-ewaol-config/kas/sdk.yml

In this example, the SDK images produced by the kas build will be found at:
``build/tmp/deploy/images/n1sdp/ewaol-image-[docker|podman]-sdk-n1sdp.*``.
To deploy the generated images, please refer to the
:ref:`quickstart_deploy_on_n1sdp` section.
