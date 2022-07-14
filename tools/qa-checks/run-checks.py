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
import logging.handlers
import multiprocessing
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
import venv

import abstract_check
import commit_msg_check
import doc_build_check
import header_check
import inclusivity_check
import layer_check
import python_check
import shell_check
import spell_check
import yaml_check

path = f'{os.path.dirname(os.path.abspath(__file__))}/../common'
sys.path.append(path)

import modules_virtual_env  # noqa: E402

AVAILABLE_CHECKS = [commit_msg_check.CommitMsgCheck,
                    doc_build_check.DocBuildCheck,
                    header_check.HeaderCheck,
                    inclusivity_check.InclusivityCheck,
                    layer_check.LayerCheck,
                    python_check.PythonCheck,
                    shell_check.ShellCheck,
                    spell_check.SpellCheck,
                    yaml_check.YamlCheck,
                    ]

# The following keywords can be passed as values to the arguments.
# They will be set to their correct mapped values lazily.
KEYWORD_MAP = dict()
KEYWORD_MAP["ROOT"] = None
KEYWORD_MAP["GITIGNORE_CONTENTS"] = None

CHECK_NAMES = [check.name for check in AVAILABLE_CHECKS]
VALID_CHECKS = set(CHECK_NAMES + ["default", "all"])

LOG_LEVELS = {
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG
}

