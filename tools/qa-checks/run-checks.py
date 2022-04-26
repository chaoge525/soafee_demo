#!/usr/bin/env python3
#
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""
This tool can be used to run the quality-assurance (QA) check modules. By
default, the tool utilises the ModulesVirtualEnv class to build a Python
virtual environment in which all necessary Python package dependencies will be
installed, which then provides an execution context for the tool to run the
checks, without mutating the host system's Python environment.

To execute the checks, the tool first receives from the user a set of requested
checks to run, selected from a list of available checks. Each check provides
its required Python packages to be installed in the virtual environment, as
well as its list of required configuration variables, which must be provided
either via a command-line argument, or defined within a YAML configuration
file. Assuming the required packages can be installed and the necessary
configuration variables have been provided, the ModulesVirtualEnvironment calls
this tool again from the virtual environment context, with all variables
defined as command-line arguments, as well as an additional "--no_venv" option.
The checks are then execution in succession.

In order to be compatible with this tool, check modules must inherit the
AbstractCheck class, and their run function should return a value of zero for
success or non-zero for failure. This tool will return zero if all requested
checks succeed, otherwise the tool will return 1.

Usage instructions are available by passing --help (-h) as a command-line
argument to this script.
"""

import argparse
import inspect
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import venv

import abstract_check
import commit_msg_check
import header_check
import layer_check
import python_check
import shell_check
import spell_check

path = f'{os.path.dirname(os.path.abspath(__file__))}/../common'
sys.path.append(path)

import modules_virtual_env  # noqa: E402

AVAILABLE_CHECKS = [commit_msg_check.CommitMsgCheck,
                    header_check.HeaderCheck,
                    layer_check.LayerCheck,
                    python_check.PythonCheck,
                    shell_check.ShellCheck,
                    spell_check.SpellCheck
                    ]

# All checks except these will be run by default if specific checkers are not
# requested.
DEFAULT_EXCLUDE = [layer_check.LayerCheck]

# The following keywords can be passed as values to the arguments.
# They will be set to their correct mapped values lazily.
KEYWORD_MAP = dict()
KEYWORD_MAP["ROOT"] = None
KEYWORD_MAP["GITIGNORE_CONTENTS"] = None


def convert_gitstyle_pattern_to_regex(pattern):
    """ Patterns provided as gitstyle patterns (e.g. "*.log" or /build") are
        converted in this function to regex based on the rules listed here:
        https://git-scm.com/docs/gitignore
    """

    pattern = pattern.strip()
    pattern = pattern.replace(".", r"\.")

    if pattern.startswith("#") or pattern == "":
        return None

    if pattern.startswith("!"):
        logger.warn(("Pattern exclusions via '!' are not supported, this"
                     f"character in '{pattern}' will be treated literally."))

    if len(pattern) > 1:
        pattern = pattern.rstrip("/")

    pattern = pattern.replace("*", r"[^/]*")
    pattern = pattern.replace("?", r"[^/]")

    project_root = eval_keyword("ROOT")
    if pattern.startswith("/"):
        pattern = f"{project_root}{pattern}"
        pass
    else:
        pattern = f"{project_root}/+.*{pattern}"

    return pattern


def load_gitignore_file():
    """ Checks may ignore the same patterns as .gitignore, so parse the file
        and convert it as a list of regex strings to pass to the checks. """
    ignored = []

    project_root = eval_keyword("ROOT")
    try:
        with open(f"{project_root}/.gitignore", 'r') as f:

            ignored = []
            for line in f:
                ignored.append(line)

    except FileNotFoundError:
        logger.warn(f"No .gitignore was not found in {project_root}.")

    return ignored


def eval_keyword(keyword):
    """ The user may use keywords when configuring the checks. This function
        provides access to the mapped values for those keywords.
        To avoid unnecessary work, keyword mappings are only evaluated if they
        are needed.

        The ROOT keyword is set via a user-argument.
        """

    if keyword not in KEYWORD_MAP:
        # This should never happen
        raise ValueError(f"Internal error: keyword {keyword} not recognized.")

    if KEYWORD_MAP[keyword] is None:
        if keyword == "GITIGNORE_CONTENTS":
            KEYWORD_MAP[keyword] = load_gitignore_file()
        else:
            # This should never happen
            raise ValueError((f"Internal error: keyword {keyword} was not"
                              " initialized."))

    return KEYWORD_MAP[keyword]


def parse_options():

    loglevels = {
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG
    }

    check_names = [check.name for check in AVAILABLE_CHECKS]
    excluded_check_names = [check.name for check in DEFAULT_EXCLUDE]
    default_check_names = [name for name in check_names
                           if name not in excluded_check_names]

    desc = ("run-checks.py is used to execute a set of quality-check modules"
            " on the repository. By default, a virtual Python environment is"
            " created to install the Python packages necessary to run the"
            " suite.")
    usage = ("Optional arguments can be found by passing --help to the script")
    example = ("\nExample:\n$ ./run-checks.py\n"
               "to run all default checks in a virtual environment, according"
               " to the per-check configuration within the default config YAML"
               " file.")

    excluded_str = ""
    if excluded_check_names:
        excluded_str = ("\nAdditional non-default checks can be enabled"
                        f" explicitly: {{{','.join(excluded_check_names)}}}.")
    sets = (f"The default checks are: {{{','.join(default_check_names)}}}."
            f"{excluded_str}")

    # Parse Arguments and assign to args object
    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f"{desc}\n{usage}\n\n{example}\n\n{sets}")

    parser.add_argument("--check", action="append", default=[],
                        choices=check_names + ["default", "all"],
                        dest="checks",
                        help=("Add a specific check to run, or the 'default'"
                              " set, or 'all' checks. If not given, then the"
                              " default set will be run."))

    # Internal usage: a requested check may be skipped using this option (e.g.
    # due to failed dependency-installation in the virtual environment)
    parser.add_argument("--skip", action="append", default=[],
                        choices=check_names,
                        dest="skip_checks",
                        help=argparse.SUPPRESS)

    # Each check has its own path options to include/exclude
    for check in AVAILABLE_CHECKS:

        name = check.name
        list_args, args, _ = check.get_vars()

        for arg, msg in {**list_args, **args}.items():
            prefix = ""
            if arg in list_args:
                prefix = "Comma-separated list: "
            parser.add_argument(f"--{name}_{arg}", required=False,
                                help=(f"{prefix}{msg}"))

    default_config_file = "meta-ewaol-config/qa-checks/qa-checks_config.yml"
    parser.add_argument("--config",
                        help=("YAML file that holds configuration defaults for"
                              " the checkers (default: <PROJECT_ROOT>/"
                              f"{default_config_file})"
                              ))

    parser.add_argument("--no_config",
                        action="store_true",
                        help=("If set, the configuration defaults within the"
                              " YAML file will be ignored (default: False,"
                              " meaning user-arguments will be appended to"
                              " the defaults given in the YAML file)."))

    # Internal usage: If set, any supplied patterns will not be considered
    # gitstyle patterns, and will therefore not be converted for regex
    # matching. This parameter indicates that this has already been done by the
    # caller of the script)
    parser.add_argument("--no_process_patterns",
                        action="store_true",
                        help=argparse.SUPPRESS)

    parser.add_argument("--venv",
                        required=False,
                        help=("Provide a Python virtual environment directory"
                              " in which to run the checks (default: auto"
                              " generate a new virtual environment directory)."
                              " Cannot be passed with --no_venv."))

    parser.add_argument("--no_venv",
                        action="store_true",
                        help=("Run the checks directly in the calling context"
                              " without using up a Python virtual environment."
                              " Cannot be passed with --venv."))

    parser.add_argument("--keep_venv",
                        action="store_true",
                        default=False,
                        help=("Do not delete the temporary Python virtual"
                              " environment directory after the checks have"
                              " been completed (Default: False)"))

    default_root = f"{os.path.dirname(os.path.abspath(__file__))}/../../"
    default_root = os.path.abspath(default_root)

    parser.add_argument("--project_root",
                        required=False,
                        default=default_root,
                        help=("Define the project root path, from which all"
                              " provided relative paths will be considered"
                              f" (Default: {default_root})"))

    parser.add_argument("--log", default="info",
                        choices=["debug", "info", "warning"],
                        help="Set the log level (Default: info).")

    opts = parser.parse_args()

    logger.setLevel(loglevels.get(opts.log.lower()))

    # Validate the opts (venv and no_venv are mutually exclusive)
    if opts.venv is not None and opts.no_venv is True:
        logger.error((f"Cannot provide a path via --venv while also setting"
                      " --no_venv."))
        exit(1)

    # Only allow a check to be skipped if it has been provided
    if opts.skip_checks:
        if any([skip not in opts.checks for skip in opts.skip_checks]):
            logger.error("Cannot skip a check that wasn't requested.")
            exit(1)

    # Set default here because the append action extends the argparse default
    # rather than replaces the default
    if len(opts.checks) == 0 or "default" in opts.checks:
        opts.checks = default_check_names

    if "all" in opts.checks:
        opts.checks = check_names

    if opts.config is None:
        opts.config = os.path.join(opts.project_root, default_config_file)

    # Initialize the keyword value to the user-provided root
    KEYWORD_MAP["ROOT"] = opts.project_root

    return opts


def load_param_from_config(config_filename, check_name, param, list_param):
    """ Check the config YAML file for the existance of the given parameter
        for the given check module. The boolean list_param determines if the
        value should read and validated as a list type.
        If a value is not found, then a default will be taken from the defaults
        YAML section..

        Return None if no value could be found. """

    value = None

    try:
        import yaml

        with open(config_filename, 'r') as config_file:
            config = yaml.safe_load(config_file)

            found_value = False
            found_default = False

            # Check if there is a default
            default = None
            try:
                default = config["defaults"][param]
                found_default = True
            except KeyError:
                pass

            # Check if there is a defined value in the config
            try:
                value = config["modules"][check_name][param]
                found_value = True
            except KeyError:
                pass

            if found_value:
                pass
            elif found_default:
                # Replace with the default
                value = default
            else:
                return None

            if value is not None:
                # Check the resulting type is as expected
                if ((list_param and type(value) is not list) or
                        (not list_param and type(value) is list)):
                    logger.error((f"Type of {check_name} {param} in"
                                  f" {config_filename} does not match type"
                                  " expected by check module. Discarding"
                                  " this value."))
                    return None
                if list_param and None in value:
                    logger.error(("Found one or more empty elements for the"
                                  f" {check_name} {param} list variable in"
                                  f" {config_filename}. Discarding this"
                                  " value."))
                    return None

    except FileNotFoundError:
        logger.error(f"Config file '{config_filename}' was not found.")
        exit(1)
    except ImportError:
        logger.error(("Could not import the Python yaml module. Either install"
                      " 'pyyaml' via pip on the host system to load"
                      " the YAML configuration file, or pass --no_config."))
        exit(1)

    return value


def load_check_params(
        opts,
        check_name,
        list_vars,
        plain_vars,
        optional_var_names):
    """ For each variable, we check if we already have a value from the command
        line arguments. If we do, we either append it to or replace the default
        in the configuration YAML file, depending on whether or not it is a
        list variable. If no value can be found and the variable is not
        optional, then the check will be skipped, by removing it from the opts.

        If --no_config was supplied, the YAML file is not read at all, and
        only the user-supplied arguments considered. """

    params = dict()
    missing_params = list()

    combined_list = list_vars + plain_vars

    for param in combined_list:
        key = f"{check_name}_{param}"

        is_list = param in list_vars

        # Get value from config file
        config_value = None
        if opts.no_config is False:
            config_value = load_param_from_config(opts.config,
                                                  check_name,
                                                  param,
                                                  is_list)

        # Get value from command line args
        value = None
        try:
            value = getattr(opts, key)
            if value is not None and is_list:
                value = value.split(",")
        except AttributeError:
            pass

        # Merge with list from config file
        if config_value is not None and is_list:
            if value is not None:
                value.extend(config_value)

        if value is None:
            value = config_value

        # If value is still None, then we didn't find anything for this param
        # from command line or config file
        if value is not None:

            # Replace any keywords with mapped values
            # If it's a list, extend with the contents of the keyword
            # If it's not a list, replace with the contents of the keyword
            if is_list:
                value = [eval_keyword(element) if element in KEYWORD_MAP
                         else element for element in value]

                # Make sure the list is flattened
                flattened_list = []
                for element in value:
                    # Make sure we don't include strings in the flattening
                    if isinstance(element, str):
                        flattened_list.append(element)
                    else:
                        flattened_list.extend([val for val in element])
                value = flattened_list

            else:
                value = eval_keyword(value) if value in KEYWORD_MAP else value
                if type(value) is list:
                    logger.warn(("Used a list keyword for a non-list"
                                 f"parameter: {check_name}_{param}. Discarding"
                                 " the value."))
                    return None

            # If the parameter is a pattern, convert it for regex matching
            if (not opts.no_process_patterns and
                    (param.endswith("_pattern") or
                     param.endswith("_patterns"))):
                if is_list:
                    converted_patterns = []
                    for pattern in value:
                        converted = convert_gitstyle_pattern_to_regex(pattern)
                        converted_patterns.append(converted)
                    value = converted_patterns
                else:
                    value = convert_gitstyle_pattern_to_regex(value)

            params[param] = value
            setattr(opts, key, value)
        else:
            # Nothing supplied for this parameter

            if param in optional_var_names:
                # Optional, so pass it through to the check module as None
                value = None
                params[param] = value
                setattr(opts, key, value)
            else:
                # Required, set as missing
                missing_params.append(param)

    if missing_params:
        logger.warning((f"Missing parameters for {check_name} check:"
                        f" {missing_params}, skipping this check."))
        opts.checks.remove(check_name)
        return None

    return params


def build_check_modules(opts):
    """ For each module, check that we have values for all required variables
        either from the command-line arguments, and/or from the configuration
        YAML file. Ignore any skipped checks. """

    checkers = []

    for check_module in AVAILABLE_CHECKS:
        name = check_module.name
        if name in opts.checks and name not in opts.skip_checks:

            list_vars, plain_vars, optional_var_names = check_module.get_vars()

            params = load_check_params(opts,
                                       name,
                                       list(list_vars.keys()),
                                       list(plain_vars.keys()),
                                       optional_var_names)

            if params:
                # All check modules have a project_root variable
                params["project_root"] = eval_keyword("ROOT")

                check = check_module(logger, **params)
                checkers.append(check)

    return checkers


def generate_venv_script_args_from_opts(opts):
    """ In order to call this script from the virtual environment, convert the
        processed options to a string array, and adjust settings accordingly:
        - Remove --venv and --key_venv, replace with --no_venv (already built)
        - Add --no_process_patterns (patterns already processed)

        """

    args = []
    for opt, value in vars(opts).items():
        arg = ""
        if opt == "venv" or opt == "keep_venv":
            # remove the venv arguments
            continue
        elif opt == "no_venv":
            # set the no_venv argument
            arg = opt
        elif opt == "no_config":
            # in the venv, we don't need to load the YAML again
            arg = "no_config"
        elif value is None:
            continue
        elif opt == "no_process_patterns":
            # Set the no_process_patterns argument
            arg = "no_process_patterns"
        elif opt == "checks":
            for check in value:
                arg = f"--check={check}"
                args.append(arg)
            continue
        elif opt == "skip_checks":
            for check in value:
                arg = f"--skip={check}"
                args.append(arg)
            continue
        else:
            if type(value) is list:
                arg = f"{opt}=\"{','.join(value)}\""
            else:
                arg = f"{opt}=\"{value}\""

        args.append(f"--{arg}")

    return args


def main():
    if sys.version_info < (3, 8):
        raise ValueError("This script requires Python 3.8 or later")

    exit_code = 0

    # Get the options that the user supplied
    opts = parse_options()

    # Build the checkers, loading configuration from the config file if
    # necessary
    checkers = build_check_modules(opts)

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

    # Print the options (only when we intend to run the checks)
    if opts.no_venv is True:
        logger.debug("***")
        logger.debug("Script arguments:")
        for key, val in vars(opts).items():
            # We change the venv arguments programmatically, so don't print to
            # avoid confusing the user with a different value
            if "venv" not in key and "skip_checks" not in key:
                logger.debug(f"{key}:{val}")
        logger.debug("***")

    if opts.no_venv:

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

        for skipped_check in opts.skip_checks:

            # Get the check module object from the name
            skipped_module = next(filter(lambda module:
                                         module.name == skipped_check,
                                         AVAILABLE_CHECKS))

            # Report the failure from the context of the skipped module, by
            # first overriding the filename used by the logger, outputting the
            # failure, then resetting the filename

            skipped_filename = inspect.getmodule(skipped_module).__file__
            logger.filename_override = os.path.basename(skipped_filename)
            logger.error("FAIL")
            logger.filename_override = None

            failed_modules.add(skipped_check)
            exit_code |= 1

        fail_str = ""
        if failed_modules:
            fail_str = f" ({','.join(failed_modules)})"

        total_checks = len(checkers) + len(opts.skip_checks)
        total_check_str = "check" if total_checks == 1 else "checks"

        logger.info((f"Ran {total_checks} {total_check_str} of which"
                     f" {len(failed_modules)} failed{fail_str}."
                     f" Exit code: {exit_code}."))

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
            pip_dependencies[checker.name] = checker.get_pip_dependencies()

        virt_env = modules_virtual_env.ModulesVirtualEnv(script,
                                                         arg_str,
                                                         pip_dependencies,
                                                         logger)

        venv_dirname = None
        if opts.venv is not None:
            venv_dirname = opts.venv
            if not os.path.isdir(venv_dirname):
                logger.error("Cannot find the given venv directory:"
                             f"{venv_dirname}. Aborting.")
                exit(1)
            logger.debug(f"Using existing venv directory: {venv_dirname}")
        else:
            venv_dirname = tempfile.mkdtemp()
            if opts.keep_venv:
                logger.info(f"Created new venv directory: {venv_dirname}")
            else:
                logger.debug(f"Created new venv directory: {venv_dirname}")

        virt_env.create(venv_dirname)
        exit_code = virt_env.returncode

        if opts.venv is None and opts.keep_venv is False:
            shutil.rmtree(venv_dirname)
            logger.debug(f"Deleted the venv directory: {venv_dirname}")

    exit(exit_code)


class FilenameFormatter(logging.Formatter):
    """ The script's standard logging format includes the filename to identify
        what the message relates to (e.g. 'python-check.py: PASS').
        However, we may want to output a message pertaining to a particular
        module, from outside that module (e.g. 'python-check.py: SKIPPED').

        As the Python logging module determines the filename by inspecting the
        stack via the sys module, the value of this variable cannot easily be
        changed. Therefore, this class conditionally swaps the logging
        format to a custom one that reads the contents of the logger's
        filename_override string (if it is not None) instead of using the
        filename variable. """

    def __init__(self):
        self.fmt_str = "%(levelname)-8s:{filename}:%(message)s"
        logging.getLogger().filename_override = None
        super().__init__(fmt=self.fmt_str.format(filename="%(filename)-24s"),
                         style='%')

    def format(self, record):
        original_format = self._style._fmt

        if logging.getLogger().filename_override:
            self._style._fmt = self.fmt_str.format(
                filename=f"{logging.getLogger().filename_override:24}")

        output = logging.Formatter.format(self, record)

        if logging.getLogger().filename_override:
            self._style._fmt = original_format

        return output


if __name__ == "__main__":

    basic_log_format = "%(levelname)-8s:%(filename)-24s:%(message)s"
    formatter = FilenameFormatter()
    logging.basicConfig(format=basic_log_format)
    logger = logging.getLogger()
    logger.handlers[0].setFormatter(formatter)

    main()
