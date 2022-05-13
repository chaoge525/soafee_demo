..
 # Copyright (c) 2022, Arm Limited.
 #
 # SPDX-License-Identifier: MIT

###########################
Migrating to Later Releases
###########################

This page describes guidance for updating a user's build environment and
processes from those required to use a previous EWAOL release, to instead setup
and use a later EWAOL release, as part of a migration process.

Details of the EWAOL release process can be found at
:ref:`Codeline Management <codeline_management:Codeline Management>`, and a
summary of each release can be found at
:ref:`Changelog & Release Notes <changelog:Changelog & Release Notes>`.

The following migration guidance is described such that the required changes are
with respect to the previous EWAOL release. The processes are categorized
according to the associated section of the user-guide documentation.

***************************
To |v1.0:migration version|
***************************

After following the below guidance to transition to EWAOL
:substitution-code:`|v1.0:migration version|`, boot the resulting image to run
and validate the release.

EWAOL Reproduce Migration
=========================

Build Host Setup
----------------

* The list of essential packages and package versions for the associated release
  of the Yocto Project was updated. Refer to the
  |list of essential packages|_ documentation to ensure the necessary
  packages are installed and upgraded to support the migration.

* The supported version of the ``kas`` build tool was updated to
  :substitution-code:`|v1.0:kas version|`. See
  :ref:`Build Host Environment Setup<user_guide_reproduce_environment_setup>`
  for guidance on installing this version of ``kas``.

Download
--------

* To migrate to :substitution-code:`|v1.0:migration version|`, it is necessary
  to download that version of the ``meta-ewaol`` repository source. To do this,
  either clone the repository into a new directory by following the instructions
  given in :ref:`Download<user_guide_reproduce_download>`, or update the
  existing local repository by switching to the
  :substitution-code:`|v1.0:migration version|` tag using Git.

Build
-----

* The kas configuration files provided to build and customize EWAOL distribution
  images have been updated, and it is necessary to supply them to the kas build
  tool in a particular order. Therefore, to build the later version of EWAOL,
  refer to the :ref:`Build Documentation<user_guide_reproduce_build>`.

* If working from an existing local ``meta-ewaol`` repository that was switched
  to the :substitution-code:`|v1.0:migration version|` release but has artifacts
  remaining from previous builds, ensure that there are no locally staged
  changes to the dependent layers so that the kas build tool can successfully
  update them.

Deploy
------

* :substitution-code:`|v1.0:migration version|` introduces new types of EWAOL
  distribution images, and the resulting filenames and paths are therefore
  different than previous releases.  Check the
  :ref:`Build<user_guide_reproduce_build>` and
  :ref:`Deploy<user_guide_reproduce_deploy>` sections of the release
  documentation for the new filenames produced during the build, and which
  should be deployed to the target platform.

EWAOL Extend Migration
======================

Porting
-------

* If migrating to EWAOL :substitution-code:`|v1.0:migration version|` as part of
  porting to a custom or unsupported target platform, it is necessary to change
  the existing custom kas configuration file for the target platform to use the
  correct kas configuration files, and supply them with the correct ordering in
  the ``includes`` YAML section. In addition, the ``meta-ewaol`` repository
  definition must be set to use the
  :substitution-code:`|v1.0:migration version|` release tag in ``refspec:``.
  See :ref:`Porting<user_guide_extend_porting>` for details of the necessary
  configuration.
