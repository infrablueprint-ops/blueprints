#!/usr/bin/env bash
# RustFS 1.0.0 disk-failure lab - setup (tested on WSL2 Ubuntu 22.04, 2026-09-24).
# Everything lives in /var/tmp/rustfs_lab: nothing is installed system-wide.
set -euo pipefail
LAB=/var/tmp/rustfs_lab
R=https://github.com/rustfs/rustfs/releases/download/1.0.0
mkdir -p "$LAB" && cd "$LAB"
# The "gnu" build needs glibc >= 2.39 (fails on Ubuntu 22.04 / RHEL 9): use the static musl build.
curl -sSLO "$R/rustfs-linux-x86_64-musl-v1.0.0.zip"
curl -sSLO "$R/SHA256SUMS"
grep 'linux-x86_64-musl-v' SHA256SUMS | sha256sum -c -
python3 -c "import zipfile; zipfile.ZipFile('rustfs-linux-x86_64-musl-v1.0.0.zip').extractall('bin_musl')"
chmod +x bin_musl/rustfs
./bin_musl/rustfs --version   # prints git commit d47f54bfb2f39f48bd1adda334bd27e151fe85b8
# Throwaway venv (works even without the python3-venv package)
python3 -m venv --without-pip venv
curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
venv/bin/python get-pip.py -q
venv/bin/pip install -q boto3==1.35.99 psutil
cp "$(dirname "$0")/bench.py" .
