# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Ensure that all the required kernel config is present in the
# .config file after do_configure

# Validate that the required kernel config is present
# 'required_cfg' is a file containing configs
# 'md5sum' is a checksum of the required_cfg file
# 'ignore_cfg' is an optional string containing configs to ignore during
# the check
def kernelcfg_check(required_cfg, md5sum, d, ignore_cfg=None):
    import hashlib
    import re
    import subprocess

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

    # Find path of all config files with name 'file'
    required_cfg_paths = [root + "/" + required_cfg
                          for root, _, files in os.walk(d.getVar('WORKDIR'))
                          if required_cfg in files]

    bb.note("Kernel Config Files:" + list_format(required_cfg_paths))

    required_config = []

    # Pull config from file if checksum matches
    for cfg_file in required_cfg_paths:
        if md5_file(cfg_file) == md5sum:
            with open(cfg_file) as f:
                # builtin or module is acceptable
                required_config = re.findall('^(CONFIG_[A-Z_]+)=[ym]',
                                             f.read(),
                                             re.MULTILINE)

    # No required config file matching checksum found
    if not required_config:
        bb.warn((f"Kernel Config File {required_cfg} may have been "
                 "overwritten or updated upstream. Ensure no collisions on "
                 f"the following paths: {list_format(required_cfg_paths)} "
                 "\nOr set md5sum to update the checksum."))
        return

    if ignore_cfg:
        for cfg in ignore_cfg.split():
            bb.debug(1, "Ignoring Config: %s" % cfg)
            matched = [i for i in required_config if i.startswith(cfg)]
            if matched:
                required_config.remove(matched[0])

    bb.note("Required Config:" + list_format(required_config))

    missing_config = required_config.copy()

    kernel_cfg_file = d.getVar('B') + "/.config"

    with open(kernel_cfg_file) as kcfg:
        # remove from missing_config if found in kernel config
        for line in kcfg.readlines():
            missing_config = [r for r in missing_config if not re.match(
                              r + "=[ym]", line)]

    # End of kernel config reached, missing_config not found
    if missing_config:
        bb.note("Missing Config:" + list_format(missing_config))
    for mcfg in missing_config:
        bb.warn("Missing Required Kernel Config: %s" % mcfg)
