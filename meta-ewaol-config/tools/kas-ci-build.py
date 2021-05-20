#!/usr/bin/env python3

import argparse
import os, sys
import subprocess
import tarfile

ALL_TARGETS=['n1sdp.yml', 'fvp-base.yml']

class DockerEngine:

    CONTAINER_IMAGE_DEFAULT = "ghcr.io/siemens/kas/kas"
    CONTAINER_IMAGE_VERSION_DEFAULT = "latest"
    # Not recommended to use versions 2.4 or less, due to lack of support for
    # KAS_BUILD_DIR
    CONTAINER_ENGINE = "docker"

    def __init__(self, base_args=""):
        self.args = [base_args]

    def addarg(self, arg):
        self.args.append(arg)

    # Set a value in the Environment variables and print
    def setenv(self, key, value):
        val_str = str(value)
        self.addarg(f'-e {key}="{val_str}"')
        print("ENV:",key,"=",value)

    # Add the args to mount a volume in the engine arguments
    def mnt_vol(self, path, name, perms="rw"):
        print("MNT:",path,"at",name,f"({perms})")
        self.addarg(f"-v {path}:{name}:{perms}")

    # Combine mounting a path and setting an env to that path
    def mnt_and_env_format(self, path, env_var, pre_str="", post_str="", perms="rw"):
        mnt_point = "/" + env_var.lower()
        self.mnt_vol(path, mnt_point, perms)
        self.setenv(env_var, pre_str + mnt_point + post_str)

    # Simplify when no formatting strings are required
    def mnt_and_env(self, path, env_var, perms="rw"):
        self.mnt_and_env_format(path, env_var, "", "", perms)

    # Execute the command with generated arguments
    def run(self, kas_config):
        command = \
        f"{self.CONTAINER_ENGINE} run {' '.join(self.args)}\
        {self.CONTAINER_IMAGE_DEFAULT}:{self.CONTAINER_IMAGE_VERSION_DEFAULT}\
        -d build {kas_config}"

        print(command)
        result = subprocess.run(command, shell=True)

        if result.returncode != 0:
            print(f"Error: container command: \n{command}\
                  Failed with returncode {result.returncode}")
            return True
        return False


# Create a directory only if it doesn't already exist
def mk_newdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# replaces colon seperated names of kas config files with full paths
def kasconfig_format(kasfiles, layer_dir, kas_dir, mnt_dir):

    def format_path(kfile):
        return os.path.join(mnt_dir,
                            os.path.relpath(os.path.join(kas_dir, kfile),
                                            layer_dir))

    return ":".join(map(format_path, kasfiles.split(":")))

# Define and parse the provided arguments
def get_config():

    config = {}

    # Get path of script and from their path to kas file directory
    config["script_dir"] = os.path.dirname(os.path.realpath(sys.argv[0]))
    # Path of kas directory of meta-ewaol-config
    config["kas_dir"] = os.path.normpath(os.path.join(config["script_dir"], "../kas"))
    # Path were dependant layers will be downloaded
    config["layer_dir"] = os.path.normpath(os.path.join(config["script_dir"], "../.."))
    # Default output directory
    config["out_dir"] = os.path.join(config["layer_dir"],"ci-build")
    # Default artifact directory
    config["artifacts_dir"] = os.path.join(config["out_dir"],"artifacts")
    # Default parent of SSTATE_DIR and DL_DIR
    config["cache_dir"] = os.path.join(config["out_dir"],"yocto-cache")
    # Default SSTATE_DIR
    config["sstate_dir"] = os.path.join(config["cache_dir"],"sstate-cache")
    # Default DL_DIR
    config["dl_dir"] = os.path.join(config["cache_dir"],"downloads")

    # Parse Arguments and assign to args object
    parser = argparse.ArgumentParser(\
formatter_class=argparse.RawDescriptionHelpFormatter, description=\
"kas-ci-build is used for building yocto based projects, using the kas docker \
image to handle build dependencies.\
\nA kas config yaml file from \
meta-ewaol-config/kas must be provided, and any optional arguments. \
\n\nExample:\n$ ./kas-ci-build all\nto pull the required layers and build both \
n1sdp and fvp-base images sequentially, with no local cache mirrors. ")

    parser.add_argument("kasfile", metavar='[config.yml, all]', help=\
        "The name of a yaml or json file in meta-ewaol-config/kas containing \
        the config for kas. Can be a colon (:) seperated list of files to \
        merge, or 'all'.")

    parser.add_argument("--sstate-dir", default=config["sstate_dir"], help=\
        "Path to local sstate cache for this build \
        (default: " + os.path.relpath(config["sstate_dir"]) + "/)")
    parser.add_argument("--dl-dir", default=config["dl_dir"], help=\
        "Path to local downloads cache for this build \
        (default: " + os.path.relpath(config["dl_dir"]) + "/)")

    parser.add_argument("--sstate-mirror", default="", help=\
        "Path to read-only sstate mirror")

    parser.add_argument("--downloads-mirror", default="", help=\
        "Path to read-only downloads mirror")

    parser.add_argument("--deploy-artifacts", action="store_true", help=\
        "Generate artifacts for CI, and store in artifacts dir",)

    parser.add_argument("--artifacts-dir", default=config["artifacts_dir"], help=\
        "Specify the directory to store the build logs and config after the \
        build if --deploy-artifacts is enabled \
        (default: " + os.path.relpath(config["artifacts_dir"]) + "/)")

    args = vars(parser.parse_args())

    config.update(args)

    return config


