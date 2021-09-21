#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

import argparse
import enum
import os
import signal
import subprocess
import sys
import tarfile
import time
import yaml


class ContainerEngine:
    """ Simple class used to configure and run kas under a container """

    def __init__(self, engine, image, image_version):
        self.CONTAINER_NAME = f"kas_build.{int(time.time())}"
        self.args = [f"--rm --name {self.CONTAINER_NAME}"]
        self.container_engine = engine
        self.container_image = image
        self.container_image_version = image_version

    def add_arg(self, arg):
        """ Add a container engine run argument """
        print(f"Adding arg: {arg}")
        self.args.append(arg)

    def add_env(self, key, value):
        """ Add a container engine run environment argument """
        arg = f'--env {key}="{value}"'
        self.add_arg(arg)

    def add_volume(self, path_host, path_container, perms="rw", env_var=None):
        """ Add a container engine run volume argument.
        When 'env_var' is used, also add an environment argument with 'env_var'
        being the key and 'path_container' the value """

        path_host_absolute = path_host
        if not os.path.isabs(path_host):
            path_host_absolute = os.path.realpath(path_host)

        self.add_arg(f"--volume {path_host_absolute}:{path_container}:{perms}")
        if env_var:
            self.add_env(env_var, path_container)

    def run(self, kas_config, kas_command):
        """ Invoke the container engine with all arguments previously added to
            the object. """

        command = f"{self.container_engine} run {' '.join(self.args)}\
                    {self.container_image}:{self.container_image_version}\
                    {kas_command} {kas_config}"

        def handle_interrupt(signum, frame):
            """ If this script is aborted while we have started a detached
                container subprocess, we should stop it before exiting """

            # Additional signals should be handled normally, so deregister
            signal.signal(signal.SIGINT, signal.default_int_handler)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)

            print((f"Recieved signal ({signum}) during the run process, "
                  "sending a stop command to the build container"),
                  file=sys.tee)

            # Stop the container
            stop_cmd = [self.container_engine, "stop", self.CONTAINER_NAME]
            stop_proc = subprocess.Popen(stop_cmd,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         universal_newlines=True)

            stop_stdout, stop_stderr = stop_proc.communicate()
            print(stop_stdout)
            print(stop_stderr)

            stop_proc.wait()
            if stop_proc.returncode is None or stop_proc.returncode > 0:
                print(("Error: failed to stop the build container via:\n."
                       " ".join(stop_cmd)), file=sys.tee)

            exit(1)

        signal.signal(signal.SIGINT, handle_interrupt)
        signal.signal(signal.SIGTERM, handle_interrupt)

        # Start the build container
        print(command, file=sys.tee)
        proc = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                shell=True)

        for next_line in proc.stdout:
            print(next_line.decode(), end='')

        proc.wait()

        # Deregister the signal handler as the subprocess is complete
        signal.signal(signal.SIGINT, signal.default_int_handler)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

        if proc.returncode is None or proc.returncode > 0:
            print((f"Error: container command: \n{command}\n"
                  f"Failed with return code {proc.returncode}"), file=sys.tee)
            return 1

        return 0


# Create a directory only if it doesn't already exist
def mk_newdir(path):
    if not os.path.exists(path):
        os.makedirs(path)


# replaces colon seperated names of kas config files with full paths
def kasconfig_format(kasfiles, project_root, kas_dir, mnt_dir):

    def format_path(kfile):
        return os.path.join(mnt_dir,
                            os.path.relpath(os.path.join(kas_dir, kfile),
                                            project_root))

    return ":".join(map(format_path, kasfiles.split(":")))


# Get all "*-build" configs from kas-runner config file
def get_build_configs(configs):
    config_list = []
    for key in configs.keys():
        if key.endswith("-build"):
            config_list.append(key)
    return config_list


# self referential dictionary
class ArgumentsDictionary(dict):
    def __getitem__(self, item):
        value = dict.__getitem__(self, item)
        if isinstance(value, str):
            return value % self
        else:
            return value


