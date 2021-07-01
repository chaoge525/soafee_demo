Yocto Layers
============


Layers Dependency Diagram
-------------------------

.. image:: images/ewaol_layers_deps_diagram.png

meta-arm
^^^^^^^^

* URL: https://git.yoctoproject.org/cgit/cgit.cgi/meta-arm/tree/meta-arm
* Clean separation between Firmware and OS
* The canonical source for SystemReady firmware

meta-arm-bsp
^^^^^^^^^^^^

* URL: https://git.yoctoproject.org/cgit/cgit.cgi/meta-arm/tree/meta-arm-bsp
* Board specific components for Arm's platforms targets
* Can be replaced by ``meta-<SiP>-bsp``

meta-ewaol
^^^^^^^^^^

* Umbrella repository containing EWAOL layers and documentation with the
  following directory structure:

  * ``meta-ewaol``

    * ``meta-ewaol-config``
    * ``meta-ewaol-distro``
    * ``meta-ewaol-tests``
    * ``meta-ewaol-bsp`` (only implemented if BSP adaptations are required)
    * ``documentation``

meta-ewaol-config
^^^^^^^^^^^^^^^^^

Provides kas and build configurations files and scripts for building EWAOL
images in a CI environment, as well as tooling for code, license, commit
message and spell checks.

meta-ewaol-distro
^^^^^^^^^^^^^^^^^

Yocto distribution layer providing top-level and general policies for the EWAOL
images:

* Based on ``poky.conf`` distro
* RPM package management system
* Systemd as Init system
* Build targets definition
  (e.g.: image recipes, images flavours, preferred providers and distro
  features)

  * development image
  * Docker and Podman images
  * Hello-world container image generation
  * test image

meta-ewaol-tests
^^^^^^^^^^^^^^^^

Yocto layer to validate EWAOL functionalities implementation:

* Container engine and run-time integration tests
* Tools for validation of external BSP layers as EWAOL compatible

  * External layers can use ``meta-ewaol-bsp`` as a reference implementation

meta-ewaol-bsp
^^^^^^^^^^^^^^

BSP layer extending other BSP layers to fulfil EWAOL requirements:

* SystemReady configuration and adaptation if required. Ideally should be done
  in ``meta-arm-bsp``
