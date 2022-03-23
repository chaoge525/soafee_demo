..
 # Copyright (c) 2022, Arm Limited.
 #
 # SPDX-License-Identifier: MIT

Extend
======

This section of the User Guide describes how to extend EWAOL in order to
configure and build it for deployment on custom or unsupported target platforms,
via kas.

Porting EWAOL to a Custom or Unsupported Target Platform via kas
----------------------------------------------------------------

To build an EWAOL distribution image that targets an externally defined target
platform using ``meta-ewaol``, a kas configuration file must be defined and
added to the external Yocto BSP or application layer. For example,
``my-machine.yml`` (where ``my-machine`` is the ``MACHINE`` name of the custom
or unsupported target platform) defined in a custom BSP layer
``meta-my-bsp-layer`` should have the following structure to build a baremetal
distribution image:

.. code-block:: yaml

    header:
      version: 11
      includes:
        - repo: meta-ewaol
          file: meta-ewaol-config/kas/baremetal.yml
        - repo: meta-ewaol
          file: meta-ewaol-config/kas/tests.yml

    repos:
      meta-my-bsp-layer:

      meta-ewaol:
        url: https://git.gitlab.arm.com/ewaol/meta-ewaol.git
        refspec: honister-dev

    machine: my-machine

This example kas configuration file for the ``my-machine`` target platform
defines the Yocto project configuration build via the kas configuration files
that are added in the ``includes`` section. These inclusions can be customized
in order to build a different image. For example, to build a virtualization
distribution image with run-time validation tests, include
``meta-ewaol-config/kas/virtualization.yml`` instead of
``meta-ewaol-config/kas/baremetal.yml`` in the above example.

Images for ``my-machine`` can then be built using this example kas configuration
file by running the following kas command:

.. code-block:: console

    kas build meta-my-bsp-layer/my-machine.yml
