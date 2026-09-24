#!/usr/bin/env bash
# Replays every measurement shown in the video. Usage: ./run.sh [startup|throughput|failure|heal]
set -euo pipefail
cd /var/tmp/rustfs_lab
for s in "${@:-startup throughput failure heal}"; do
  for scenario in $s; do
    echo "=== $scenario"; venv/bin/python bench.py "$scenario"
  done
done
