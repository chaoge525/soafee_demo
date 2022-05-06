..
 # Copyright (c) 2021-2022, Arm Limited.
 #
 # SPDX-License-Identifier: MIT

##########
Validation
##########

*************************************
Build-Time Kernel Configuration Check
*************************************

After the kernel configuration has been produced during the build, it is checked
to validate the presence of necessary kernel configuration to comply with
specific EWAOL functionalities.

A list of required kernel configs is used as a reference, and compared against
the list of available configs in the kernel build. All reference configs need to
be present either as module (``=m``) or built-in (``=y``). A Bitbake warning
message is produced if the kernel is not configured as expected.

The following kernel configuration checks are performed:

* **Container engine support**:

  Check performed via:
  ``meta-ewaol-distro/classes/containers_kernelcfg_check.bbclass``.
  By default |Yocto Docker config|_ is used as the reference.

* **K3s orchestration support**:

  Check performed via:
  ``meta-ewaol-distro/classes/k3s_kernelcfg_check.bbclass``.
  By default |Yocto K3s config|_ is used as the reference.

* **Xen virtualization support** (available for EWAOL virtualization
  distribution images):

  Check performed via:
  ``meta-ewaol-distro/classes/xen_kernelcfg_check.bbclass``.
  By default |Yocto Xen config|_ is used as the reference.

.. _validation_run-time_integration_tests:

**************************
Run-Time Integration Tests
**************************

The ``meta-ewaol-tests`` Yocto layer contains recipes and configuration for
including run-time integration tests into an EWAOL distribution, to be run
manually after booting the image.

The EWAOL run-time integration tests are a mechanism for validating EWAOL core
functionalities. The integration test suites included on an EWAOL distribution
image depend on its target architecture, as follows:

* Baremetal architecture:
    * `Container Engine Tests`_
    * `K3s Orchestration Tests`_ (local deployment of K3s pods)
    * `User Accounts Tests`_
* Virtualization architecture:
    * Control VM:

      * `Container Engine Tests`_
      * `K3s Orchestration Tests`_ (remote deployment of K3s pods on a Guest
        VM, from the Control VM)
      * `User Accounts Tests`_
      * `Xen Virtualization Tests`_
    * Guest VM:

      * `Container Engine Tests`_
      * `User Accounts Tests`_

The tests are built as a |Yocto Package Test|_ (ptest), and implemented using
the |Bash Automated Test System|_ (BATS).

Run-time integration tests are not included on an EWAOL distribution image by
default, and must instead be included explicitly. See
:ref:`manual_build_system_run_time_integration_tests` within the Build System
documentation for details on how to include the tests.

The test suites are executed using the ``test`` user account, which has ``sudo``
privileges. More information about user accounts can be found at
:ref:`User Accounts<manual/user_accounts:User Accounts>`.

Running the Tests
=================

If the tests have been included on the EWAOL distribution image, they may be run
via the ptest framework, using the following command after booting the image and
logging in:

.. code-block:: console

   ptest-runner [test-suite-id]

If the test suite identifier (``[test-suite-id]``) is omitted, all integration
tests will be run.  For example, running ``ptest-runner`` on the Control VM of
an EWAOL virtualization distribution image produces output such as the
following:

.. code-block:: console

   $ ptest-runner
   START: ptest-runner
   [...]
   PASS:container-engine-integration-tests
   [...]
   PASS:k3s-integration-tests
   [...]
   PASS:user-accounts-integration-tests
   [...]
   PASS:virtualization-integration-tests
   [...]
   STOP: ptest-runner

.. note::
  As different EWAOL architectures support different test suites.
  ``ptest-runner -l`` is a useful command to list the available test suites on
  the image.

Alternatively, a single standalone test suite may be run via a runner script
included in the test suite directory:

.. code-block:: console

   /usr/share/[test-suite-id]/run-[test-suite-id]

Upon completion of the test-suite, a result indicator will be output by the
script, as one of two options: ``PASS:[test-suite-id]`` or
``FAIL:[test-suite-id]``, as well as an appropriate exit status.

A test suite consists of one or more 'top-level' BATS tests, which may be
composed of multiple assertions, where each assertion is considered a named
sub-test. If a sub-test fails, its individual result will be included in the
output with a similar format. In addition, if a test failed then debugging
information will be provided in the output of type ``DEBUG``. The format of
these results are described in `Test Logging`_.

Test Logging
============

Test suite execution outputs results and debugging information into a log file.
As the test suites are executed using the ``test`` user account, this log file
will be owned by the ``test`` user and located in the ``test`` user's home
directory by default, at:

    ``/home/test/runtime-integration-tests-logs/[test-suite-id].log``