DEFAULT_CONFIG_FILE = "meta-ewaol-config/qa-checks/qa-checks_config.yml"


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

    project_root = eval_keyword("ROOT").rstrip('/')
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

    desc = ("run-checks.py is used to execute a set of quality-check modules"
            " on the repository. By default, a virtual Python environment is"
            " created to install the Python packages necessary to run the"
            " suite.")
    usage = ("Optional arguments can be found by passing --help to the script")
    example = ("\nExample:\n$ ./run-checks.py\n"
               "to run all default checks in a virtual environment, according"
               " to the per-check configuration within the default config YAML"
               " file.")

    sets = (f"The available checks are: {{{','.join(CHECK_NAMES)}}}.")

    note = (" Note: only checks defined in the config file will be run by"
            " default, unless no config is defined, or called directly.")

    # Parse Arguments and assign to args object
    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f"{desc}\n{usage}\n\n{example}\n\n{sets}\n\n{note}")

    parser.add_argument("--check", action="append", default=[],
                        dest="checks",
                        metavar="{" + ",".join(sorted(VALID_CHECKS)) + "}",
                        help=("Comma-separated list: Add specific checks to"
                              " run, or the 'default' set, or 'all' checks. If"
                              " not given, then the default config modules"
                              " will be used as defined by the config and/or "
                              " default_check_excludes. Multiple checks can be"
                              " specified as a list and by passing the"
                              " argument multiple times."))

    # Internal usage: a requested check may be skipped using this option (e.g.
    # due to failed dependency-installation in the virtual environment)
    parser.add_argument("--skip", action="append", default=[],
                        choices=CHECK_NAMES,
                        dest="skip_checks",
                        help=argparse.SUPPRESS)

    # Each check has its own path options to include/exclude
    for check in AVAILABLE_CHECKS:

        name = check.name
        settings = check.get_vars()

        group = parser.add_argument_group(f"{name} check arguments")

        for setting in settings:
            prefix = ""
            if setting.is_list:
                prefix = "Comma-separated list: "
            group.add_argument(f"--{name}_{setting.name}", required=False,
                               help=(f"{prefix}{setting.message}"))

    parser.add_argument("--config",
                        help=("YAML file that holds configuration defaults for"
                              " the checkers (default: <PROJECT_ROOT>/"
                              f"{DEFAULT_CONFIG_FILE})"
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
                        help=("Define the root path of the target project,"
                              " used as the base path for any check argument"
                              " given as a relative file-path (Default:"
                              f" {default_root})"))

    parser.add_argument("--log", default="info",
                        choices=LOG_LEVELS.keys(),
                        help="Set the log level (Default: info).")

    parser.add_argument("--default_check_excludes",
                        help=("Comma-separated list: Exclude a list of checks"
                              " from being run as 'default'."))

    parser.add_argument("--number_threads",
                        default=min(os.cpu_count(), len(AVAILABLE_CHECKS)),
                        type=int,
                        help=("Set the max number of threads to use to run"
                              " checks."))

    opts = parser.parse_args()

    return opts


def parse_config(config_path):
    """ Parse the config file and return a dictionary with all config options.
        """

    # Create a dictionary of valid checks and parameters
    valid_params = {}
    for check in AVAILABLE_CHECKS:
        settings = check.get_vars()
        valid_params[check.name] = {
            setting.name: setting for setting in settings}

    config_dict = {}

    try:
        import yaml

        with open(config_path, 'r') as config_file:
            yaml_content = yaml.safe_load(config_file)

            if 'run_checks_settings' in yaml_content:
                config_settings = yaml_content['run_checks_settings']
                valid_settings = {'default_check_excludes'}
                for setting_name, value in config_settings.items():
                    if setting_name in valid_settings:
                        config_dict[setting_name] = value
                    else:
                        logger.warning(
                            f"Cannot set run_checks_settings/{setting_name}"
                            " from config. Currently only"
                            f" {{{','.join(sorted(valid_settings))}}} can be "
                            "set from config.")

            if 'defaults' in yaml_content:
                defaults = yaml_content['defaults']
            else:
                defaults = {}

            modules = yaml_content['modules']
            config_dict['all_checks'] = modules.keys()

            for module, params in modules.items():

                # Warn if there are non existent modules configured.
                if module not in valid_params:
                    logger.warning(f"Check module {module} was not found.")
                    continue

                valid_check_params = valid_params[module]

                if params is not None:
                    for key, value in params.items():
                        # Warn if there are extra parameters defined.
                        if key not in valid_check_params:
                            logger.warning(f"Config param {module}/{key} is"
                                           " invalid")
                            continue
                        config_dict[f'{module}_{key}'] = value

                for key, value in defaults.items():
                    # Ignore default if not for this module
                    if key not in valid_check_params:
                        continue

                    full_key = f'{module}_{key}'
                    # Ignore if value already found
                    if full_key in config_dict:
                        continue
                    config_dict[full_key] = value

    except FileNotFoundError:
        logger.error(f"Config file '{config_filename}' was not found.")
        exit(1)
    except ImportError:
        logger.error(("Could not import the Python yaml module. Either install"
                      " 'pyyaml' via pip on the host system to load"
                      " the YAML configuration file, or pass --no_config."))
        exit(1)
    except KeyError:
        logger.error(f"Invalid config {config_filename}")
        exit(1)

    return config_dict


def resolve_checks_list(opts, config):
    """ Process and validate the list of checks.
        The order of priority to use (highest first):
            command line, config file, default.
        If default or all is provided, these override the value.
        """

    # If no config then use hard coded all
    if opts.no_config is True:
        all_checks = CHECK_NAMES
        default_checks = []
    # If there is a config, then 'all' defined as all checks in config
    elif 'all_checks' in config:
        all_checks = config['all_checks']
        # 'default' is 'all' with 'default_check_excludes' removed.
        default_checks = [check for check in all_checks
                          if check not in opts.default_check_excludes]
    # If there is a config that defines no checks then 'all' and 'default' are
    # empty
    else:
        all_checks = []
        default_checks = []

    # Split any comma separated checks in the list
    checks = []
    for check_sublist in opts.checks:
        checks.extend(check_sublist.split(","))
    opts.checks = checks

    # Validate values
    has_invalid_check = False
    for check in opts.checks:
        if check not in VALID_CHECKS:
            logger.error(f"Argument 'check': value '{check}' is invalid."
                         f" Choose from {VALID_CHECKS}")
            has_invalid_check = True
    if has_invalid_check:
        exit(1)

    # Set default here because the append action extends the argparse default
    # rather than replaces the default
    if len(opts.checks) == 0 or "default" in opts.checks:
        opts.checks = default_checks

    if "all" in opts.checks:
        opts.checks = all_checks


def resolve_check_param_from_config(key, config, setting):
    """ Get the check param value from config (if it exists, None otherwise)
        and perform config specific value validation. """

    value = None
    if key in config:
        value = config[key]
        if value is not None:
            # Check the resulting type is as expected
            if ((setting.is_list and type(value) is not list) or
                    (not setting.is_list and type(value) is list)):
                logger.error((f"Type of {check_name} {param} in"
                              f" {config_filename} does not match type"
                              " expected by check module. Discarding"
                              " this value."))
                return None
            if setting.is_list and None in value:
                logger.error(("Found one or more empty elements for the"
                              f" {check_name} {param} list variable in"
                              f" {config_filename}. Discarding this"
                              " value."))
                return None
    return value


def resolve_check_param(opts, config, check_name, setting):
    """ For a parameter, we check if we have a value from the command line
        arguments. If we do, we either append it to or replace the default in
        the configuration YAML file, depending on whether or not it is a list
        variable. If no value can be found and the variable is not optional,
        then the check will be skipped, by removing it from the opts.

        If --no_config was supplied, config will be empty so config_value will
        be None.

        If the parameter is a pattern then special formatting is applied. """
    param = setting.name
    key = f"{check_name}_{param}"
    is_list = setting.is_list

    value = None
    try:
        value = getattr(opts, key)
        if value is not None and is_list:
            value = value.split(",")
    except AttributeError:
        pass

    config_value = resolve_check_param_from_config(key, config, setting)
    # Merge with list from config file
    if config_value is not None and is_list:
        if value is not None:
            value.extend(config_value)

    if value is None:
        value = config_value

    if value is None:
        # Nothing supplied for this parameter

        if not setting.required:
            # Optional, so use its default value (which may be None)
            value = setting.default

    # If value is still None, then we didn't find anything for this param
    # from command line or config file and the default value is None
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
        if (not opts.no_process_patterns and setting.is_pattern):
            if is_list:
                converted_patterns = []
                for pattern in value:
                    converted = convert_gitstyle_pattern_to_regex(pattern)
                    converted_patterns.append(converted)
                value = converted_patterns
            else:
                value = convert_gitstyle_pattern_to_regex(value)

    setattr(opts, key, value)

    if value is None and setting.required:
        return False
    else:
        return True


def resolve_check_params(opts, config):
    """ Process and validate all check settings for all checks. """

    for check in AVAILABLE_CHECKS:
        check_name = check.name

        if check_name not in opts.checks or check_name in opts.skip_checks:
            continue

        settings = check.get_vars()
        missing_params = []

        for setting in settings:
            found = resolve_check_param(opts, config, check_name, setting)
            if not found:
                missing_params.append(setting.name)

        if missing_params:
            logger.warning((f"Missing parameters for {check_name} check:"
                            f" {missing_params}, skipping this check."))
            opts.checks.remove(check_name)


def resolve_settings(opts):
    """ Perform validation and operations relating to the options supplied. """

    # Resolve 'log'
    logger.setLevel(LOG_LEVELS.get(opts.log.lower()))

    # Resolve 'venv' and 'no_venv'
    # Validate the opts (venv and no_venv are mutually exclusive)
    if opts.venv is not None and opts.no_venv is True:
        logger.error((f"Cannot provide a path via --venv while also setting"
                      " --no_venv."))
        exit(1)

    # Resolve 'project_root'
    opts.project_root = os.path.abspath(opts.project_root)
    # Initialize the keyword value to the user-provided root
    KEYWORD_MAP["ROOT"] = opts.project_root

    # Resolve 'config'
    if opts.config is None:
        opts.config = os.path.join(opts.project_root, DEFAULT_CONFIG_FILE)

    if opts.no_config:
        config = {}
    else:
        config = parse_config(opts.config)

    # Resolve 'default_check_excludes'
    value = []
    if opts.default_check_excludes is not None:
        value.extend(opts.default_check_excludes.split(","))

    if 'default_check_excludes' in config and config['default_check_excludes']:
        value.extend(config['default_check_excludes'])

    opts.default_check_excludes = value

    # Resolve 'checks'
    resolve_checks_list(opts, config)

    # Resolve 'skip_checks'
    # Only allow a check to be skipped if it has been provided
    if opts.skip_checks:
        if any([skip not in opts.checks for skip in opts.skip_checks]):
            logger.error("Cannot skip a check that wasn't requested.")
            exit(1)

    # Resolve all check params
    resolve_check_params(opts, config)


def load_check_params(
        opts,
        check_name,
        settings):
    """ Load check params from the resolved opts. """

    params = dict()
    missing_params = list()

    for setting in settings:
        key = f"{check_name}_{setting.name}"
        value = getattr(opts, key)
        params[setting.name] = value

    return params


def build_check_modules(opts):
    """ For each module, check that we have values for all required variables
        either from the command-line arguments, and/or from the configuration
        YAML file. Ignore any skipped checks. """

    checkers = []

    queue = multiprocessing.Queue(-1)

    for check_module in AVAILABLE_CHECKS:
        name = check_module.name
        if name in opts.checks and name not in opts.skip_checks:

            settings = check_module.get_vars()

            params = load_check_params(opts, name, settings)

            if params:
                # All check modules have a project_root variable
                params["project_root"] = eval_keyword("ROOT")

                check_logger = logging.getLogger(name)
                check_logger.addHandler(logging.handlers.QueueHandler(queue))

                check = check_module(check_logger, **params)
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


def run_checker(checker):
    rc = 0
    try:
        rc = checker.run()
    except Exception as e:
        logger.error(("Caught exception when executing the"
                      f" {checker.name} check:"))
        logger.error(''.join(traceback.format_exception(
            etype=type(e), value=e, tb=e.__traceback__)))
        rc = 1

    return rc


def run_checks_parallel(checkers, failed_modules, number_threads):

    logger.debug("Creating process pool")

    proc_pool = multiprocessing.Pool(number_threads)
    queue = multiprocessing.Queue(-1)

    queue_listener = logging.handlers.QueueListener(
        queue, *logger.handlers, respect_handler_level=True)

    queue_listener.start()
    logger.debug("Waiting for processes.")
    checker_rcs = proc_pool.map(run_checker, checkers)

    queue_listener.stop()

    rc = 0

    # Process return codes
    for i, checker in enumerate(checkers):
        checker_rc = checker_rcs[i]
        if checker_rc != 0:
            failed_modules.add(checker.name)

        rc |= checker_rc

    return rc


def main():
    if sys.version_info < (3, 8):
        raise ValueError("This script requires Python 3.8 or later")

    exit_code = 0

    # Get the options that the user supplied
    opts = parse_options()

    # Process and validate the options
    resolve_settings(opts)

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

        exit_code |= run_checks_parallel(checkers, failed_modules,
                                         opts.number_threads)

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