# Define and parse the provided arguments
def get_config():

    config = ArgumentsDictionary({})

    args_defaults = ArgumentsDictionary({
      "artifacts_dir": "%(out_dir)s/artifacts",
      "build_all": False,
      "config": None,
      "container_engine": "docker",
      "container_image": "ghcr.io/siemens/kas/kas",
      "container_image_version": "2.5",
      "deploy_artifacts": False,
      "dl_dir": "%(out_dir)s/yocto-cache/downloads",
      "downloads_mirror": None,
      "engine_arguments": None,
      "j": f"{os.cpu_count()}",
      "kas_arguments": "build",
      "kas_dir": "%(project_root)s/meta-ewaol-config/kas",
      "log_file": None,
      "network_mode": "bridge",
      "out_dir": "%(project_root)s/build",
      "project_root": f"{os.path.realpath(os.getcwd())}",
      "sstate_dir": "%(out_dir)s/yocto-cache/sstate-cache",
      "sstate_mirror": None
    })

    desc = (f"{os.path.basename(__file__)} is used for building yocto based "
            "projects, using the kas image to handle build dependencies.")
    usage = ("A kas config yaml file from meta-ewaol-config/kas must be "
             "provided, and any optional arguments.")
    example = (f"Example:\n$ {os.path.basename(__file__)} all\nto pull the "
               "required layers and build all images (as output by "
               "--list-configs) sequentially, with no local cache mirrors.")

    # Parse Arguments and assign to args object
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f"{desc}\n{usage}\n{example}\n\n")

    parser.add_argument(
        "kasfile",
        nargs='*',
        metavar='[config.yml, all]',
        help="The names of yaml or json files in meta-ewaol-config/kas \
             containing the config for the kas build. Can provide multiple \
             space-separated build configs, where each config can be a colon \
             (:) seperated list of .yml files to merge, or 'all'.")

    parser.add_argument(
        "--config",
        help="Load script parameters from file (default: %(default)s).")

    parser.add_argument(
        "--out-dir",
        help=f"Path to build directory (default: {args_defaults['out_dir']})")

    parser.add_argument(
        "--sstate-dir",
        help=f"Path to local sstate cache for this build \
             (default: {args_defaults['sstate_dir']})")

    parser.add_argument(
        "--dl-dir",
        help=f"Path to local downloads cache for this build \
             (default: {args_defaults['dl_dir']})")

    parser.add_argument(
        "--sstate-mirror",
        help="Path to read-only sstate mirror")

    parser.add_argument(
        "--downloads-mirror",
        help="Path to read-only downloads mirror")

    parser.add_argument(
        "--deploy-artifacts",
        dest="deploy_artifacts",
        action="store_const",
        const=True,
        help=f"Generate artifacts for CI, and store in artifacts dir (default:\
              {args_defaults['deploy_artifacts']})")

    parser.add_argument(
        "--no-deploy-artifacts",
        dest="deploy_artifacts",
        action="store_const",
        const=False,
        help="Do not generate artifacts for CI")

    parser.add_argument(
        "--artifacts-dir",
        help=f"Specify the directory to store the build logs, config and \
             images after the build if --deploy-artifacts is enabled (default:\
             {args_defaults['artifacts_dir']})")

    parser.add_argument(
        "--network-mode",
        help=f"Set the network mode of the container (default: \
             {args_defaults['network_mode']}).")

    parser.add_argument(
        "--container-engine",
        help=f"Set the container engine (default: \
             {args_defaults['container_engine']}).")

    parser.add_argument(
        "--container-image",
        help=f"Set the container image (default: \
             {args_defaults['container_image']}).")

    parser.add_argument(
        "--engine-arguments",
        help="Optional string of arguments for running the container, e.g.\
              --engine-arguments '--volume /host/dir:/container/dir \
                                  --env VAR=value'.")

    parser.add_argument(
        "--container-image-version",
        help=f"Set the container image version (default: \
             {args_defaults['container_image_version']}). Note: it is not \
             recommended to use versions 2.4 or lower for kas containers \
             due to lack of support for KAS_BUILD_DIR.")

    parser.add_argument(
        "-j",
        help=f"Sets number of threads used by bitbake, by exporting\
             environment variable BB_NUMBER_THREADS = J\
             (default: {args_defaults['j']})")

    parser.add_argument(
        "--kas-arguments",
        help=f"Arguments to be passed to kas executable within the container \
             (default: {args_defaults['kas_arguments']}).")

    parser.add_argument(
        "--log-file",
        help=f"Write output to the given log file as well as to stdout \
             (default: {args_defaults['log_file']}).")

    parser.add_argument(
        "--list-configs",
        action="store_true",
        help="List all named configs from the config file specified with a \
             '--config' parameter.")

    parser.add_argument(
        "--project-root",
        help=f"Project root path (default: {args_defaults['project_root']}).")

    args = ArgumentsDictionary(vars(parser.parse_args()))

    # load script defaults
    config.update(args_defaults)

    if "all" in args["kasfile"]:
        if args.get("project_root") is None:
            args["project_root"] = config["project_root"]
        if not args["config"]:
            # if 'config' is not specified, load ci.yml config
            args["config"] = \
                "%(project_root)s/meta-ewaol-config/kas-runner/ci.yml"
        config['build_all'] = True
        args.pop("kasfile")

    if args["config"]:
        # 'config' is a string like "path/to/config_file.yml[:named_config]"
        # check if named_config is specified
        config_input = args["config"].split(":", maxsplit=1)
        config_file = config_input[0]
        named_config = config_input[1] if len(config_input) == 2 else None

        with open(config_file, "r") as yaml_file:
            yaml_content = yaml.safe_load(yaml_file)
            header = yaml_content["header"]
            configs = yaml_content["configs"]
            try:
                # check if header version is supported
                if header["version"] < 1:
                    print(f"ERROR: incompatible version of config file")
                    exit(1)
                if named_config is None:
                    named_config = next(iter(configs))
                if not config['build_all']:
                    config.update(configs[named_config])
            except KeyError as e:
                print(f"ERROR: invalid configs {args['config']}")
                exit(1)

    for (key, value) in args.items():
        # do not pass empty lists into the config
        if value or isinstance(value, bool):
            # update config with cmdline parameters
            config[key] = args[key]
            # update configs list, by removing keys overwritten via cmdline
            if 'configs' in locals():
                for named_config in configs.keys():
                    if configs[named_config].get(key) is not None:
                        configs[named_config].pop(key)
                config["configs"] = configs

    if config.get("kasfile") is None and not config["build_all"]:
        print("ERROR: No kas configs specified!")
        exit(1)

    if config["list_configs"]:
        if config["config"] is None:
            print("ERROR: No kas-runner configs specified!")
        else:
            print(f"Build targets: {' '.join(get_build_configs(configs))}")
        exit(1)

    return config


