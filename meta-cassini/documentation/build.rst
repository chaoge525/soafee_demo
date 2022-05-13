..
 # Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
 #
 # SPDX-License-Identifier: MIT

########################################
Build, Deploy and validate Cassini Image
########################################

The recommended approach for image build setup and customization is to use the
`kas build tool`_. To support this, Cassini provides configuration files to
setup and build different target images, different distribution image features,
and set associated parameter configurations.

This page first briefly describes below the kas configuration files provided
with Cassini, before guidance is given on using those kas configuration files
to set up the Cassini distribution on a target platform.

.. note::
  All command examples on this page can be copied by clicking the copy button.
  Any console prompts at the start of each line, comments, or empty lines will
  be automatically excluded from the copied text.

The ``meta-cassini-config/kas`` directory contains kas configuration files to
support building and customizing Cassini distribution images via kas. These kas
configuration files contain default parameter settings for a Cassini distribution
build. Here, the files are briefly introduced, classified into three ordered
categories:

  * **Base Config**: Configures common software components

    * ``cassini.yml`` to prepare an image for the Cassini distribution.

  * **Build Modifier Configs**: Set and configure features of the Cassini
    distribution

    * ``tests.yml`` to include run-time validation tests into the image.
    * ``cassini-sdk.yml`` to build an SDK image for the Cassini distribution.
    * ``security.yml`` to build a security-hardened Cassini distribution image.

  * **Target Platform Configs**: Set the target platform

    Cassini currently supports the The Neoverse N1 System Development Platform
    (N1SDP), corresponding to the ``n1sdp`` ``MACHINE`` implemented in
    |meta-arm-bsp|_.
    A single Target Platform Config is therefore provided:

      * ``n1sdp.yml`` to select the N1SDP as the target platform.

    To read documentation about the N1SDP, see the
    |N1SDP Technical Reference Manual|_.

These kas configuration files can be used to build a custom Cassini distribution
by passing one **Base Config**, zero or more **Build Modifier Configs**,
and one **Target Platform Config** to the kas build tool, chained via a colon
(:) character. Examples for this are given later in this document.

In the next section, guidance is provided for configuring, building and
deploying Cassini distributions using these kas configuration files.

****************************
Build Host Environment Setup
****************************

This documentation assumes an Ubuntu-based Build Host, where the build steps
have been validated on the Ubuntu 18.04.6 LTS Linux distribution.

A number of package dependencies must be installed on the Build Host to run
build scenarios via the Yocto Project. The Yocto Project documentation
provides the |list of essential packages|_ together with a command for their
installation.

The recommended approach for building Cassini is to use the kas build tool. To
install kas:

.. code-block:: console
  :substitutions:

  sudo -H pip3 install --upgrade kas==|kas version|

For more details on kas installation, see |kas Dependencies & installation|_.

To deploy an Cassini distribution image onto the supported target platform,
``bmap-tools`` is used. This can be installed via:

.. code-block:: console

   sudo apt install bmap-tools

.. note::
  The Build Host should have at least 65 GBytes of free disk space to build a
  Cassini distribution image.

********
Download
********

The ``meta-cassini`` repository can be downloaded using Git, via:

.. code-block:: shell
  :substitutions:

  # Change the tag or branch to be fetched by replacing the value supplied to
  # the --branch parameter option

  mkdir -p ~/cassini
  cd ~/cassini
  git clone |meta-ewaol remote| --branch |meta-cassini branch|
  cd meta-ewaol

*****
Build
*****

To build Cassini distribution image for the N1SDP hardware target platform:

  .. code-block:: console

    kas build meta-cassini/meta-cassini-config/kas/cassini.yml:meta-cassini/meta-cassini-config/kas/n1sdp.yml

  The resulting Cassini distribution image will be produced at:
  ``build/tmp/deploy/images/n1sdp/cassini-image-base-n1sdp.*``

To build Cassini distribution image with the Cassini SDK for the N1SDP
hardware target platform:

  .. code-block:: console

    kas build meta-cassini-config/kas/cassini-sdk.yml:meta-cassini-config/kas/n1sdp.yml

  The resulting Cassini distribution image will be produced at:
  ``build/tmp/deploy/images/n1sdp/cassini-image-sdk-image-n1sdp.*``

