Image Builds
============

The ``meta-ewaol`` repository provides build targets for both architectures
(see :ref:`overview_high-level_architecture`):

  * ``ewaol-baremetal-image`` for baremetal architecture.
  * ``ewaol-virtualization-image`` for virtualization architecture, available
    only if ``ewaol-virtualization`` is defined in ``DISTRO_FEATURES``.

Both images include the Docker container engine to facilitate containerized
workload orchestration on the edge and the K3s orchestration package, provided
by the ``meta-virtualization`` Yocto layer.

On a baremetal image, the K3s package is provided with a systemd service that
auto-starts on image boot and runs the K3s server. This K3s server may be
interacted with via the Kubernetes REST API or via the Kubernetes command-line
tool ``kubectl`` (see `Kubernetes API Overview`_ and `kubectl Overview`_ for
usage instructions). Enabling and disabling the systemd service via ``systemctl
[start|stop] k3s`` will bring up or shut down the K3s server running on the
image, meaning K3s-deployed containers may remain running (without
orchestration) after stopping the systemd service. To avoid containers running
after stopping the server, they should be disabled prior to stopping the server
via the Kubernetes API or command-line tool. Alternatively, the provided
``k3s-killall.sh`` script may be used to stop all running containers even after
the K3s server has been disabled.

.. note::
    Example usage of the K3s orchestration package is provided in the form of
    the K3s integration test suite implementation, documented in
    :ref:`validations:Image Validation`.

.. _Kubernetes API Overview: https://kubernetes.io/docs/reference/using-api/
.. _kubectl Overview: https://kubernetes.io/docs/reference/kubectl/overview/

On a virtualization image, the software stack includes the Xen type-1 hypervisor
and provides a Control VM (Dom0) and a single bundled Guest VM (DomU), by
default. Virtualization support also includes Xen-related configuration for the
kernel image and all necessary packages for the Control VM and Guest VM root
filesystems. Both VMs include the Docker container engine and K3s container
orchestration. On a virtualization image, the same systemd service which is
provided on a baremetal image is deployed to the Control VM
(``k3s-server.service``), but a different systemd service which runs a K3s agent
is deployed to the Guest VM (``k3s-agent.service``). Additional run-time
configuration is required to connect the agent to the server, see
:ref:`validations:Image Validation` for details. The Control VM also includes
the ``xen-tools`` package along with network configuration for the ``xenbr0``
bridge, to allow the Guest VM to access the external network. More details are
provided in `Virtualization Image Build`_. The Guest VM image is based on the
``generic-arm64`` ``MACHINE``.

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

The currently supported ``MACHINE`` is:

* ``n1sdp``

The currently supported ``DISTRO_FEATURES`` are:

* ``ewaol-devel``
* ``ewaol-test``
* ``ewaol-sdk``
* ``ewaol-virtualization``

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
      and image features to support software development on the target. For
      more details on the SDK, see
      `Software Development Kit (SDK) Image Build`_.

* ``ewaol-virtualization``

    * Adds the Xen hypervisor into the software stack.
    * Provides an additional build target ``ewaol-virtualization-image``.
    * Enables Xen specific configs required by kernel.
    * Includes all necessary packages and adjustments to the Control VM's root
      filesystem to support management of Xen Guest VMs.

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
:ref:`quickstart_ewaol_image_build_via_kas`.

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

``meta-ewaol-config`` currently provides a single machine build config:

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
    platform of the supported machine.

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
    the EWAOL SDK is given in `Software Development Kit (SDK) Image Build`_.

* ``virtualization.yml``

    Appends ``ewaol-virtualization`` to the ``DISTRO_FEATURES`` and selects the
    virtualization image as the build target. If this config file is not
    provided, the default image built by kas will be the baremetal image.
    The Control VM and Guest VM images can be customized, see
    `Virtualization Image Build`_ for details.

.. note::
  If a kas build config does not set a build parameter, the parameter will
  take the default value. For example, if ``tests.yml`` is not included then
  the value of ``DISTRO_FEATURES`` will take its default value as specified
  earlier in this document.