# Deploy generated artifacts like build configs and logs.
def deploy_artifacts(build_dir, build_artifacts_dir):

    # Collect config
    build_conf_dir = os.path.join(build_dir, "conf")

    if os.path.exists(build_conf_dir):
        tar_filename = os.path.join(build_artifacts_dir, "conf.tgz")
        with tarfile.open(tar_filename, "w:gz") as conf_tar:
            conf_tar.add(build_conf_dir,
                         arcname=os.path.basename(build_conf_dir))

        print(f"Deployed build configuration artifacts into {tar_filename}")
    else:
        print("No build configuration files to archive")

    # Collect logs
    tar_filename = os.path.join(build_artifacts_dir, "logs.tgz")
    with tarfile.open(tar_filename, "w:gz") as log_tar:

        cooker_log = os.path.join(build_dir, "bitbake-cookerdaemon.log")
        if os.path.exists(cooker_log):
            arcname = os.path.join("logs", os.path.basename(cooker_log))
            log_tar.add(cooker_log, arcname=arcname)

        tmp_dir = os.path.join(build_dir, "tmp")
        if os.path.exists(tmp_dir):

            console_dir = os.path.join(tmp_dir, "log/cooker")
            for path, dirs, files in os.walk(console_dir):
                if "console-latest.log" in files:

                    log_link = os.path.join(path, "console-latest.log")
                    log = os.path.join(path, os.readlink(log_link))

                    arcname = os.path.relpath(log_link, console_dir)
                    arcname = os.path.join("logs", arcname)
                    log_tar.add(log, arcname=arcname)

            work_dir = os.path.join(tmp_dir, "work")
            for path, dirs, files in os.walk(work_dir):

                if "temp" in dirs:
                    log_dir = os.path.join(path, "temp")
                    arcname = os.path.relpath(path, work_dir)
                    arcname = os.path.join("logs", arcname)
                    log_tar.add(log_dir, arcname=arcname)

                if "pseudo.log" in files:
                    pseudo_log = os.path.join(path, "pseudo.log")
                    arcname = os.path.relpath(pseudo_log, work_dir)
                    arcname = os.path.join("logs", arcname)
                    log_tar.add(pseudo_log, arcname=arcname)

            print(f"Deployed build logs into {tar_filename}")

            # Collect images
            base_image_dir = os.path.join(tmp_dir, "deploy/images")
            if os.path.exists(base_image_dir):

                tar_filename = os.path.join(build_artifacts_dir, "images.tgz")
                with tarfile.open(tar_filename, "w:gz") as image_tar:
                    image_tar.add(base_image_dir,
                                  arcname=os.path.basename(base_image_dir))

                print(f"Deployed images into {tar_filename}")
            else:
                print("No image directory found, did not archive images")

        else:
            print("No tmp directory found, did not archive build artifacts")


