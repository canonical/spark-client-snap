# spark-k8s-snap
snap for spark on kubernetes

# Build
SNAPCRAFT_BUILD_ENVIRONMENT_MEMORY=8G snapcraft

# Install
sudo snap install --devmode ./spark-k8s_0.1_amd64.snap

# Usage
spark-k8s.spark-submit ...
