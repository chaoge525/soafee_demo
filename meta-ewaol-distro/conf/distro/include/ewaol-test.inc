# Config specifc to the ewaol-test distro feature, enabled using
# DISTRO_FEATURES

DISTRO_FEATURES_append = " ptest"
EXTRA_IMAGE_FEATURES_append = " debug-tweaks"
IMAGE_INSTALL_append = " oci-runtime-integration-tests-ptest"