Therefore, reading this file as another user will require ``sudo`` access. The
location of the log file for each test suite is customizable, as described in
the detailed documentation for each test suite below. The log file is replaced
on each new execution of a test suite.

The log file will record the results of each top-level integration test, as
well as a result for each individual sub-test up until a failing sub-test is
encountered.

Each top-level result is formatted as:

    ``TIMESTAMP RESULT:[top_level_test_name]``

Each sub-test result is formatted as:

    ``TIMESTAMP RESULT:[top_level_test_name]:[sub_test_name]``

Where ``TIMESTAMP`` is of the format ``%Y-%m-%d %H:%M:%S`` (see
|Python Datetime Format Codes|_), and ``RESULT`` is either ``PASS``, ``FAIL``,
or ``SKIP``.

On a test failure, a debugging message of type ``DEBUG`` will be written to
the log. The format of a debugging message is:

    ``TIMESTAMP DEBUG:[top_level_test_name]:[return_code]:[stdout]:[stderr]``

Additional informational messages may appear in the log file with ``INFO`` or
``DEBUG`` message types, e.g. to log that an environment clean-up action
occurred.

Test Suites
===========

The test suites are detailed below.

Container Engine Tests
----------------------

The container engine test suite is identified as:

    ``container-engine-integration-tests``

for execution via ``ptest-runner`` or as a standalone BATS suite, as described
in `Running the Tests`_.

On an EWAOL virtualization distribution image, the container engine test suite
is available for execution on both the Control VM and the Guest VM. In addition,
as part of running the test suite on the Control VM, an extra test will be
performed which logs into the Guest VM and runs the container engine test suite
on it, thereby reporting any test failures of the Guest VM as part of the
Control VM's test suite execution.

The test suite is built and installed in the image according to the following
bitbake recipe:
``meta-ewaol-tests/recipes-tests/runtime-integration-tests/container-engine-integration-tests.bb``.

Currently the test suite contains three top-level integration tests, which run
consecutively in the following order.

| 1. ``run container`` is composed of four sub-tests:
|    1.1. Run a containerized detached workload via the ``docker run`` command
|        - Pull an image from the network
|        - Create and start a container
|    1.2. Check the container is running via the ``docker inspect`` command
|    1.3. Remove the running container via the ``docker remove`` command
|        - Stop the container
|        - Remove the container from the container list
|    1.4. Check the container is not found via the ``docker inspect`` command
| 2. ``container network connectivity`` is composed of a single sub-test:
|    2.1. Run a containerized, immediate (non-detached) network-based workload
         via the ``docker run`` command
|        - Create and start a container, re-using the existing image
|        - Update package lists within container from external network
| 3. ``run container engine integration tests on the Guest VM from the Control VM``
     is only executed on the Control VM. On the Guest VM this test is skipped.
     The test is composed of two sub-tests:
|    3.1. Check that Xendomains is initialized and the Guest VM is running via
          ``systemctl status`` and ``xendomains status``
|    3.2. Run the container engine integration tests on the Guest VM
|        - Uses an Expect script to log-in and execute the
           ``ptest-runner container-engine-integration-tests`` command
|        - This command will therefore run only the first and second top-level
           integration tests of the container engine integration test suite on
           the Guest VM

The tests can be customized via environment variables passed to the execution,
each prefixed by ``CE_`` to identify the variable as associated to the
container engine tests:

|  ``CE_TEST_IMAGE``: defines the container image
|    Default: ``docker.io/library/alpine``
|  ``CE_TEST_LOG_DIR``: defines the location of the log file
|    Default: ``/home/test/runtime-integration-tests-logs/``
|    Directory will be created if it does not exist
|    See `Test Logging`_
|  ``CE_TEST_CLEAN_ENV``: enable test environment clean-up
|    Default: ``1`` (enabled)
|    See `Container Engine Environment Clean-Up`_
|  ``CE_TEST_GUEST_VM_NAME``: defines the Xen domain name and Hostname of the
    Guest VM
|    Only available when running the tests on an EWAOL virtualization
     distribution image
|    Represents the target Guest VM to test when executing the suite on the
     Control VM
|    Default: ``${EWAOL_GUEST_VM_HOSTNAME}1``
|    With standard configuration, the default Guest VM will therefore be
     ``ewaol-guest-vm1``

Container Engine Environment Clean-Up
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
    * Clearing the password set when the tests accessed the Guest VM, performed
      only when running the test suite on a virtualization distribution image
      with :ref:`Security Hardening<manual/hardening:Security Hardening>`
      enabled.