Adding External Machines and BSP Layers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to add an external machine to be built with EWAOL, you need to add a
``my-machine.yml`` kas configuration file (where ``my-machine`` is the
``MACHINE`` name of the external machine) to your Yocto BSP layer:
``meta-my-bsp-layer``. This file should have the following structure:

.. code-block:: yaml

    header:
      version: 11
      includes:
        - repo: meta-ewaol
          file: meta-ewaol-config/kas/ewaol-base.yml
        - repo: meta-ewaol
          file: meta-ewaol-config/kas/tests.yml

    repos:
      meta-my-bsp-layer:

      meta-ewaol:
        url: https://git.gitlab.arm.com/ewaol/meta-ewaol.git
        refspec: main

    machine: my-machine

To read more about how to customize this configuration file, check the
`Kas documentation`_. Images for ``my-machine`` can be built by running the
following kas command:

.. code-block:: console

    kas build meta-my-bsp-layer/my-machine.yml

.. _Kas documentation: https://kas.readthedocs.io/en/latest/userguide.html#including-configuration-files-from-other-repos

Build Validation
----------------

Kernel Configuration Check
^^^^^^^^^^^^^^^^^^^^^^^^^^

After the kernel configuration has been produced, it is checked to validate the
presence of the kernel config, e.g: necessary for the resulting image to run
container instances.

The list of required kernel configs is compared against the list of available
configs in the kernel. They all need to be present either as module (=m) or
built-in (=y). A bitbake warning is produced if the kernel is not configured
correctly.

The following kernel configs checks are performed:

* For container engine support it is done via:
  ``meta-ewaol-distro/classes/containers_kernelcfg_check.bbclass``. By default
  `Yocto docker config`_ is used as the reference.

* For K3s container orchestration support, it is done via:
  ``meta-ewaol-distro/classes/k3s_kernelcfg_check.bbclass``.
  By default `Yocto K3s config`_ is used as the reference.

* For virtualization images, the Xen related configs is
  done via: ``meta-ewaol-distro/classes/xen_kernelcfg_check.bbclass``.
  By default `Yocto Xen config`_ is used as the reference.

.. _Yocto docker config: http://git.yoctoproject.org/cgit/cgit.cgi/yocto-kernel-cache/tree/features/docker/docker.cfg
.. _Yocto K3s config: http://git.yoctoproject.org/cgit/cgit.cgi/meta-virtualization/tree/recipes-kernel/linux/linux-yocto/kubernetes.cfg
.. _Yocto Xen config: http://git.yoctoproject.org/cgit/cgit.cgi/yocto-kernel-cache/tree/features/xen/xen.cfg

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
        * meta-openembedded/meta-python
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

        ``DISTRO_FEATURES:append = " ewaol-test"``

.. note::
  The kas build configuration YAML files within the ``meta-ewaol-config/kas/``
  directory define how the build will be prepared by the kas build tool. Any
  specific functionalities not described in this section may therefore be
  enabled by reading these configuration files and manually inserting their
  changes into the build configuration folder.

Software Development Kit (SDK) Image Build
------------------------------------------

.. note::
  Please note that the SDK image requires at least 110 GBytes of free disk
  space to build!

EWAOL SDK images enable users to perform common development tasks on the target,
such as:

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
target to ``ewaol-baremetal-image-sdk``. For more details about selecting
configuration files for kas, see: :ref:`quickstart_build_host_setup`.

For example, to build the SDK images for the N1SDP via kas:

.. code-block:: console

  kas build meta-ewaol-config/kas/n1sdp.yml:meta-ewaol-config/kas/sdk.yml

In this example, the SDK produced image by the kas build will be found at:
``build/tmp/deploy/images/n1sdp/ewaol-baremetal-image-sdk-n1sdp.*``.
To deploy the generated image, please refer to the
:ref:`quickstart_deploy_on_n1sdp` section.

Virtualization Image Build
--------------------------

.. note::
  Please note that an ``ewaol-virtualization-image`` requires at least 100
  GBytes of free disk space to build!

