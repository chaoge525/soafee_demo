Image Validation
================

The ``meta-ewaol-tests`` Yocto layer contains recipes and configuration for
including run-time integration tests into a target image, to be run manually
after booting the image, or within a Continuous Integration process.

The EWAOL integration tests provide a mechanism to validate that an image has
functionality that is compliant with the EWAOL project, where the
``meta-ewaol-tests`` Yocto layer is independently available for inclusion in
any desired Yocto image build process.

Currently, run-time integration tests are provided for validating the
functionality of:

* Container Engine (Docker, Podman)
* K3S Container Orchestration

These integration tests are described later in this document.

Building the Tests
------------------

As described in :ref:`builds:Image Builds`, the tests can be included by
appending ``ewaol-test`` to the build's ``DISTRO_FEATURES`` variable and
including the ``meta-ewaol-tests`` layer in the bitbake build, or simply by
passing ``tests.yml`` as a build modifier for a kas build.

The tests are built as a Yocto Package Test (ptest_), and implemented and
executed using the Bash Automated Test Suite (BATS_).

.. _ptest: https://wiki.yoctoproject.org/wiki/Ptest
.. _BATS: https://github.com/bats-core/bats-core

.. _validations_fvp-base_build_image_including_tests:

fvp-base: build image including tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To build tests for fvp-base machine from this example
:ref:`quickstart_fvp-base`, you need to:

* download the `FVP_Base_RevC-2xAEMvA_11.14_21.tgz`_ "Armv-A Base AEM FVP FOC
  (Linux)" package from Arm's website. You need to have an account and be logged
  in to be able to download it
* set absolute path to the ``FVP_Base_RevC-2xAEMvA_11.14_21.tgz`` downloaded
  package in ``FVP_BASE_A_AEM_TARBALL_URI``
* accept EULA in ``FVP_BASE_A_ARM_EULA_ACCEPT``
* Add ``:meta-ewaol-config/kas/tests.yml`` to the kas build command:

.. _FVP_Base_RevC-2xAEMvA_11.14_21.tgz: https://silver.arm.com/download/download.tm?pv=4849271&p=3042387

  * using ``kas`` directly:

    .. code-block:: console

        FVP_BASE_A_AEM_TARBALL_URI="file:///absolute/path/to/FVP_Base_RevC-2xAEMvA_11.14_21.tgz" \
        FVP_BASE_A_ARM_EULA_ACCEPT="True" \
        kas build meta-ewaol-config/kas/fvp-base.yml:meta-ewaol-config/kas/tests.yml

  * using ``tools/build/kas-ci-build.py``:

    .. code-block:: console

        ./tools/build/kas-ci-build.py fvp-base.yml:tests.yml --engine-arguments \
            '--volume /absolute/path/to/fvp_volume/:/work/fvp_volume \
             --env FVP_BASE_A_AEM_TARBALL_URI="file:///work/fvp_volume/FVP_Base_RevC-2xAEMvA_11.14_21.tgz" \
             --env FVP_BASE_A_ARM_EULA_ACCEPT="True"'

    .. note::
       The ``fvp_volume`` is a directory that contains "Armv-A Base RevC AEM FVP
       " package.

* To execute tests please refer to `fvp-base: running tests`_.

.. _validations_n1sdp_build_image_including_tests:

N1SDP: build image including tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To build tests for N1SDP using the same process as described in
:ref:`quickstart_build_for_n1sdp`, you only need to add
``:meta-ewaol-config/kas/tests.yml`` to the kas build command:

.. code-block:: console

    kas build meta-ewaol-config/kas/n1sdp.yml:meta-ewaol-config/kas/tests.yml

To deploy the generated images on the board, please refer to the
:ref:`quickstart_deploy_on_n1sdp` section.

To execute tests please refer to `n1sdp: running tests`_.

Running the Tests
-----------------

Once the tests are built and the image booted, they can be run on the target
using the ptest framework via:

.. code-block:: console

   ptest-runner [test-suite-id]

If the test suite identifier is omitted, all integration tests will be run.

Alternatively, the tests may be run as a standalone BATS script, via a runner
script included in the test suite directory:

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
of these results are described in `Test Logging`_.

.. _validations_fvp-base_running_tests:

fvp-base: running tests
^^^^^^^^^^^^^^^^^^^^^^^

To start fvp emulation and run tests you need to:

* build the tests using above instructions
  `fvp-base: build image including tests`_