If enabled then the environment clean operations will always be run, regardless
of test-suite success or failure.

K3s Orchestration Tests
-----------------------

The K3s test suite is identified as:

    ``k3s-integration-tests``

for execution via ``ptest-runner`` or as a standalone BATS suite, as described
in `Running the Tests`_.

The test suite is built and installed in the image according to the following
bitbake recipe within
``meta-ewaol-tests/recipes-tests/runtime-integration-tests/k3s-integration-tests.bb``.

Currently the test suite contains a single top-level integration test which
validates the deployment and high-availability of a test workload based on the
|Nginx|_ webserver. The test suite is dependent on the target EWAOL
architecture, as follows.

For EWAOL baremetal distribution images, the K3s integration tests consider a
single-node cluster, which runs a K3s server together with its built-in worker
agent. The containerized test workload is therefore deployed to this node for
scheduling and execution.

For EWAOL virtualization distribution images, the K3s integration tests consider
a cluster comprised of two nodes: the Control VM running a K3s server, and the
Guest VM running a K3s agent which is connected to the server. The containerized
test workload is configured to only be schedulable on the Guest VM, meaning that
the server on the Control VM orchestrates a test application which is deployed
and executed on the Guest VM. In addition to the same initialization procedure
that is carried out when running the tests on a baremetal distribution image,
initialization for virtualization distribution images includes connecting the
Guest VM's K3s agent to the Control VM's K3s server (if it is not already
connected). To do this, before the tests run, the Systemd service that provides
the K3s agent on the Guest VM is configured with a Systemd service unit override
that provides the IP and authentication token of the Control VM's K3s server,
and this service is then started. The K3s integration test suite therefore
expects that the target Guest VM is available when running on a virtualization
distribution image, and will not create one if it does not exist.

In both cases, the test suite will not be run until the appropriate K3s services
are in the 'active' state, and all 'kube-system' pods are either running, or
have completed their workload.

| 1. ``K3s orchestration of containerized web service`` is composed of many
     sub-tests, grouped here by test area:
|    **Workload Deployment:**
|    1.1. Deploy test Nginx workload from YAML file via ``kubectl apply``
|    1.2. Ensure Pod replicas are initialized via ``kubectl wait``
|    1.3. Create NodePort Service to expose Deployment via
          ``kubectl create service``
|    1.4. Get the IP of the node running the Deployment via ``kubectl get``
|    1.5. Ensure web service is accessible on the node via ``wget``
|    **Pod Failure Tolerance:**
|    1.6. Get random Pod name from Deployment name via ``kubectl get``
|    1.7. Delete random Pod via ``kubectl delete``
|    1.8. Ensure web service is still accessible via ``wget``
|    **Deployment Upgrade:**
|    1.9. Get image version of random Pod via ``kubectl get``
|    1.10. Upgrade image version of Deployment via ``kubectl set``
|    1.11. Ensure web service is still accessible via ``wget``
|    1.12. Get upgraded image version of random Pod via ``kubectl get``
|    **Server Failure Tolerance:**
|    1.13. Stop K3s server Systemd service via ``systemctl stop``
|    1.14. Ensure web service is still accessible via ``wget``
|    1.15. Restart the Systemd service via ``systemctl start``
|    1.16. Check K3S server is again responding to ``kubectl get``

The tests can be customized via environment variables passed to the execution,
each prefixed by ``K3S_`` to identify the variable as associated to the
K3s orchestration tests:

|  ``K3S_TEST_LOG_DIR``: defines the location of the log file
|    Default: ``/home/test/runtime-integration-tests-logs/``
|    Directory will be created if it does not exist
|    See `Test Logging`_
|  ``K3S_TEST_CLEAN_ENV``: enable test environment clean-up
|    Default: ``1`` (enabled)
|    See `K3s Environment Clean-Up`_
|  ``K3S_TEST_GUEST_VM_NAME``: defines the name of the Guest VM to use for the
   tests
|    Only available when running the tests on a virtualization distribution
     image
|    Default: ``${EWAOL_GUEST_VM_HOSTNAME}1``
|    With standard configuration, the default Guest VM will therefore be
     ``ewaol-guest-vm1``

K3s Environment Clean-Up
^^^^^^^^^^^^^^^^^^^^^^^^

A clean environment is expected when running the K3s integration tests, to
ensure that the system is ready to be validated. For example, the test suite
expects that the Pods created from any previous execution of the integration
tests have been deleted, in order to test that a new Deployment successfully
initializes new Pods for orchestration.

