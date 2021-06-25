#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import venv
import yaml

import abstract_check
import commit_msg_check
import modules_virtual_env
import python_check
import shell_check
import spell_check

AVAILABLE_CHECKS = ["commit_msg",
                    "python",
                    "shell",
                    "spell"]


def parse_options(project_root, check_config_filename):

    loglevels = {
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG
    }

    desc = ("run-checks.py is used to execute a set of quality-check modules"
            " on the repository. By default, a virtual Python environment is"
            " created to install the Python packages necessary to run the"
            " suite.")
    usage = ("Optional arguments can be found by passing --help to the script")
    example = ("Example:\n$ ./run-checks.py --check=all --log=debug\n"
               "to run all checks with the default include/exclude paths as"
               " found in check-defaults.yml, and maximum log verbosity.")

    # Parse Arguments and assign to args object
    parser = argparse.ArgumentParser(
        prog=__name__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f"{desc}\n{usage}\n{example}\n\n")

    parser.add_argument("--check", action="append", default=[],
                        choices=AVAILABLE_CHECKS + ["all"],
                        dest="checks",
                        help=("Add a specific check to run, or 'all'"
                              " (default: 'all')."))

    # Each check has its own path options to include/exclude
    for check in AVAILABLE_CHECKS:

        parser.add_argument(f"--{check}_paths",
                            required=False,
                            help=("Comma-separated list of additional paths to"
                                  f" run the {check} check on."))
        parser.add_argument(f"--{check}_excludes",
                            required=False,
                            help=("Comma-separated list of additional paths to"
                                  f" exclude from {check} check."))

    parser.add_argument("--venv",
                        required=False,
                        help=("Provide a Python virtual environment directory"
                              " in which to run the checks (default: auto"
                              " generate a new virtual environment directory)."
                              " Cannot be passed with --novenv."))

    parser.add_argument("--novenv",
                        action="store_true",
                        help=("Run the checks directly in the calling context"
                              " without using up a Python virtual environment."
                              " Cannot be passed with --venv."))

    parser.add_argument("--log", default="info",
                        choices=["debug", "info", "warning"],
                        help="Set log level.")

    opts = parser.parse_args()

    if opts.venv is not None and opts.novenv is True:
        logger.error((f"Cannot provide a path via --venv while also setting"
                      " --novenv."))
        exit(1)

    logger.setLevel(loglevels.get(opts.log.lower()))

    # Set default here because the append action extends the argparse default
    # rather than replaces the default
    if len(opts.checks) == 0 or "all" in opts.checks:
        opts.checks = AVAILABLE_CHECKS

    # Command line arguments are appended to those already defined in the
    # config file
    try:
        with open(check_config_filename, 'r') as config_file:
            config = yaml.safe_load(config_file)

            for check in opts.checks:

                for var in ["paths", "excludes"]:

                    combined_list = []

                    # Check if user has provided custom values on the command
                    # line
                    key = f"{check}_{var}"
                    if getattr(opts, key):

                        # Convert any relative paths to absolute
                        paths = getattr(opts, key).split(",")
                        abs_paths = []
                        for path in paths:
                            if os.path.isabs(path):
                                abs_paths.append(path)
                            else:
                                abs_paths.append(os.path.join(project_root,
                                                              path))
                        combined_list.extend(abs_paths)

                    # Add values from the config file
                    if (config is not None and
                            check in config and
                            config[check] is not None):

                        if var in config[check]:
                            defaults = config[check][var].split()
                            paths = []
                            for path in defaults:
                                paths.append(os.path.join(project_root,
                                                          path))
                            combined_list.extend(paths)

                    if combined_list:
                        # Remove duplicates before setting the option
                        combined_list = list(set(combined_list))
                        setattr(opts, key, ",".join(combined_list))

                # If user nor config file defined a path for the check, then
                # set project root as the default
                if getattr(opts, f"{check}_paths") is None:
                    setattr(opts, f"{check}_paths", project_root)

    except (FileNotFoundError, IOError):
        logger.error(("Could not load the configuration YAML from"
                      f"{check_config_filename}. Aborting."))
        exit(1)

    # Only output the arguments when we intend to run the checks
    if opts.novenv is True:
        logger.debug("***")
        logger.debug("Script arguments:")
        for key, val in vars(opts).items():
            # We change the venv arguments programmatically, so don't print to
            # avoid confusing the user with a different value
            if "venv" not in key:
                logger.debug(f"{key}:{val}")
        logger.debug("***")

    return opts