* start the fvp-base emulator with podman or docker flavour:

  * using ``kas`` directly:

    .. code-block:: console

      kas shell --keep-config-unchanged \
          meta-ewaol-config/kas/fvp-base.yml:meta-ewaol-config/kas/tests.yml \
              --command "../layers/meta-arm/scripts/runfvp \
                   tmp/deploy/images/fvp-base/ewaol-image-[docker|podman]-fvp-base.fvpconf \
                   --console \
                   -- \
                       --parameter 'bp.smsc_91c111.enabled=1' \
                       --parameter 'bp.hostbridge.userNetworking=true'"

  * using ``tools/build/kas-ci-build.py``:

    .. code-block:: console

        ./tools/build/kas-ci-build.py fvp-base.yml:tests.yml \
            --engine-arguments ' -it -p 5000:5000' \
            --kas-arguments 'shell --keep-config-unchanged \
                --command "/work/layers/meta-arm/scripts/runfvp \
                    tmp/deploy/images/fvp-base/ewaol-image-[docker|podman]-fvp-base.fvpconf \
                       -- \
                           --parameter \"bp.smsc_91c111.enabled=1\" \
                           --parameter \"bp.hostbridge.userNetworking=true\""'

    * grab FVP emulation console in other terminal window with
      ``telnet localhost 5000``

* login as ``root`` without password, then execute all tests with:

.. code-block:: console

    $ ptest-runner
    START: ptest-runner
    [...]
    PASS:container-engine-integration-tests
    [...]
    PASS:k3s-integration-tests
    [...]
    STOP: ptest-runner

  * to run a specific integration test suite, provide its identifier as an
  argument to ``ptest-runner``.

* to finish the fvp emulation you need to close telnet session
  and stop the runfvp script:

  1. to close telnet session:

    * escape to telnet console with ``ctrl+]``
    * run ``quit`` to close the session.

  2. to stop the runfvp:

    * type ``ctrl+c`` and wait for kas process to finish

.. _validations_n1sdp_running_tests:

n1sdp: running tests
^^^^^^^^^^^^^^^^^^^^

To run tests on N1SDP you need to:

* build the tests using above instructions `n1sdp: build image including tests`_
* boot a n1sdp board using the images generated by kas using the information
  from the :ref:`quickstart_deploy_on_n1sdp` section.

Log in as ``root`` without password. All tests can then be launched from the
main console:

.. code-block:: console

    $ ptest-runner
    START: ptest-runner
    [...]
    PASS:container-engine-integration-tests
    [...]
    PASS:k3s-integration-tests
    [...]
    STOP: ptest-runner

To run a specific integration test suite, provide its identifier as an argument
to ``ptest-runner``.

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

Additional informational messages may appear in the log file with ``INFO`` or
``DEBUG`` prefixes, e.g. to log that an environment clean-up action occurred.

The test suites are detailed below.

Test Suites
-----------

Container Engine Tests
^^^^^^^^^^^^^^^^^^^^^^

The container engine test suite is identified as:

    ``container-engine-integration-tests``

for execution via ``ptest-runner`` or as a standalone BATS suite, as described
in `Running the Tests`_.

The test suite is built and installed in the image according to the following
bitbake recipe within
``meta-ewaol-tests/recipes-tests/runtime-integration-tests/container-engine-integration-tests.bb``.

The tests execution is identical on both Docker and Podman images, as it makes
use of Podman provided aliases for Docker commands.

Currently the test suite contains two top-level integration tests, which run
consecutively in the following order.

| 1. ``run container`` is composed of four sub-tests:
|    1.1. Run a containerised detached workload via the ``docker run`` command
|        - Pull an image from the network
|        - Create and start a container
|    1.2. Check the container is running via the ``docker inspect`` command
|    1.3. Remove the running container via the ``docker remove`` command
|        - Stop the container
|        - Remove the container from the container list
|    1.4. Check the container is not found via the ``docker inspect`` command
| 2. ``container network connectivity`` is composed of a single sub-test:
|    2.1 Run a containerised, immediate (non-detached) network-based workload
         via the ``docker run`` command
|        - Create and start a container, re-using the existing image
|        - Update package lists within container from external network

The tests can be customised via environment variables passed to the execution,
each prefixed by ``CE_`` to identify the variable as associated to the
container engine tests:

|  ``CE_TEST_IMAGE``: defines the container image
|    Default: ``docker.io/library/alpine``
|  ``CE_TEST_LOG_DIR``: defines the location of the log file
|    Default: ``/usr/share/container-engine-integration-tests/logs``
|    Directory will be created if it does not exist
|    See `Test Logging`_
|  ``CE_TEST_CLEAN_ENV``: enable test environment cleanup
|    Default: ``1`` (enabled)
|    See `Container Engine Environment Clean-Up`_

Container Engine Environment Clean-Up
"""""""""""""""""""""""""""""""""""""