# Entry Point
def main():

    # Parse commandline arguments. Any extra are passed to kas
    config = get_config()

    if config["log_file"]:
        mk_newdir(os.path.dirname(os.path.realpath(config["log_file"])))
        log_file = open(config["log_file"], "w")

        # By default, if we have a log file then only write to it
        # But provide a logger to write to both terminal and the log file for
        # important messages
        sys.tee = TeeLogger(LogOpt.TO_BOTH, log_file)
        sys.stdout = TeeLogger(LogOpt.TO_FILE, log_file)

    else:
        # If we have no log file, write both stdout and tee to only terminal
        sys.tee = TeeLogger(LogOpt.TO_TERM)

    exit_code = 0

    # 'all' will make kas-runner to ignore other kas config files passed via
    # via commandline and build all *-build named-configs from selected
    # config file instead.
    tasklist = get_build_configs(config["configs"]) if config["build_all"] \
        else config["kasfile"]

    if config["build_all"]:
        config_backup = config

    for build_task in tasklist:

        print(f"Starting build task: {build_task}", file=sys.tee)

        # load named-config settings into current config
        if config["build_all"]:
            # to keep original parameters for other build_tasks,
            # add build_task customization on a copy of config
            config = ArgumentsDictionary(config_backup)
            config.update(config["configs"][build_task])
            kas_files = config["kasfile"][0]
        else:
            kas_files = build_task

        # Check that all config files for the target exist
        missing_confs = "\n".join(
            filter(lambda kfile:
                   not os.path.isfile(os.path.join(config["kas_dir"], kfile)),
                   kas_files.split(":")))

        if missing_confs:
            print((f"Error: The kas config files: \n{missing_confs}\nwere not"
                  " found."), file=sys.tee)
            exit_code = 1
            continue

        # buildname is the kas file names without path or extension
        buildname = "_".join([os.path.basename(os.path.splitext(kfile)[0])
                             for kfile in kas_files.split(':')])

        # Name of build dir specific to this config
        config["build_dir"] = os.path.join(config["out_dir"], buildname)

        # Create directories if they don't exist
        mk_newdir(config["out_dir"])
        mk_newdir(config["build_dir"])

        engine = ContainerEngine(config["container_engine"],
                                 config["container_image"],
                                 config["container_image_version"])

        # Pass user and group ID to container engine env
        engine.add_env("USER_ID", os.getuid())
        engine.add_env("GROUP_ID", os.getgid())

        # Mount and set up workdir
        work_dir_name = "/work"
        engine.add_volume(config["project_root"], work_dir_name)
        engine.add_arg(f"--workdir={work_dir_name}")
        engine.add_env("KAS_WORK_DIR", work_dir_name)

        # Mount and set up build directory
        engine.add_volume(config["build_dir"],
                          "/kas_build_dir",
                          env_var="KAS_BUILD_DIR")

        # Configure local caches
        engine.add_volume(config["sstate_dir"],
                          "/sstate_dir",
                          env_var="SSTATE_DIR")
        mk_newdir(config["sstate_dir"])

        engine.add_volume(config["dl_dir"], "/dl_dir", env_var="DL_DIR")
        mk_newdir(config["dl_dir"])

        # Set network mode
        network_mode = config["network_mode"]
        engine.add_arg(f"--network={network_mode}")

        # Configure cache mirrors
        if config["sstate_mirror"]:
            path = "/sstate_mirrors"
            mk_newdir(config["sstate_mirror"])
            engine.add_volume(config["sstate_mirror"], path, "ro")
            engine.add_env(
                "SSTATE_MIRRORS",
                f"file://.* file://{path}/PATH;downloadfilename=PATH")

        if config["downloads_mirror"]:
            path = "/source_mirror_url"
            mk_newdir(config["downloads_mirror"])
            engine.add_volume(config["downloads_mirror"], path, "ro")
            engine.add_env("SOURCE_MIRROR_URL", f"file://{path}")
            engine.add_env('INHERIT', "own-mirrors")
            engine.add_env('BB_GENERATE_MIRROR_TARBALLS', "1")

        # kasfiles must be relative to container filesystem
        kas_config = kasconfig_format(kas_files,
                                      config["project_root"],
                                      config["kas_dir"],
                                      work_dir_name)

        if config['engine_arguments']:
            engine.add_arg(config['engine_arguments'])

        engine.add_env('BB_NUMBER_THREADS', config['j'])

        # Execute the command
        exit_code |= engine.run(kas_config, config['kas_arguments'])

        # Grab build artifacts and store in artifacts_dir/buildname
        if config["deploy_artifacts"]:
            mk_newdir(config["artifacts_dir"])

            build_artifacts_dir = os.path.join(config["artifacts_dir"],
                                               buildname)
            mk_newdir(build_artifacts_dir)

            deploy_artifacts(config["build_dir"], build_artifacts_dir)

        print(f"Finished build task: {build_task}\n", file=sys.tee)

    exit(exit_code)


class LogOpt(enum.Enum):
    TO_TERM = enum.auto()
    TO_FILE = enum.auto()
    TO_BOTH = enum.auto()


class TeeLogger(object):
    """ Logging class that outputs to either stdout or a log file, or both """

    def __init__(self, log_opt, log_file_handler=None):
        self.terminal = sys.stdout
        self.log_opt = log_opt
        self.log_file = log_file_handler

    def write(self, msg):
        if self.log_opt == LogOpt.TO_BOTH:
            self.terminal.write(msg)
            self.log_file.write(msg)

        elif self.log_opt == LogOpt.TO_TERM:
            self.terminal.write(msg)

        elif self.log_opt == LogOpt.TO_FILE:
            self.log_file.write(msg)

    def flush(self):
        self.terminal.flush()
        if self.log_file:
            self.log_file.flush()

    def __del__(self):
        if not self.log_file.closed:
            self.log_file.close()


if __name__ == "__main__":
    main()
