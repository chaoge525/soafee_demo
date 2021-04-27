# Ensure that all the required kernel config for containers is present in the
# .config file after do_configure

REQ_KERNELCFG_FILENAME ?= "docker.cfg"
# Current checksum, should be updated to track latest containers requirements
# http://git.yoctoproject.org/cgit/cgit.cgi/yocto-kernel-cache/tree/features/docker/docker.cfg
REQ_KERNELCFG_MD5SUM ?= "61e59db3a77cea4b81320305144e9de5"

# Validate that the required kernel config for containers is present
python do_containers_kernelcfg_check() {
    import subprocess, re
    import hashlib

    # Pretty print a list of items
    def list_format(items):
        return ' '.join('\n + %s' % item for item in items)

    # Return the md5 hash of a file from the path
    def md5_file(filepath):
        md5_hash = hashlib.md5()

        f = open(filepath, "rb")
        content = f.read()
        md5_hash.update(content)
        f.close()

        return md5_hash.hexdigest()

    containers_cfg = d.getVar('REQ_KERNELCFG_FILENAME')

    # Find path of all config files with name $REQ_KERNELCFG_FILENAME
    containers_cfg_paths = [ root + "/" + containers_cfg
                             for root, _, files in os.walk(d.getVar('WORKDIR'))
                             if containers_cfg in files ]

    bb.note("Kernel Config Files:" + list_format(containers_cfg_paths))

    required_config = []

    # Pull config from file if checksum matches
    for cfg_file in containers_cfg_paths:
        if md5_file(cfg_file) == d.getVar('REQ_KERNELCFG_MD5SUM'):
            with open(cfg_file) as f:
                # builtin or module is acceptable
                required_config = re.findall('^(CONFIG_[A-Z_]+)=[ym]',
                                              f.read(),
                                              re.MULTILINE)

    # No containers config file matching checksum found
    if not required_config:
        bb.warn("\
Kernel Config File " + containers_cfg + " may have been overwritten or updated \
upstream. Ensure no collisions on the following paths:" + \
list_format(containers_cfg_paths) + "\n\
Or set REQ_KERNELCFG_MD5SUM to update the checksum.")
        return

    bb.note("Required Config:" + list_format(required_config))

    kernel_cfg_file = d.getVar('B') + "/.config"

    missing_config = required_config.copy()

    with open(kernel_cfg_file) as kcfg:
        # remove from missing_config if found in kernel config
        for line in kcfg.readlines():
            missing_config = [r for r in missing_config if not re.match(\
                              r + "=[ym]", line)]

    # End of kernel config reached, missing_config not found
    if missing_config:
        bb.note("Missing Config:" + list_format(missing_config))
    for mcfg in missing_config:
        bb.warn("Missing Required Kernel Config for containers: %s" % mcfg)
}

addtask containers_kernelcfg_check before do_compile after do_configure
