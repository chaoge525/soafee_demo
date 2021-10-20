Project Quickstart
##################

This documentation explains how to quickly get started with the EWAOL project.
For more information on building an image for the EWAOL project, see
:ref:`builds:Image Builds`.

.. _quickstart_build_host_setup:

Build Host Setup
****************

A number of dependencies are required to build projects with Yocto.
`The Yocto Project documentation`_ provides the list of essential packages to
be installed on the Build Host.

.. _The Yocto Project documentation:
   https://docs.yoctoproject.org/singleindex.html#required-packages-for-the-build-host

``meta-ewaol-config`` contains build configs for kas, a tool for easily setting
up bitbake based projects. Each build config is a YAML file that specifies
sources and parameter definitions which, when passed to kas, will be
automatically downloaded and configured in preparation for a subsequent build.
kas can also invoke the bitbake build process to condense everything necessary
to produce an image from the build config files into a single step.

On the Build Host, install the kas setup tool:

.. code-block:: console

    sudo -H pip3 install kas

For more details on kas installation, see `kas Dependencies & installation`_.

.. _kas Dependencies & installation: https://kas.readthedocs.io/en/latest/userguide.html#dependencies-installation

For more details on kas, see `kas Introduction`_.

.. _kas Introduction: https://kas.readthedocs.io/en/latest/intro.html

.. note::
  The Build Host machine should have at least 65 GBytes of free disk space for
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
:ref:`builds:Image Builds`.

.. _quickstart_minimal_image_build_via_kas:

Minimal Image Build via kas
***************************

This section describes how to build images for the EWAOL project for the
following machine:

- The Neoverse N1 System Development Platform (N1SDP), corresponding to the
  ``n1sdp`` ``MACHINE`` implemented in `meta-arm-bsp`_.

.. _meta-arm-bsp:
   https://git.yoctoproject.org/cgit/cgit.cgi/meta-arm/tree/meta-arm-bsp/documentation

Checkout the ``meta-ewaol`` repository:

.. code-block:: console

   mkdir -p ~/ewaol
   cd ~/ewaol
   git clone https://git.gitlab.arm.com/ewaol/meta-ewaol.git -b main
   cd meta-ewaol

Running kas with the build configurations within ``meta-ewaol-config`` will
build two images by default: one that includes the Docker container engine and
another one that includes the Podman container engine.

N1SDP
=====

To read documentation about the N1SDP board, check the
`N1SDP Technical Reference Manual`_.

.. _quickstart_build_for_n1sdp:

Build for N1SDP
---------------

To build the images via kas for the N1SDP board:

.. code-block:: console

   kas build meta-ewaol-config/kas/n1sdp.yml

The resulting images will be produced:

 - ``build/tmp/deploy/images/n1sdp/ewaol-image-docker-n1sdp.*``
 - ``build/tmp/deploy/images/n1sdp/ewaol-image-podman-n1sdp.*``

To build only one image corresponding to a particular container engine, specify
the ``--target`` (either ``ewaol-image-docker`` or ``ewaol-image-podman``) as
an option to the kas build command, as shown in the following example:

.. code-block:: console

   kas build --target ewaol-image-docker meta-ewaol-config/kas/n1sdp.yml

.. _quickstart_deploy_on_n1sdp:

Deploy on N1SDP
---------------

To deploy the image on N1SDP you will need a tool to copy an image using its
block map. In this tutorial, we will use ``bmap-tools`` which can be installed
on your host via the following command (example on Ubuntu based host):

.. code-block:: console

   sudo apt install bmap-tools

USB Storage Device
^^^^^^^^^^^^^^^^^^

The image is produced as files with the ``.wic.bmap`` and ``.wic.gz``
extensions. They are produced by building the default build target.

Prepare a USB disk (min size of 64 GB).
Identify the USB storage device using ``lsblk`` command:

.. code-block:: console

   lsblk
   NAME   MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
   sdc      8:0    0    64G  0 disk
   ...

.. note::
   In this example, the USB storage device is the ``/dev/sdc`` device. Be extra
   careful when copying and pasting the following commands.

Use ``bmap-tools`` to copy the image to USB disk (docker image in this example):

.. note::
   All partitions and data on the USB disk will be erased. Please backup before
   continuing.

.. code-block:: console

   sudo umount /dev/sdc*
   cd build/tmp/deploy/images/n1sdp/
   sudo bmaptool copy --bmap ewaol-image-docker-n1sdp.wic.bmap ewaol-image-docker-n1sdp.wic.gz /dev/sdc

Safely eject the USB storage device from the host PC and plug it onto one of
the USB 3.0 ports in the N1SDP.

Board's MCC configuration microSD card
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::
   This process doesn't need to be performed every time the
   `USB Storage Device` gets updated. You just need to update the MCC
   configuration microSD card when the EWAOL version changes.

1. Connect the USB-B cable to the DBG USB port of the N1SDP back panel.

2. Find four TTY USB devices in your ``/dev`` directory. Example:

.. code-block:: console

   ls /dev/ttyUSB*
   /dev/ttyUSB0
   /dev/ttyUSB1
   /dev/ttyUSB2
   /dev/ttyUSB3

By default the four ports are connected to the following devices:

 - ttyUSB<n> Motherboard Configuration Controller (MCC)
 - ttyUSB<n+1> Application processor (AP)
 - ttyUSB<n+2> System Control Processor (SCP)
 - ttyUSB<n+3> Manageability Control Processor (MCP)

In this guide the ports are:

 - ttyUSB0: MCC
 - ttyUSB1: AP
 - ttyUSB2: SCP
 - ttyUSB3: MCP

The ports are configured with the following settings:

 - 115200 Baud
 - 8N1
 - No hardware or software flow support