Therefore, if ``K3S_TEST_CLEAN_ENV`` is set to ``1`` (as is default), running
the test suite will perform an environment clean before and after the suite
execution.

The environment clean operation involves:

    * Deleting any previous K3s test Service
    * Deleting any previous K3s test Deployment, ensuring corresponding Pods
      are also deleted

For virtualization distribution images, additional clean-up operations are
performed:

    * Deleting the Guest VM node from the K3s cluster
    * Stopping the K3s agent running on the Guest VM, and deleting any test
      Systemd service override on the Guest VM
    * Clearing the password set when the tests accessed the Guest VM, performed
      only when running the test suite on a virtualization distribution image
      with :ref:`Security Hardening<manual/hardening:Security Hardening>`
      enabled.

If enabled then the environment clean operations will always be run, regardless
of test-suite success or failure.

.. _manual_validation_user_accounts_tests:

User Accounts Tests
-------------------

The User Accounts test suite is identified as:

    ``user-accounts-integration-tests``

for execution via ``ptest-runner`` or as a standalone BATS suite, as described
in `Running the Tests`_.

The test suite is built and installed in the image according to the following
bitbake recipe within
``meta-ewaol-tests/recipes-tests/runtime-integration-tests/user-accounts-integration-tests.bb``.

The test suite validates that the user accounts described in
:ref:`User Accounts<manual/user_accounts:User Accounts>` are correctly
configured on the EWAOL distribution image. Therefore, the validation performed
by the test suite is dependent on the target architecture, and on whether or not
it has been configured with
:ref:`EWAOL Security Hardening<manual/hardening:Security Hardening>`, as
follows.

For a baremetal image, the test suite validates that the expected user accounts
are configured and appropriate access permissions are in place. For a
virtualization image, the test suite is available on both the Control VM and the
Guest VM(s), and includes the same validation as the baremetal test suite on the
respective VM's local user accounts. However, as part of running the test suite
on the Control VM, an extra test will be performed which logs into the Guest VM
and runs the user accounts test suite on it, thereby reporting any test failures
of the Guest VM as part of the Control VM's test suite execution.

As the configuration of user accounts is modified for EWAOL distribution images
that are built with EWAOL security hardening, additional security-related
validation is included in the test suite for these images, both on EWAOL
baremetal and virtualization distribution images. These additional tests
validate that the appropriate password requirements and root-user access
restrictions are correctly imposed, and that the mask configuration for
permission control of newly created files and directories is applied correctly.

The test suite therefore contains three top-level integration tests, two of
which are conditionally executed, as follows:

| 1. ``user accounts management tests`` is composed of three sub-tests:
|    1.1. Check home directory permissions are correct for the default
          non-privileged EWAOL user account, via the filesystem ``stat`` utility
|    1.2. Check the default privileged EWAOL user account has ``sudo`` command
          access
|    1.3. Check the default non-privileged EWAOL user account does not have
          ``sudo`` command access
| 2. ``user accounts management additional security tests`` is only included for
     images configured with EWAOL security hardening, and is composed of four
     sub-tests:
|    2.1. Log-in to a local console using the non-privileged EWAOL user account
|        - As part of the log-in procedure, validate the user is prompted to
           set an account password
|    2.2. Check that log-in to a local console using the root account fails
|    2.3. Check that SSH log-in to localhost using the root account fails
|    2.4. Check that the umask value is set correctly
| 3. ``run user accounts integration tests on the Guest VM from the Control VM``
     is only included for EWAOL virtualization distribution images, and is only
     executed on the Control VM. On the Guest VM this test is skipped. The test
     is composed of two sub-tests:
|    3.1. Check that Xendomains is initialized and the Guest VM is running via
          ``systemctl status`` and ``xendomains status``
|    3.2. Run the user accounts integration tests on the Guest VM
|        - Uses an Expect script to log-in and execute the
           ``ptest-runner user-accounts-integration-tests`` command
|        - This command will therefore run only the first and second
           (if EWAOL security hardening is configured) top-level integration
           tests of the user accounts integration test suite on the Guest VM

The tests can be customized via environment variables passed to the execution,
each prefixed by ``UA_`` to identify the variable as associated to the user
accounts tests:

|  ``UA_TEST_LOG_DIR``: defines the location of the log file
|    Default: ``/home/test/runtime-integration-tests-logs/``
|    Directory will be created if it does not exist
|    See `Test Logging`_
|  ``UA_TEST_CLEAN_ENV``: enable test environment clean-up
|    Default: ``1`` (enabled)
|    See `User Accounts Environment Clean-Up`_
|  ``UA_TEST_GUEST_VM_NAME``: defines the Xen domain name and Hostname of the
   Guest VM
