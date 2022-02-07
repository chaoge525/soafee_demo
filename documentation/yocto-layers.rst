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

    * ``meta-ewaol-bsp``
    * ``meta-ewaol-config``
    * ``meta-ewaol-distro``
    * ``meta-ewaol-tests``
    * ``documentation``
    * ``tools``

meta-ewaol-bsp
^^^^^^^^^^^^^^

Yocto layer with machine specific extensions for particular EWAOL images.
Currently this layer extends the ``n1sdp`` machine definition from the
``meta-arm-bsp`` layer for EWAOL virtualization images. The ``meta-ewaol-bsp``
layer contains an additional grub configuration file with Xen boot entry and a
custom kickstart ``ewaol-virtualization-n1sdp-efidisk.wks.in`` file. There is
also a ``xen-devicetree.bb`` recipe, to generate a devicetree with extra modules
nodes required by Xen to start the Control VM (Dom0). In addition, the Xen
devicetree together with a Xen efi binary are included into the final wic image
in the ``boot`` partition.

meta-ewaol-config
^^^^^^^^^^^^^^^^^

Provides kas configurations files for building EWAOL images.

meta-ewaol-distro
^^^^^^^^^^^^^^^^^

Yocto distribution layer providing top-level and general policies for the EWAOL
images. For more details, please see :ref:`overview_high-level_architecture`.

meta-ewaol-tests
^^^^^^^^^^^^^^^^

Yocto layer with recipes including tests to validate EWAOL functionalities.