3. Connect to the MCC console. Any terminal applications such as  ``putty``,
   ``screen`` or ``minicom``  will work. In this guide, we use the  ``screen``
   command:

.. code-block:: console

   sudo screen /dev/ttyUSB0 115200

4. Turn the main power switch on the power supply of the N1SDP tower. The MCC
window will be shown. Type ``?`` to see MCC firmware version and a list of
commands:

.. code-block:: console

   Cmd> ?
    Arm N1SDP MCC Firmware v1.0.1
    Build Date: Sep  5 2019
    Build Time: 14:18:16
    + command ------------------+ function ---------------------------------+
    | CAP "fname" [/A]          | captures serial data to a file            |
    |                           |  [/A option appends data to a file]       |
    | FILL "fname" [nnnn]       | create a file filled with text            |
    |                           |  [nnnn - number of lines, default=1000]   |
    | TYPE "fname"              | displays the content of a text file       |
    | REN "fname1" "fname2"     | renames a file 'fname1' to 'fname2'       |
    | COPY "fin" ["fin2"] "fout"| copies a file 'fin' to 'fout' file        |
    |                           |  ['fin2' option merges 'fin' and 'fin2']  |
    | DEL "fname"               | deletes a file                            |
    | DIR "[mask]"              | displays a list of files in the directory |
    | FORMAT [label]            | formats Flash Memory Card                 |
    | USB_ON                    | Enable usb                                |
    | USB_OFF                   | Disable usb                               |
    | SHUTDOWN                  | Shutdown PSU (leave micro running)        |
    | REBOOT                    | Power cycle system and reboot             |
    | RESET                     | Reset Board using CB_nRST                 |
    | DEBUG                     | Enters debug menu                         |
    | EEPROM                    | Enters eeprom menu                        |
    | HELP  or  ?               | displays this help                        |
    |                                                                       |
    | THE FOLLOWING COMMANDS ARE ONLY AVAILABLE IN RUN MODE                 |
    |                                                                       |
    | CASE_FAN_SPEED "SPEED"    | Choose from SLOW, MEDIUM, FAST            |
    | READ_AXI "fname"          | Read system memory to file 'fname'        |
    |          "address"        | from address to end address               |
    |          "end_address"    |                                           |
    | WRITE_AXI "fname"         | Write file 'fname' to system memory       |
    |           "address"       | at address                                |
    +---------------------------+-------------------------------------------+
   Cmd>

Enable USB:

.. code-block:: console

   Cmd> USB_ON

5. Mount the N1SDP's internal microSD card over the DBG USB connection to your
host PC and copy the required files.

The microSD card is visible on your host PC as a disk device after issuing the
``USB_ON`` command in the MCC console, as performed in the previous step.
This can be found using the ``lsblk`` command:

.. code-block:: console

   lsblk
   NAME   MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
   sdb      8:0    0     2G  0 disk
   └─sdb1   8:1    0     2G  0 part

.. note::
   In this example, we need to mount the ``/dev/sdb1`` partition. Be extra
   careful when copying and pasting the following commands.

.. code-block:: console

   sudo umount /dev/sdb1
   sudo mkdir -p /tmp/sdcard
   sudo mount /dev/sdb1 /tmp/sdcard
   ls /tmp/sdcard
   config.txt   ee0316a.txt   LICENSES   LOG.TXT   MB   SOFTWARE

6. Wipe and extract the contents of
``build/tmp/deploy/images/n1sdp/n1sdp-board-firmware_primary.tar.gz``
onto the mounted microSD card:

.. code-block:: console

   sudo rm -rf /tmp/sdcard/*
   sudo tar --no-same-owner -xf \
      build/tmp/deploy/images/n1sdp/n1sdp-board-firmware_primary.tar.gz -C \
      /tmp/sdcard/ && sync
   sudo umount /tmp/sdcard
   sudo rmdir /tmp/sdcard

.. note::
   If the N1SDP board was manufactured after November 2019 (Serial Number
   greater than ``36253xxx``), a different PMIC firmware image must be used to
   prevent potential damage to the board. More details can be found in
   `Potential firmware damage notice`_. The ``MB/HBI0316A/io_v123f.txt`` file
   located in the microSD needs to be updated. To update it, set the PMIC image
   (``300k_8c2.bin``) to be used in the newer models by running the following
   commands on your host PC:

   .. code-block:: console

      sudo umount /dev/sdb1
      sudo mkdir -p /tmp/sdcard
      sudo mount /dev/sdb1 /tmp/sdcard
      sudo sed -i '/^MBPMIC: pms_0V85.bin/s/^/;/g' /tmp/sdcard/MB/HBI0316A/io_v123f.txt
      sudo sed -i '/^;MBPMIC: 300k_8c2.bin/s/^;//g' /tmp/sdcard/MB/HBI0316A/io_v123f.txt
      sudo umount /tmp/sdcard
      sudo rmdir /tmp/sdcard

7. Power on the main SoC using the MCC console:

.. code-block:: console

    Cmd> REBOOT

Run on N1SDP
------------

To run the image, connect to the AP console by running the following command
from a terminal in your host PC:

.. code-block:: console

   sudo screen /dev/ttyUSB1 115200

Then, log-in as ``root`` without password.

Tests on N1SDP
--------------

* To build an image with tests included please refer to
  :ref:`validations_n1sdp_build_image_including_tests`.
* To execute tests please refer to :ref:`validations_n1sdp_running_tests`.

.. _Potential firmware damage notice: https://community.arm.com/developer/tools-software/oss-platforms/w/docs/604/notice-potential-damage-to-n1sdp-boards-if-using-latest-firmware-release
.. _N1SDP Technical Reference Manual: https://developer.arm.com/documentation/101489/0000
