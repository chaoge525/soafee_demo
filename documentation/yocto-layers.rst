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
    * ``tools``

meta-ewaol-config
^^^^^^^^^^^^^^^^^

Provides kas configurations files for building EWAOL images.

meta-ewaol-distro
^^^^^^^^^^^^^^^^^

Yocto distribution layer providing top-level and general policies for the EWAOL
images. For more details, please see :ref:`High-Level Architecture`.

meta-ewaol-tests
^^^^^^^^^^^^^^^^

Yocto layer with recipes including tests to validate EWAOL functionalities.

meta-ewaol-bsp
^^^^^^^^^^^^^^

BSP layer extending other BSP layers to fulfil EWAOL requirements:

* SystemReady configuration and adaptation if required. Ideally should be done
  in ``meta-arm-bsp``