A clean environment is expected when running the container engine tests. For
example, if the target image already exists within the container engine
environment, then the functionality to pull the image over the network will not
be validated. Or, if there are running containers from previous (failed) tests
then they may interfere with subsequent test executions.

Therefore, if ``CE_TEST_CLEAN_ENV`` is set to ``1`` (as is default), running
the test suite will perform an environment clean before and after the suite
execution.

The environment clean operation involves:

    * Determination and removal of all running containers of the image given by
      ``CE_TEST_IMAGE``
    * Removal of the image given by ``CE_TEST_IMAGE``, if it exists

If enabled then the environment clean operations will always be run, regardless
of test-suite success or failure.

K3S Orchestration Tests
^^^^^^^^^^^^^^^^^^^^^^^

The K3S test suite is identified as:

    ``k3s-integration-tests``

for execution via ``ptest-runner`` or as a standalone BATS suite, as described
in `Running the Tests`_.

The test suite is built and installed in the image according to the following
bitbake recipe within
``meta-ewaol-tests/recipes-tests/runtime-integration-tests/k3s-integration-tests.bb``.

The tests execution is identical on both Docker and Podman images.

Currently the test suite contains a single top-level integration test which
validates the deployment and high-availability of a test workload based on the
`Nginx`_ webserver. This integration test is described below.

.. _Nginx: https://www.nginx.com/

| 1. ``K3S orchestration of containerised web service`` is composed of many
     sub-tests, grouped here by test area:
|    **Workload Deployment:**
|    1.1. Ensure server is running via systemd service
|        - ``kubectl`` check that built-in kube-system Pods are available
|    1.2. Deploy test Nginx workload from YAML file via ``kubectl apply``
|    1.3. Ensure Pod replicas are initialised via ``kubectl wait``
|    1.4. Create Service to expose Deployment via ``kubectl expose``
|    1.5. Get IP of resulting Service via ``kubectl get``
|    1.6. Ensure web service is accessible via ``wget``
|    **Pod Failure Tolerance:**
|    1.7. Get random Pod name from Deployment name via ``kubectl get``
|    1.8. Delete random Pod via ``kubectl delete``
|    1.9. Ensure web service is still accessible via ``wget``
|    **Deployment Upgrade:**
|    1.10. Get image version of random Pod via ``kubectl get``
|    1.11. Upgrade image version of Deployment via ``kubectl set``
|    1.12. Ensure web service is still accessible via ``wget``
|    1.13. Get upgraded image version of random Pod via ``kubectl get``
|    **Server Failure Tolerance:**
|    1.14. Stop K3S server systemd service
|    1.15. Ensure web service remains accessible via ``wget``
|    1.16. Restart the systemd service
|    1.17. Ensure server is running via systemd service
|    1.18. Check K3S server is again responding to ``kubectl get``
|    **Server Configuration Change:**
|    1.19. Add systemd override to change server's command-line arguments
|         - Configuration change to run the server without built-in worker
|         - Reload and restart the systemd service
|    1.20. Check systemd service is running after configuration change
|    1.21. Delete test Nginx workload via ``kubectl delete``
|    1.22. Deploy test Nginx workload from YAML file via ``kubectl apply``
|    1.23. Ensure Pod replicas are not initialised (as no worker available) via
           ``kubectl get``

The tests can be customised via environment variables passed to the execution,
each prefixed by ``K3S_`` to identify the variable as associated to the
K3S orchestration tests:

|  ``K3S_TEST_LOG_DIR``: defines the location of the log file
|    Default: ``/usr/share/k3s-integration-tests/logs``
|    Directory will be created if it does not exist
|    See `Test Logging`_
|  ``K3S_TEST_CLEAN_ENV``: enable test environment cleanup
|    Default: ``1`` (enabled)
|    See `K3S Environment Clean-Up`_

K3S Environment Clean-Up
""""""""""""""""""""""""

A clean environment is expected when running the K3S integration tests, to
ensure that the system is ready to be validated. For example, the test suite
expects that the Pods created from any previous execution of the integration
tests have been deleted, in order to test that a new Deployment successfully
initialises new Pods for orchestration.

Therefore, if ``K3S_TEST_CLEAN_ENV`` is set to ``1`` (as is default), running
the test suite will perform an environment clean before and after the suite
execution.

The environment clean operation involves:

    * Starting the K3S systemd service if it is not currently active
    * Deleting any previous K3S test Service
    * Deleting any previous K3S test Deployment, ensuring corresponding Pods
      are also deleted
    * Deleting any previous K3S systemd service test override

If enabled then the environment clean operations will always be run, regardless
of test-suite success or failure.