Cassini distribution images can be modified by adding run-time
validation tests and security hardening to the distribution. This can be done
by including ``meta-cassini-config/kas/tests.yml`` and
``meta-cassini-config/kas/security.yml`` kas configuration file as a Build
Modifier.

******
Deploy
******

Instructions for deploying a Cassini distribution image on the supported N1SDP
hardware target platform is divided into two parts:

  * `Load the Image onto an USB Storage Device`_
  * `Update the N1SDP MCC Configuration MicroSD Card`_

.. note::
  As the image filenames vary depending on the base config and the SDK, the
  precise commands to deploy a Cassini distribution image vary. The following
  documentation denotes required instructions with sequentially numbered
  indexes (e.g., 1, 2, ...), and distinguishes alternative instructions by
  denoting the alternatives alphabetically (e.g., A, B, ...).

Load the Image onto an USB Storage Device
=========================================

Cassini distribution images are produced as files with the ``.wic.bmap`` and
``.wic.gz`` extensions. They must first be loaded to the USB storage device, as
follows:

1. Prepare the USB storage device (minimum size of 64 GB).

  Identify the USB storage device using ``lsblk`` command:

  .. code-block:: shell

    lsblk

  This will output, for example:

  .. code-block:: console

    NAME   MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
    sdc      8:0    0    64G  0 disk
    ...

.. warning::
  In this example, the USB storage device is the ``/dev/sdc`` device. As this
  may vary on different machines, care should be taken when copying and pasting
  the following commands.

2. Prepare for the image copy:

  .. code-block:: console

    sudo umount /dev/sdc*
    cd build/tmp/deploy/images/n1sdp/

.. warning::
  The next step will result in all prior partitions and data on the USB storage
  device being erased. Please backup before continuing.

3. Flash the image onto the USB storage device using ``bmap-tools``:

  A. Cassini distribution image:

    .. code-block:: console

      sudo bmaptool copy --bmap cassini-image-base-n1sdp.wic.bmap cassini-image-base-n1sdp.wic.gz /dev/sdc

  B. Cassini-SDK distribution image:

    .. code-block:: console

      sudo bmaptool copy --bmap cassini-image-sdk-n1sdp.wic.bmap cassini-image-sdk-n1sdp.wic.gz /dev/sdc

The USB storage device can then be safely ejected from the Build Host, and
plugged into one of the USB 3.0 ports on the N1SDP.

Update the N1SDP MCC Configuration MicroSD Card
===============================================

.. note::
  This process doesn't need to be performed every time the USB Storage Device
  gets updated. It is only necessary to update the MCC configuration microSD
  card when the Cassini major version changes.

This guidance requires a physical connection able to be established between the
N1SDP and a PC that can be used to interface with it, here assumed to be the
Build Host. The instructions are as follows:

1. Connect a USB-B cable between the Build Host and the DBG USB port of the
   N1SDP back panel.

2. Find four TTY USB devices in the ``/dev`` directory of the Build Host, via:

  .. code-block:: shell

    ls /dev/ttyUSB*

  This will output, for example:

  .. code-block:: console

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

3. Connect to the N1SDP's MCC console. Any terminal applications such as
   ``putty``, ``screen`` or ``minicom``  will work. The  ``screen`` utility is
   used in the following command:

  .. code-block:: shell

    sudo screen /dev/ttyUSB0 115200

4. Power-on the N1SDP via the power supply switch on the N1SDP tower. The MCC
   window will be shown. Type the following command at the ``Cmd>`` prompt to
   see MCC firmware version and a list of commands:

  .. code-block:: console

    ?

  This will output, for example:

  .. code-block:: console

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

5. In the MCC window at the ``Cmd>`` prompt, enable USB via:

  .. code-block:: console

    USB_ON

