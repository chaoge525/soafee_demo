Project Quickstart
==================

This documentation explains how to quickly get started with the EWAOL project.
For more information on building an image for the EWAOL project, see
:ref:`Image Builds`.

Build Host Setup
----------------

A number of dependencies are required to build projects with Yocto.
`The Yocto Project documentation`_ provides the list of essential packages to
be installed on the Build Host.

.. _The Yocto project documentation:
   https://docs.yoctoproject.org/3.3.1/singleindex.html#required-packages-for-the-build-host

``meta-ewaol-config`` contains build configs for kas, a tool for easily setting
up bitbake based projects. Each build config is a YAML file that specifies
sources and parameter definitions which, when passed to kas, will be
automatically downloaded and configured in preparation for a subsequent build.
kas can also invoke the bitbake build process to condense everything necessary
to produce an image from the build config files into a single step.

On the Build Host, install the kas setup tool:

.. code-block:: console

    pip3 install --user kas

For more details on kas, see `kas Introduction`_:

.. _kas Introduction: https://kas.readthedocs.io/en/latest/intro.html

.. note::
  The Build Host machine should have at least 50 GBytes of free disk space for
  the next steps to work correctly.

Build configuration YAML files can then be built via kas by running:

.. code-block:: console

   kas build config.yml

Multiple build configurations can be chained via a colon (:) character to
build an image with the sources and configuration defined in both, for example:

.. code-block:: console

  kas build config_one.yml:config_two.yml

Multiple distinct builds can be run in sequence by providing space-separated
build config arguments to kas.

The build configurations and the distribution features available for EWAOL
project builds within ``meta-ewaol`` repository are described in:
:ref:`Image Builds`.

Minimal Image Build via kas
---------------------------

This section describes how to build images for the EWAOL project for an
example target machine.

The machine used in this example is the Armv8-A Base RevC AEM FVP machine,
corresponding to the ``fvp-base`` ``MACHINE`` implemented in `meta-arm-bsp`_.
The FVP binary package is available for download from
`Arm Architecture Models`_ as "Armv-A Base RevC AEM FVP".

.. _meta-arm-bsp:
   https://git.yoctoproject.org/cgit/cgit.cgi/meta-arm/tree/meta-arm-bsp/documentation/fvp-base.md
.. _Arm Architecture Models:
   https://developer.arm.com/tools-and-software/simulation-models/fixed-virtual-platforms/arm-ecosystem-models

Checkout the ``meta-ewaol`` repository:

.. code-block:: console

   mkdir -p ~/ewaol
   cd ~/ewaol
   git clone <meta-ewaol-public-repo> -b hardknott

Running kas with the build configurations within ``meta-ewaol-config`` will
build two images by default: one that includes the Docker container engine and
another one that includes the Podman container engine.


To build these images via kas for the FVP-Base machine:

.. code-block:: console

   kas build meta-ewaol/meta-ewaol-config/kas/fvp-base.yml

The resulting images will be produced:
 - ``build/tmp/deploy/images/fvp-base/ewaol-image-docker-fvp-base.*``
 - ``build/tmp/deploy/images/fvp-base/ewaol-image-podman-fvp-base.*``

To build only one image corresponding to a particular container engine, specify
the ``--target`` (either ``ewaol-image-docker`` or ``ewaol-image-podman``) as
an option to the kas build command, as shown in the following example:

.. code-block:: console

   kas build --target ewaol-image-docker meta-ewaol/meta-ewaol-config/kas/fvp-base.yml
