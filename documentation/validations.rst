Image Validation
=================

The ``meta-ewaol-tests`` Yocto layer contains recipes and configuration for
including run-time integration tests into a target image, to be run manually
after booting the image, or within a Continuous Integration process.

The EWAOL integration tests provide a mechanism to validate that an image has
functionality that is compliant with the EWAOL project, where the
``meta-ewaol-tests`` Yocto layer is independently available for inclusion in any
desired Yocto image build process.

Currently, run-time integration tests are provided for validating the
functionality of:

* OCI Container Engine (Docker, Podman)

These integration tests are described later in this document.

Building the Tests
------------------

As described in :ref:`Image Builds`, the tests can be included by
appending ``ewaol-test`` to the build's ``DISTRO_FEATURES`` variable and
including the ``meta-ewaol-tests`` layer in the bitbake build, or simply by
passing ``tests.yml`` as a build modifier for a kas build.

The tests are built as a Yocto Package Test (ptest_), and implemented and
executed using the Bash Automated Test Suite (BATS_).

.. _ptest: https://wiki.yoctoproject.org/wiki/Ptest
.. _BATS: https://github.com/bats-core/bats-core

fvp-base: build image including tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To build tests for fvp-base machine from this example
:ref:`Minimal Image Build via kas`, you need to:

* go to `Arm Architecture Models`_ website, and download the "Armv-A Base RevC AEM FVP" package
* set absolute path to the downloaded package
  (e.g. **FVP_Base_RevC-2xAEMvA_11.14_21.tgz**) in ``FVP_BASE_A_AEM_TARBALL_URI``
* accept EULA in ``FVP_BASE_A_ARM_EULA_ACCEPT``

.. _Arm Architecture Models: https://developer.arm.com/tools-and-software/simulation-models/fixed-virtual-platforms/arm-ecosystem-models

  * using kas directly:

    .. code-block:: console

        FVP_BASE_A_AEM_TARBALL_URI="file:///absolute/path/to/FVP_Base_RevC-2xAEMvA_11.14_21.tgz" \
        FVP_BASE_A_ARM_EULA_ACCEPT="True" \
        kas build meta-ewaol-config/kas/fvp-base.yml:meta-ewaol-config/kas/tests.yml

  * using tools/build/kas-ci-build.py:

    .. code-block:: console

        tools/build/kas-ci-build.py fvp-base.yml:tests.yml --engine-arguments \
            '--volume /absolute/path/to/fvp_volume/:/work/fvp_volume \
             --env FVP_BASE_A_AEM_TARBALL_URI="file:///work/fvp_volume/FVP_Base_RevC-2xAEMvA_11.14_21.tgz" \
             --env FVP_BASE_A_ARM_EULA_ACCEPT="True"'

    .. note::
       The ``fvp_volume`` is a directory that contains "Armv-A Base RevC AEM FVP" package.

Running the Tests
-----------------

Once the tests are built and the image booted, they can be run on the target
either using the ptest framework via:

.. code-block:: console

   ptest-runner [test-suite-id]

Or as a standalone BATS script, via a runner script included in the test suite
directory:

.. code-block:: console

   /usr/share/[test-suite-id]/run-[test-suite-id]

Upon completion of the test-suite, a result indicator will be output by the
script, as one of two options: ``PASS:[test-suite-id]`` or
``FAIL:[test-suite-id]``.

A test suite consists of one or more 'top-level' BATS tests, which may be
composed of multiple assertions, where each assertion is considered a named
sub-test. If a sub-test fails, its individual result will be included in the
output with a similar format. In addition, if a test failed then debugging
information will be provided in the output with a ``DEBUG`` prefix. The format
of these results are described in `Test Logging`_ below.

Test Logging
------------

Test suite execution will be logged to a ``[test-suite-id].log`` file within
the log directory of the test suite, which by default is ``logs/`` within the
test suite directory.

This log file will record the results of each top-level integration test, as
well as a result for each individual sub-test up until a failing sub-test is
encountered.

Each top-level result is formatted as:

    ``RESULT:[top_level_test_name]``

Each sub-test result is formatted as:

    ``RESULT:[top_level_test_name]:[sub_test_name]``

Where ``RESULT`` is either ``PASS`` or ``FAIL``.

