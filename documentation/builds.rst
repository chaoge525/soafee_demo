Image Builds
============

The currently supported image build targets are:

* ``ewaol-image-docker``
* ``ewaol-image-podman``

Each build target implements the EWAOL software stack, differing only on the
backend containerisation technology: Docker or Podman.

For each target image for a target machine, particular EWAOL recipes and
components within ``meta-ewaol`` repository can be enabled in the build by
either including them as features passed as bitbake ``DISTRO_FEATURES``
together with the specified ``MACHINE``, or via kas build configuration YAML
files with these parameters pre-configured.

The available options are provided here, before being further detailed later
in this document.

The currently supported ``MACHINE``\s are:

* ``fvp-base``
* ``n1sdp``

The currently supported ``DISTRO_FEATURES`` are:

* ``ewaol-devel``
* ``ewaol-test``

In addition to kas build config files that enable the above build options, an
image build via kas may be further customised with extra optional config
files, currently:

* ``ci.yml``

Next, the features are defined as they should be configured for an image build
via bitbake, before descriptions are provided for how they can be easily
included and further customisations enabled using build configs within
``meta-ewaol-config/kas``, for use by the kas build tool.

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
      Yocto layer, documented in :ref:`Image Validation`.

Provided their Yocto layer sources can be found by bitbake via
``conf/bblayers.conf``, these features can be enabled by passing them as a
space-separated list into ``DISTRO_FEATURES`` within ``conf/local.conf``.

``meta-ewaol`` repository also provides kas build config files that will enable
automatic fetch and inclusion of layer sources, as well as parameter and
feature specification for building the target images. Extra build config files
are further provided that enable a wider range of build options without manual
configuration. These are as follows.

kas Build Configurations
------------------------

The EWAOL quickstart guide illustrates how to build an EWAOL software image via
kas: :ref:`Minimal Image Build via kas`.

The ``meta-ewaol-config/kas`` directory contains build configs to support
building images via kas for the EWAOL project.

Build configs are modular, where combining config files will result in an image
produced with their combined configuration. Further, build configs files can
extend other build configs files, thereby enabling specialised configurations
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

* ``base.yml``

    Defines the image targets, layer dependencies and their software sources
    and build configuration variables.

* ``arm_machines.yml``

    Defines the BSPs, layers, and dependencies specific to the Arm reference
    platforms of the supported machines.

Build Modifiers
^^^^^^^^^^^^^^^

Build modifier config files specify additional sources and parameter
customisations relevant to a particular image feature.

There are currently two build modifier YAML files:

* ``tests.yml``

    Includes the Yocto Package Test (ptest) framework in the image, configures
    the inclusion of ``meta-ewaol-tests`` as a Yocto layer source for the
    build, and appends the ``ewaol-test`` feature as a ``DISTRO_FEATURE`` for
    the build. Additional documentation for the EWAOL tests layer is given in
    :ref:`Image Validation`.

* ``ci.yml``

    Considers the image build to be an image built as part of a Continuous
    Integration pipeline, causing the build process to delete its temporary
    work files following build completion.

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
          file: meta-ewaol-config/kas/base.yml
        - repo: meta-ewaol
          file: meta-ewaol-config/kas/tests.yml
        - repo: meta-ewaol
          file: meta-ewaol-config/kas/ewaol-v0.1.yml

    repos:
      meta-my-bsp-layer:

      meta-ewaol:
        url: https://<meta-ewaol-public-repo>
        refspec: v0.1

    machine: my-machine

To read more about how to customise this configuration file, check the
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