# Deploy generated artifacts like build configs and logs.
def deploy_artifacts(build_dir, build_artifacts_dir):

    # Collect config
    build_conf_dir = os.path.join(build_dir,"conf/")

    if os.path.exists(build_conf_dir):
        with tarfile.open(os.path.join(build_artifacts_dir,"conf.tgz"), "w:gz") as conf_tar:
            conf_tar.add(build_conf_dir, arcname=os.path.basename(build_conf_dir))
    else:
        print("No configuration files to pack")

    # Collect logs
    tmp_dir = os.path.join(build_dir,"tmp/")
    work_dir =  os.path.join(tmp_dir,"work/")

    if os.path.exists(tmp_dir):
        with tarfile.open(os.path.join(build_artifacts_dir,"logs.tgz"), "w:gz") as log_tar:
            for path, dirs, files in os.walk(work_dir):
                if "temp" in dirs:
                    log_dir = os.path.join(path,"temp")
                    print("Adding: " + os.path.relpath(log_dir, work_dir))
                    log_tar.add(log_dir, arcname=os.path.relpath(path, work_dir))
    else:
        print("No tmp directory found")

# Entry Point
def main():

    # Parse commandline arguments. Any extra are passed to kas
    config = get_config()

    tasklist = ALL_TARGETS if config["kasfile"] == "all" else [config["kasfile"]]

    exit_code = 0

    for task in tasklist:
        # buildname is the kas file names without path or extension
        buildname = "_".join([os.path.basename(os.path.splitext(kfile)[0])
                              for kfile in task.split(':')
                             ])

        # Name of build dir specific to this config
        config["build_dir"] = os.path.join(config["out_dir"],buildname)

        # Create directories if they don't exist
        mk_newdir(config["out_dir"])
        mk_newdir(config["build_dir"])

        # Always set these docker args
        engine = DockerEngine("--rm")

        # Pass user and group ID to Docker env
        engine.setenv("USER_ID", os.getuid())
        engine.setenv("GROUP_ID", os.getgid())

        # Mount and set up workdir
        work_dir_name = "/work"

        engine.mnt_vol(config["layer_dir"], work_dir_name)
        engine.addarg(f"--workdir={work_dir_name}")
        engine.setenv("KAS_WORK_DIR", work_dir_name)

        # Mount and set up Build directory
        engine.mnt_and_env(config["build_dir"],
                           "KAS_BUILD_DIR")

        # Configure local Caches
        engine.mnt_and_env(config["sstate_dir"],
                           "SSTATE_DIR")

        mk_newdir(config["sstate_dir"])

        engine.mnt_and_env(config["dl_dir"], "DL_DIR")
        mk_newdir(config["dl_dir"])

        # Configure Cache mirrors
        if config["sstate_mirror"]:
            mk_newdir(config["sstate_mirror"])
            engine.mnt_and_env_format(config["sstate_mirror"],
                                      "SSTATE_MIRRORS",
                                      "file://.* file://",
                                      "/PATH;downloadfilename=PATH",
                                      "ro")

        if config["downloads_mirror"]:
            mk_newdir(config["downloads_mirror"])
            engine.mnt_and_env_format(config["downloads_mirror"],
                                      "SOURCE_MIRROR_URL",
                                      "file://",
                                      "",
                                      "ro")
            engine.setenv('INHERIT',"own-mirrors")
            engine.setenv('BB_GENERATE_MIRROR_TARBALLS',"1")

        # kasfiles must be relative to docker filesystem
        kas_config = kasconfig_format(task,
                                      config["layer_dir"],
                                      config["kas_dir"],
                                      work_dir_name)

        # Execute the command
        exit_code = 1 if engine.run(kas_config) else exit_code

        # Grab build artifacts and store in artifacts_dir/buildname
        if config["deploy_artifacts"]:
            mk_newdir(config["artifacts_dir"])

            build_artifacts_dir = os.path.join(config["artifacts_dir"], buildname)
            mk_newdir(build_artifacts_dir)

            deploy_artifacts(config["build_dir"], build_artifacts_dir)

    # Result with docker exit code
    exit(exit_code)

if __name__ == "__main__":
    main()

