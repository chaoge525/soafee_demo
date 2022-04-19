..
 # Copyright (c) 2022, Arm Limited.
 #
 # SPDX-License-Identifier: MIT

############
Contributing
############

EWAOL welcomes contributions via the ``meta-ewaol`` public Gitlab repository:
|meta-ewaol repository|.

Contributions should follow the project's contribution guidelines, below.

***********************
Contribution Guidelines
***********************

The following is a set of guidelines that must be adhered to for contributions
to be reviewed and accepted by the EWAOL project:

* **The contribution should be aligned with the goals and scope of the
  project.**

  EWAOL forms the reference software implementation of the SOAFEE project
  (`<http://soafee.io>`_). Contributions should therefore be generally
  applicable to other downstream consumers of ``meta-ewaol``.

* **Contributions should be high-quality, and should pass all tests within the
  repository's Quality Assurance (QA) check suite.**

  The QA checks validate that the contribution adheres to a set of minimal
  requirements, listed here as a link to the detailed requirement:

    * `Commit Message`_
    * `License and Copyright Header`_
    * `Python Code Quality`_
    * `Shell Script Code Quality`_
    * `Spelling`_
    * `Yocto Layer Compatibility`_

  See `Quality Assurance Checks`_ for details on how to run the QA checks. Note
  that all contributions will undergo a code-review process.

* **The contribution must be appropriately licensed.**

  It is expected that all contributions are licensed under the project's
  standard license (see :ref:`license_link:License` for details), except for
  files that represent modifications to externally licensed works (such as, for
  example, patch files), which may be contributed under alternative licenses in
  order to be compliant with the licensing requirements of the associated
  external works.

* **Contributions must include appropriate documentation.**

  Contributions which change the documentation should be validated by running
  the `Documentation Build Validation`_ step.

* **The contribution should not introduce software regressions.**

  Contributions which introduce image build failures or integration test
  failures will not be accepted.

* **Contributions that introduce additional run-time functionality to EWAOL
  distribution images should be accompanied by run-time integration tests to
  validate the functionality.**

  Any additional run-time integration tests or test suites must be documented,
  and follow a similar design to the validation tests described in
  :ref:`Validation <manual/validation:Validation>`.

* **Security aspects of contributions must be considered as part of EWAOL's
  Secure Development Lifecycle (SDL) process.**

  EWAOL's SDL process is currently handled on a per-contribution basis, and it
  is expected that any security aspects raised by the project's maintainer(s)
  will be engaged with before the contribution can be accepted.

  Example security aspects that must be considered as part of a contribution
  include:

    * The contribution's effect on the management and storage of data onto
      temporary or persistent filesystems, and whether appropriate access
      controls to stored data (e.g. filesystem permissions) have been put in
      place.

    * The contribution's effect on data communications (both transmitted or
      received) taking place on the EWAOL distribution, such as changes or
      additions involving client and server processes, and whether appropriate
      security mechanisms (e.g. secure protocols, data encryption) have been put
      in place.

********************
Contribution Process
********************

Adhering to the guidelines listed above, contributions to the EWAOL project
should be made using the process listed in this section.

Gitlab Account Setup
====================

In order to contribute to the repository, it is necessary to have an account on
|meta-ewaol repository host|. Please see `TBC`_ for details of how to create an
account. If contributing within a professional capacity, please include the
affiliation under the ``Organization`` heading on account settings.

The account must be able have sufficient personal project capacity to fork the
``meta-ewaol`` repository. Please see `TBC`_ for details of how to
increase personal project capacity.

.. _TBC: https://

Submission
==========

.. note::
  The mechanics of the EWAOL submission process has not yet been established.
  The process described here is therefore subject to change.

With an appropriate Gitlab account, a contribution can be submitted to
|meta-ewaol repository| via the following process:

1. If the contribution is a bug-fix, please include the ``meta-ewaol`` Gitlab
   Issue ID in which the bug was reported within the Git commit message(s) of
   the contribution.

2. Fork the ``meta-ewaol`` Gitlab repository.

3. Push changes to a branch on the forked repository. This contribution branch
    should be based on the latest development branch of ``meta-ewaol``, which
    is: |meta-ewaol contributions branch|.

4. Submit a Merge Request to ``meta-ewaol`` using the contribution branch on the
   forked repository. Please include all information required by the project's
   Merge Request template.

.. _contributing_documentation_build_validation:

******************************
Documentation Build Validation
******************************

EWAOL provides a Python script to locally build and render the documentation,
available at ``tools/build/doc-build.py``. This script will install all
necessary Python packages into a temporary Python Virtual Environment, and
generate an HTML version of the documentation under ``public/``. The script
requires Python 3.8 or greater, and can be executed via:

.. code-block:: console

    ./tools/build/doc-build.py

The documentation build should be used to validate each commit for contributions
that update the project's documentation, to ensure that the contribution
introduces no documentation build failures or warnings.

The rendered documentation itself should be checked for formatting problems
introduced by the contribution. To do this, simply open and explore the
generated documentation by accessing ``public/index.html`` in a web browser.

For further information about the parameters, call the help function of the
script:

.. code-block:: console

    ./tools/build/doc-build.py --help

************************
Quality Assurance Checks
************************

The project provides tooling for running Quality Assurance (QA) checks on the
repository. These checks aim to automatically validate that contributions adhere
to a set of minimal standards, defined by the project and documented for each
check later in this section.

The tooling is provided as a set of Python scripts that can be found within the
``tools/qa-checks/`` directory of the repository. In order to run the tool, the
system must have installed Python 3 (version 3.8 or greater), the PyYAML Python
package available via pip (5.4.1 is the project's currently supported version),
and Git version 2.25 or greater.

.. note::
   Git version 2.25 may not be available via the default PPAs included with
   Ubuntu 18.04. On this distribution, it can be made available via the
   Git stable releases PPA: ``add-apt-repository ppa:git-core/ppa``

The QA-checks should be run for each commit of the contribution, by executing
``run-checks.py`` via the following command:

.. code-block:: console

    ./tools/qa-checks/run-checks.py --check=all

The script should pass with no errors or warnings.

The validations performed by each QA check are described as follows.

Commit Message
==============

Each commit message of the contribution should pass the following requirements:

  * Title (first line) is not blank
  * Number of characters in the title is fewer than 80
  * The second line is blank to separate message title and body
  * Number of characters in each line of the message body is fewer than 80
  * A sign-off is included in the message, with the following format:
    "Signed-off-by: Name <valid@email.dom>". Note that the given email must also
    be formed correctly.

License and Copyright Header
=============================

Contributed files must contain a valid licence and copyright header, following
one of the two following formats, based on the source of the contribution:

  1. Original works contributed to the project:

  .. code-block:: console

      Copyright (c) YYYY(-YYYY), <Contributor>
      SPDX-License-Identifier: <License name>

  2. Modified externally-licensed works contributed to the project:

  .. code-block:: console

      Based on: <original file>
      In open-source project: <source project/repository>

      Original file: Copyright (c) YYYY(-YYYY) <Contributor>
      Modifications: Copyright (c) YYYY(-YYYY) <Contributor>

      SPDX-License-Identifier: <License name>

  .. note::
    Please follow the contribution guideline relating to licensing in order to
    select the appropriate SPDX License Identifier for the contributed files.

For each file with such a header, the final copyright year of the modifications
must match or be later than the latest year that the file was modified in the
git commit tree.

As some files within the project are inappropriate to license with a plain-text
header (for example, ``.png`` images), some file types are excluded as part of
the QA check configuration. Running the QA check will highlight any files which
are expected to include a valid header, but do not.

Python Code Quality
===================

All Python code contributed to the project must pass validation by the Python
style guide checker ``pycodestyle``, which enforces style conventions based on
the |PEP 8|_ style guide for Python code. The precise Python style conventions
that ``pycodestyle`` validates can be found in the |pycodestyle Documentation|_.

Shell Script Code Quality
=========================

All shell scripts and BATS files contributed to the project must produce no
warnings when passed to the |Shellcheck|_ static analysis tool, as made
available by the ``shellcheck-py`` Python package.

Documentation for each specific check is documented within the
|Shellcheck wiki pages|_.

Spelling
========

The project expects documentation to have correct English (en-US) spelling.
Words within documentation text files have their spelling validated via the
``pyspellchecker`` Python package.

As many project files are technical in nature with non-standard English words, a
file containing a list of additional valid words exists at
``meta-ewaol-config/qa-checks/ewaol-dictionary`` which may be modified if the
QA check erroneously highlights valid technical terminology.

Yocto Layer Compatibility
=========================

Contributions must not break layer compatibility with the Yocto Project, as
validated via the Yocto Project's ``yocto-check-layer`` script, documented as
part of the Yocto Project Documentation at |Yocto Check Layer Script|_.

This validation script will be performed as part of the QA checks.

.. note::
  More detail on the validation steps performed by each check are included at
  the top of each check Python module as in-source documentation. In addition,
  any failed validation will output the specific reason for the failure,
  enabling it to be fixed prior to submitting the contribution.