|    Only available when running the tests on an EWAOL virtualization
     distribution image
|    Represents the target Guest VM to test when executing the suite on the
     Control VM
|    Default: ``${EWAOL_GUEST_VM_HOSTNAME}1``
|    With standard configuration, the default Guest VM will therefore be
     ``ewaol-guest-vm1``

User Accounts Environment Clean-Up
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As the user accounts integration tests only modify the system for images built
with EWAOL security hardening, clean-up operations are only performed when
running the test suite on these images.

In addition, the clean-up operations will only occur if ``UA_TEST_CLEAN_ENV`` is
set to ``1`` (as is default).

The environment clean-up operations for images built with EWAOL security
hardening are:

    * Reset the password for the ``test`` user account
    * Reset the password for the non-privileged EWAOL user account
    * Clearing the password set when the tests accessed the Guest VM, performed
      only when running the test suite on a virtualization distribution image
      with :ref:`Security Hardening<manual/hardening:Security Hardening>`
      enabled.

After the environment clean-up, the user accounts will return to their original
state where the first log-in will prompt the user for a new account password.

If enabled then the environment clean operations will always be run, regardless
of test-suite success or failure.

Xen Virtualization Tests
------------------------

The Xen Virtualization test suite is identified as:

    ``virtualization-integration-tests``

for execution via ``ptest-runner`` or as a standalone BATS suite, as described
in `Running the Tests`_.

The test suite is built and installed in the image according to the following
bitbake recipe within
``meta-ewaol-tests/recipes-tests/runtime-integration-tests/virtualization-integration-tests.bb``.

The test suite is only available for images that target the virtualization
architecture.

Currently the test suite contains two top-level integration tests, which
validate a correctly running Guest VM, and validate that it can be managed
successfully from the Control VM. These tests are as follows:

| 1. ``validate Guest VM is running`` is composed of two sub-tests:
|    1.1. Check that Xen reports the Guest VM as running via
          ``xendomains status``
|    1.2. Check that the Guest VM is operational and has external network access
|        - Log-in to the Guest VM and access its interactive shell via
           ``xl console``
|        - Ping an external IP with the ``ping`` utility
| 2. ``validate Guest VM management`` is composed of five sub-tests:
|    2.1. Check that Xen reports the Guest VM as running via
          ``xendomains status``
|    2.2. Shutdown the Guest VM via ``systemctl stop``
|    2.3. Check that Xen reports the Guest VM as not running via
          ``xendomains status``
|    2.4. Start the Guest VM via ``systemctl start``
|    2.5. Check that Xen reports the Guest VM as running via
          ``xendomains status``

The tests can be customized via environment variables passed to the execution,
each prefixed by ``VIRT_`` to identify the variable as associated to the
virtualization integration tests:

|  ``VIRT_TEST_LOG_DIR``: defines the location of the log file
|    Default: ``/home/test/runtime-integration-tests-logs/``
|    Directory will be created if it does not exist
|    See `Test Logging`_
|  ``VIRT_TEST_CLEAN_ENV``: enable test environment clean-up
|    Default: ``1`` (enabled)
|    See `Xen Virtualization Environment Clean-Up`_
|  ``VIRT_TEST_GUEST_VM_NAME``: defines the name of the Guest VM to use for the
   tests
|    Default: ``${EWAOL_GUEST_VM_HOSTNAME}1``
|    With standard configuration, the default Guest VM will therefore be
     ``ewaol-guest-vm1``

Prior to execution, the Xen Virtualization test suite expects the
``xendomains.service`` Systemd service to be running or in the process of
initializing.

Xen Virtualization Environment Clean-Up
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Xen Virtualization integration tests only modify the system environment when
the test suite is executed on an image with
:ref:`Security Hardening<manual/hardening:Security Hardening>` enabled, as
accessing the Guest VM on a security hardened image requires setting the user
account password.

There is therefore only a single environment clean operation performed for this
test suite:

    * Clearing the password set when the tests accessed the Guest VM, performed
      only when running the test suite with
      :ref:`Security Hardening<manual/hardening:Security Hardening>` enabled.

Cleaning up the account password will only occur if ``VIRT_TEST_CLEAN_ENV`` is
set to ``1`` (as is default), in which case the environment clean will run
before and after the suite execution.

If enabled then the environment clean operation will always be run, regardless
of test-suite success or failure.