A virtualization image includes the Xen hypervisor into the EWAOL software
stack. To build a virtualization image for the ``n1sdp`` machine, with a Guest
VM based on the ``generic-arm64`` ``MACHINE``, `Multiple Configuration Build`_
is used. Configurable build-time variables for the Guest VM are defined
within the ``meta-ewaol-distro/conf/multiconfig/ewaol-guest-vm.conf`` file.

The Guest VM is included into the EWAOL Virtualization Image via the
``ewaol-guest-vm-package`` recipe, with the Guest VM's rootfs stored as a raw
image file in ``*.qcow2`` format. In addition, this package includes a sample
Xen domain configuration file, which holds the customizable Guest VM settings as
detailed in `xl domain configuration`_. By default one Guest VM (with hostname
``ewaol-guest-vm1``) is built and included on the virtualization image, but this
number can be customized, as described in `Multiple EWAOL Guest VM Instances`_.

The Control VM and Guest VMs can be customized via a set of environment
variables. The following list shows the available environment variables and
their default values, configuring one VM instance:

.. _vm-vars:

.. code-block:: yaml

   EWAOL_GUEST_VM_INSTANCES: "1"                      # Number of Guest VM instances
   EWAOL_GUEST_VM1_NUMBER_OF_CPUS: "4"                # Number of CPUs for Guest VM1
   EWAOL_GUEST_VM1_MEMORY_SIZE: "6144"                # Memory size for Guest VM1 (MB)
   EWAOL_GUEST_VM1_ROOTFS_EXTRA_SPACE: ""             # Extra storage space for Guest VM1 (KB)
   EWAOL_CONTROL_VM_MEMORY_SIZE: "2048"               # Memory size for Control VM (MB)
   EWAOL_CONTROL_VM_ROOTFS_EXTRA_SPACE: "1000000"     # Extra storage space for Control VM (KB)
   EWAOL_ROOTFS_EXTRA_SPACE: "2000000"                # Extra storage space for the Control VM and each Guest VM (KB)

.. note::
  Guest VM instances may be independently customized, where the above list only
  shows the variables for the default case of a single Guest VM. See
  `Multiple EWAOL Guest VM Instances`_ for configuring additional Guest VMs.

The variables may be set either within an included kas configuration file
(see ``meta-ewaol-config/kas/virtualization.yml`` for example usage), or
directly in the build environment. The ``EWAOL_*_ROOTFS_EXTRA_SPACE`` variables
apply their values to the relevant ``IMAGE_ROOTFS_EXTRA_SPACE`` bitbake
variable.

To build the virtualization image, pass
``meta-ewaol-config/kas/virtualization.yml`` to the kas build command. For
example:

.. code-block:: shell

  kas build meta-ewaol-config/kas/n1sdp.yml:meta-ewaol-config/kas/virtualization.yml

.. _xl domain configuration:
  https://xenbits.xen.org/docs/4.16-testing/man/xl.cfg.5.html

.. _Multiple Configuration Build:
  https://docs.yoctoproject.org/3.3.2/dev-manual/common-tasks.html#building-images-for-multiple-targets-using-multiple-configurations

Multiple EWAOL Guest VM Instances
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Multiple EWAOL Guest VM instances can be included on the virtualization image,
each one based on the same kernel and image recipe.

The number of Guest VM instances built for and included on the virtualization
image can be set via the ``EWAOL_GUEST_VM_INSTANCES`` variable, which is listed
:ref:`here<vm-vars>` along with its default value.

Guest VM instances can be independently configured via Bitbake variables which
reference the Guest VM's integer instance index. For example, variables with a
prefix ``EWAOL_GUEST_VM1_`` apply to the first Guest VM, variables with a prefix
``EWAOL_GUEST_VM2_`` apply to the second Guest VM, and so on. All Guest VM
instances use the same default configuration, apart from the hostname, which is
based on their instance index: ``ewaol-guest-vm1`` for the first,
``ewaol-guest-vm2`` for the second, and so on. An example of configuring a
second Guest VM instance using the kas tool is given in
``meta-ewaol-config/kas/second-vm-parameters.yml``, although these variables
will only be used if ``EWAOL_GUEST_VM_INSTANCES`` is set to build two or more
Guest VMs.