On a test failure, a debugging message with prefix ``DEBUG`` will be written to
the log. The format of a debugging message is:

    ``DEBUG:[top_level_test_name]:[return_code]:[stdout]:[stderr]```

Additional informational messages may appear in the log file with an ``INFO``
prefix, e.g. to log that an environment clean-up action occurred.

The test suites are detailed below.

Test Suites
-----------

OCI Container Engine Tests
^^^^^^^^^^^^^^^^^^^^^^^^^^

The OCI (Open Container Initiative) Container Engine test suite is identified
as:

    ``oci-runtime-integration-tests``

for execution via ``ptest-runner`` or as a standalone BATS suite, as described
in `Running the Tests`_.

The test suite is built and installed in the image according to the following
bitbake recipe within ``meta-ewaol-tests/recipes-tests/runtime-integration-tests
/oci-runtime-integration-tests.bb``.

The tests execution is identical on both Docker and Podman images, as it makes
use of Podman provided aliases for Docker commands.

Currently the test suite contains two top-level integration tests, which run
consecutively in the following order.

| 1. ``Run OCI Container`` is composed of four sub-tests:
|    1.1. Run a containerised detached workload via the ``docker run`` command
|        - Pull an image from the network
|        - Create and start a container
|    1.2. Check the container is running via the ``docker inspect`` command
|    1.3. Remove the running container via the ``docker remove`` command
|        - Stop the container
|        - Remove the container from the container list
|    1.4. Check the container is not found via the ``docker inspect`` command
| 2. ``OCI Container Network Connectivity`` is composed of a single sub-test:
|    2.1 Run a containerised, immediate (non-detached) network-based workload
         via the ``docker run`` command
|        - Create and start a container, re-using the existing image
|        - Update package lists within container from external network

The tests can be customised via environment variables passed to the execution:

|  ``OCI_TEST_IMAGE``: defines the container image
|    Default: ``docker.io/library/alpine``
|  ``OCI_TEST_LOG_DIR``: defines the location of the log file
|    Default: ``/usr/share/oci-runtime-integration-tests/logs``
|    Directory will be created if it does not exist
|    See `Test Logging`_
|  ``OCI_TEST_CLEAN_ENV``: enable test environment cleanup
|    Default: ``1`` (enabled)
|    See `Environment Clean-Up`_


fvp-base: running tests
"""""""""""""""""""""""

To start fvp emulation and run tests you need to:

* build the tests using above instructions `fvp-base: build image including tests`_
* start the fvp-base emulator with podman or docker flavour:

  * using kas directly:

    .. code-block:: console

      kas shell --keep-config-unchanged \
          meta-ewaol-config/kas/fvp-base.yml:meta-ewaol-config/kas/tests.yml \
              --command "../layers/meta-arm/scripts/runfvp \
                   tmp/deploy/images/fvp-base/ewaol-image-[docker|podman]-fvp-base.fvpconf \
                   --console \
                   -- \
                       --parameter 'bp.smsc_91c111.enabled=1' \
                       --parameter 'bp.hostbridge.userNetworking=true'"

  * using tools/build/kas-ci-build.py:

    .. code-block:: console

        tools/build/kas-ci-build.py fvp-base.yml:tests.yml \
            --engine-arguments ' -it -p 5000:5000' \
            --kas-arguments 'shell --keep-config-unchanged \
                --command "/work/layers/meta-arm/scripts/runfvp \
                    tmp/deploy/images/fvp-base/ewaol-image-[docker|podman]-fvp-base.fvpconf \
                       -- \
                           --parameter \"bp.smsc_91c111.enabled=1\" \
                           --parameter \"bp.hostbridge.userNetworking=true\""'

    * grab FVP emulation console in other terminal window with
      ``telnet localhost 5000``

* execute tests with:

.. code-block:: console

    $ ptest-runner oci-runtime-integration-tests
    START: ptest-runner
    [...]
    PASS:oci-runtime-integration-tests
    [...]
    STOP: ptest-runner

* to finish the fvp emulation you need to close telnet session
  and stop the runfvp script:

  1. to close telnet session:

    * escape to telnet console with ``ctrl+]``
    * run ``quit`` to close the session.

  2. to stop the runfvp:

    * type ``ctrl+c`` and wait for kas process to finish

Environment Clean-Up
""""""""""""""""""""

A clean environment is expected when running the OCI container engine tests.
For example, if the target OCI image already exists within the container engine
environment, then the functionality to pull the image over the network will not
be validated. Or, if there are running containers from previous (failed) tests
then they may interfere with subsequent test executions.

Therefore, if ``OCI_TEST_CLEAN_ENV`` is set to ``1`` (as is default), running
the test suite will perform an environment clean before and after the suite
execution.

The environment clean operation involves:

    * Determination and removal of all running containers of the image given by
      ``OCI_TEST_IMAGE``
    * Removal of the image given by ``OCI_TEST_IMAGE``, if it exists

If enabled then the environment clean operations will always be run, regardless
of test-suite success or failure.