def generate_venv_script_args_from_opts(opts):
    """ In order to call this script from the virtual environment, convert the
        processed options to a string array, and replace --venv with --novenv.
        """

    args = []
    for opt, value in vars(opts).items():
        if opt == "venv":
            # remove the venv argument
            continue
        elif opt == "novenv":
            # set the novenv argument
            arg = opt
        elif value is None:
            continue
        elif opt == "checks":
            for check in value:
                arg = f"--check={check}"
                args.append(arg)
            continue
        else:
            arg = f"{opt}={value}"

        args.append(f"--{arg}")

    return args


def main():
    if sys.version_info < (3, 6):
        raise ValueError("This script requires Python 3.6 or later")

    exit_code = 0

    project_root = f"{os.path.dirname(os.path.abspath(__file__))}/../../"
    project_root = os.path.abspath(project_root)

    check_config_filename = (f"{os.path.dirname(os.path.abspath(__file__))}"
                             "/check-defaults.yml")

    opts = parse_options(project_root, check_config_filename)

    # Build each requested checker
    checkers = []

    if "commit_msg" in opts.checks:
        commit_checker = commit_msg_check.CommitMsgCheck(
                            logger,
                            opts.commit_msg_paths,
                            opts.commit_msg_excludes)

        checkers.append(commit_checker)

    if "python" in opts.checks:
        python_checker = python_check.PythonCheck(logger,
                                                  opts.python_paths,
                                                  opts.python_excludes)
        checkers.append(python_checker)

    if "shell" in opts.checks:
        shell_checker = shell_check.ShellCheck(logger,
                                               opts.shell_paths,
                                               opts.shell_excludes)
        checkers.append(shell_checker)

    if "spell" in opts.checks:
        spell_checker = spell_check.SpellCheck(logger,
                                               opts.spell_paths,
                                               opts.spell_excludes)
        checkers.append(spell_checker)

    if not checkers:
        logger.info("Found no requested checks to run.")
        exit(0)

    # Validate checkers conform to API
    for checker in checkers:
        if not issubclass(type(checker), abstract_check.AbstractCheck):
            logger.error((f"The {checker} check must extend the AbstractCheck"
                          " class in order to run it as part of the check"
                          " suite. Aborting."))
            exit(1)

    if opts.novenv:

        failed_modules = set()

        # Run the checkers
        for checker in checkers:
            rc = 0
            try:
                rc = checker.run()
                if rc != 0:
                    failed_modules.add(checker.name)
            except Exception as e:
                logger.error(("Caught exception when executing the"
                              f" {checker.name} check:"))
                logger.error(e)
                failed_modules.add(checker.name)
                rc = 1

            exit_code |= rc

        fail_str = ""
        if failed_modules:
            fail_str = f" ({','.join(failed_modules)})"

        check_count_str = "checks" if len(checkers) == 1 else "checks"
        logger.info((f"Ran {len(checkers)} {check_count_str} of which"
                     f" {len(failed_modules)} failed{fail_str}. Exit code:"
                     f" {exit_code}."))

    else:
        # Create a virtual environment that installs the necessary
        # dependencies, then runs this script again from the virtual env
        # context with updated args

        script = os.path.abspath(__file__)
        args = generate_venv_script_args_from_opts(opts)
        arg_str = " ".join(args)

        # Collect each checker's dependencies to pass to the venv
        pip_dependencies = dict()
        for checker in checkers:
            pip_deps = checker.get_pip_dependencies()
            pip_dependencies[checker.name] = pip_deps

        # Add dependencies for this script (key is None for no module)
        pip_dependencies[None] = ["pyyaml"]

        virt_env = modules_virtual_env.ModulesVirtualEnv(script,
                                                         arg_str,
                                                         pip_dependencies,
                                                         logger)

        venv_dirname = None
        if opts.venv is not None:
            venv_dirname = opts.venv
            logger.debug(f"Using existing venv directory: {venv_dirname}")
        else:
            venv_dirname = tempfile.mkdtemp()
            logger.info(f"Created new venv directory: {venv_dirname}")

        virt_env.create(venv_dirname)
        exit_code = virt_env.returncode

    exit(exit_code)


if __name__ == "__main__":
    log_format = "%(levelname)-8s:%(filename)-24s:%(message)s"
    logging.basicConfig(format=log_format)
    logger = logging.getLogger(__name__)

    main()