6. Mount the N1SDP's internal microSD card over the DBG USB connection to the
   Build Host and copy the required files.

  The microSD card is visible on the Build Host as a disk device after issuing
  the ``USB_ON`` command in the MCC console, as performed in the previous step.
  This can be found using the ``lsblk`` command:

  .. code-block:: shell

    lsblk

  This will output, for example:

  .. code-block:: console

    NAME   MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
    sdb      8:0    0     2G  0 disk
    └─sdb1   8:1    0     2G  0 part

  .. warning::
    In this example, the ``/dev/sdb1`` partition is being mounted. As this
    may vary on different machines, care should be taken when copying and
    pasting the following commands.

  Mount the device and check its contents:

  .. code-block:: console

    sudo umount /dev/sdb1
    sudo mkdir -p /tmp/sdcard
    sudo mount /dev/sdb1 /tmp/sdcard
    ls /tmp/sdcard

  This should output, for example:

  .. code-block:: console

    config.txt   ee0316a.txt   LICENSES   LOG.TXT   MB   SOFTWARE

7. Wipe the mounted microSD card, then extract the contents of
   ``n1sdp-board-firmware_primary.tar.gz`` onto it:

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
    commands on the Build Host:

    .. code-block:: console

      sudo umount /dev/sdb1
      sudo mkdir -p /tmp/sdcard
      sudo mount /dev/sdb1 /tmp/sdcard
      sudo sed -i '/^MBPMIC: pms_0V85.bin/s/^/;/g' /tmp/sdcard/MB/HBI0316A/io_v123f.txt
      sudo sed -i '/^;MBPMIC: 300k_8c2.bin/s/^;//g' /tmp/sdcard/MB/HBI0316A/io_v123f.txt
      sudo umount /tmp/sdcard
      sudo rmdir /tmp/sdcard

***
Run
***

To run the deployed Cassini distribution image, simply boot the target platform.
For example, on the MCC console accessed via the connected machine described in
`Deploy`_, reset the target platform and boot into the deployed Cassini
distribution image via:

  .. code-block:: console

    REBOOT

The resulting Cassini distribution image can be logged into as ``cassini`` user.

The distribution can then be used for deployment and orchestration of
application workloads in order to achieve the desired use-cases.

********
Validate
********

As an initial validation step, check that the appropriate Systemd services are
running successfully,

  * ``docker.service``
  * ``k3s.service``

  These services can be checked by running the command:

    .. code-block:: console

      systemctl status --no-pager --lines=0 docker.service k3s.service

  And ensuring the command output lists them as active and running.

More thorough run-time validation of Cassini components are provided as a series
of integration tests, available if the ``meta-cassini-config/kas/tests.yml`` kas
configuration file was included in the image build.

*********************************
Reproducing the Cassini Use-Cases
*********************************

This section briefly demonstrates simplified use-case examples, where detailed
instructions for developing, deploying, and orchestrating application workloads
are left to the external documentation of the relevant technology.

Deploying Application Workloads via Docker and K3s
==================================================

This example deploys the |Nginx|_ webserver as an application workload, using
the ``nginx`` container image available from Docker's default image repository.
The deployment can be achieved either via Docker or via K3s, as follows:

  1. Boot the image and log-in as ``cassini`` user.

  2. Deploy the example application workload:

     * **Deploy via Docker**

       2.1. Run the following example command to deploy via Docker:

            .. code-block:: console

              sudo docker run -p 8082:80 -d nginx

       2.2. Confirm the Docker container is running by checking its ``STATUS``
       in the container list:

            .. code-block:: console

              sudo docker container list

     * **Deploy via K3s**

       2.1. Run the following example command to deploy via K3s:

            .. code-block:: console

              cat << EOT > nginx-example.yml && sudo kubectl apply -f nginx-example.yml
              apiVersion: v1
              kind: Pod
              metadata:
                name: k3s-nginx-example
              spec:
                containers:
                - name: nginx
                  image: nginx
                  ports:
                  - containerPort: 80
                    hostPort: 8082
              EOT

       2.2. Confirm that the K3s Pod hosting the container is running by
       checking that its ``STATUS`` is ``running``, using:

            .. code-block:: console

              sudo kubectl get pods -o wide

  3. After the Nginx application workload has been successfully deployed, it can
     be interacted with on the network, via for example:

     .. code-block:: console

       wget localhost:8082

.. note::
  As both methods deploy a webserver listening on port 8082, the two methods
  cannot be run simultaneously and one deployment must be stopped before the
  other can start.
