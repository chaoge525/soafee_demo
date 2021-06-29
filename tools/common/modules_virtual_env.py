#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

import logging
import os
import subprocess
import urllib.request
import venv


class ModulesVirtualEnv(venv.EnvBuilder):
    """ Class that recieves a script, a set of arguments for running the
        script, and a dict of module-dependencies required to run the script
        with those arguments. A Python virtual environment is then created, in
        which the dependencies are installed, and the script is called from
        that virtual environment context as a subprocess.

        module_pip_deps:
            - Dict mapping a module name (key) to a list (value) of pip package
              names to be installed by pip in the Python virtual environment.
              e.g. module_pip_deps["code_check"] = ["pyyaml", "pycodestyle"]

        If a dependency fails to be installed, all script arguments containing
        the module name (substring given by dict key) are removed from the
        script call.

        If a dependency is given with a None key (no module), then it is
        considered essential to run the script itself, and execution will abort
        if it is unable to be installed. """

    def __init__(self,
                 script,
                 arg_str,
                 module_pip_deps,
                 logger):

        self.script = script
        self.arg_str = arg_str
        self.module_pip_deps = module_pip_deps
        self.logger = logger
        self.returncode = None

        super().__init__()

    def post_setup(self, context):
        """ Called once the virtual environment has been built and setup, and
            contains the main logic of the class, installing dependencies and
            running the script in the venv. """

        # We set the VENV_BIN so that modules know if they are in a virtual env
        # So they can source binaries from it
        os.environ['VENV_BIN'] = context.bin_path

        # Install any dependencies
        self.install_dependencies(context)

        # Check that at least one module's dependencies were satisfied
        # Ignore the non-module dependencies
        if not [mod for mod in self.module_pip_deps.keys() if mod is not None]:
            self.logger.error(("All requested modules failed dependency"
                               " installation. Aborting"))
            exit(1)

        # Call the script from the venv context
        cmd = f"{context.env_exe} {self.script} {self.arg_str}"
        self.logger.debug(f"Running script from venv: {cmd}")
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   shell=True,
                                   universal_newlines=True)

        for next_line in process.stdout:
            print(next_line, end='')

        process.wait()

        # Set the returncode variable to report as the result of the venv
        self.returncode = process.returncode

    def install_dependencies(self, context):
        """ Parse the dependency dict and install using the venv context.
            Failed module dependency installs will be removed from the script
            arguments, failed dependency installs not specific to any module
            will cause an abort. """

        if any(deps for deps in self.module_pip_deps.values()):
            self.install_pip(context)

        failed_modules = set()
        installed_packages = set()

        for module, pip_deps in self.module_pip_deps.items():
            for pip_dep in pip_deps:

                # Modules may share dependencies, don't try to install multiple
                # times
                if pip_dep in installed_packages:
                    continue

                if self.install_via_pip(context, pip_dep) == 0:
                    installed_packages.add(pip_dep)
                else:
                    failed_modules.add(module)
                    self.logger.error((f"Could not install {pip_dep} within"
                                       " the virtual env."))

        for failed_module in failed_modules:

            if failed_module is None:
                # The dependencies necessary to run the script itself failed
                # Therefore we must abort
                self.logger.error(("Script direct dependency could not be"
                                   " installed. Aborting."))
                exit(1)

            else:
                # If a module's dependencies could not be installed, skip it
                self.logger.warning(("Dependency installation failed for"
                                     f" {failed_module}. Removing "
                                     f"'{failed_module}' from script "
                                     "execution."))

                self.arg_str = " ".join(filter(lambda arg:
                                               failed_module not in arg,
                                               self.arg_str.split(" ")))

                # Remove from the modules list (given by module_pip_deps)
                self.module_pip_deps.pop(failed_module)

    def install_pip(self, context):
        """ Install pip into the venv context by getting and installing the
            setuptools and pip installer scripts over https. """

        # Check if pip is already available
        process = subprocess.run([context.env_exe, "-m", "pip", "--version"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        if process.returncode != 0:
            url_setuptools = 'https://bootstrap.pypa.io/ez_setup.py'
            self.install_from_url(context, 'setuptools', url_setuptools)

            url_pip = 'https://bootstrap.pypa.io/get-pip.py'
            self.install_from_url(context, 'pip', url_pip)

    def install_from_url(self, context, name, url):
        """ Install package 'name' from given 'url' into the venv 'context'.
            """

        self.logger.debug(f"Installing {name} from URL.")

        script = os.path.basename(url)
        binpath = context.bin_path
        distpath = os.path.join(binpath, script)

        # Download script into the venv's binaries folder
        urllib.request.urlretrieve(url, distpath)

        # Install in the venv
        process = subprocess.Popen([context.env_exe, script],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   cwd=binpath)

        stdout, stderr = process.communicate()

        if process.returncode != 0:
            self.logger.error(f"Failed to install {name} from {url}.")
            self.logger.debug(stdout.decode())
            self.logger.debug(stderr.decode())

        # Clean up - no longer needed
        os.unlink(distpath)

    def install_via_pip(self, context, package):
        """ Install Python package given by 'package' using "pip install"
            within the venv 'context'. """

        args = [context.env_exe, "-m", "pip", "install", package]
        if self.logger.getEffectiveLevel() > logging.INFO:
            args.append("-q")

        process = subprocess.run(args,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        if process.returncode != 0:
            self.logger.error((f"Failed to install Python package '{package}'"
                               " via pip."))
            self.logger.debug(process.stdout.decode())
            self.logger.debug(process.stderr.decode())
        else:
            exists_str = f"already satisfied: {package.split('=')[0]}"
            if exists_str not in process.stdout.decode():
                self.logger.debug(f"Installed Python package '{package}'.")

        return process.returncode
