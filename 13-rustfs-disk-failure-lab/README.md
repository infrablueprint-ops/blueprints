# 13 - RustFS disk-failure lab (RustFS 1.0.0, tested for real)

Companion code for **["RUSTFS / S3 Explained - We Wiped 2 of 4 Disks (Tested 1.0.0)"](https://youtu.be/K7dxVI5F__Q)**.
Every number in the video comes from these scripts, run on WSL2 Ubuntu 22.04 (12 vCPU, 16 GB)
against the official `rustfs-linux-x86_64-musl-v1.0.0` release binary
(commit `d47f54bfb2f39f48bd1adda334bd27e151fe85b8`).

Raw outputs of the run used in the video: [`captures/`](captures/).

```bash
./setup.sh          # downloads + verifies the release, throwaway venv in /var/tmp/rustfs_lab
./run.sh            # startup, throughput, failure (wipe drives), heal (self-heal)
```

| Scenario | What it does | What we measured |
|---|---|---|
| `startup` | 3 cold starts on 1 drive, default settings; then 1 run at `info` log level | ready in ~0.15 s, ~173 MiB idle RSS; the default-credentials warning only shows at `info` |
| `throughput` | 4 drives, 1 000 x 4 KiB objects (1 and 16 clients), 3 x 1 GiB | ~850 small GET/s (1 client), ~1 100/s (16 clients), 1 GiB GET peak ~1 390 MiB/s, disk ratio x2.0 |
| `failure` | 64 MiB object, then wipe d4, d3, d2 | identical after 2 wiped drives; 3rd drive -> `NoSuchBucket` |
| `heal` | wipe d4, read once | shard rebuilt on d4 in ~4.1 s |

**Honest limits**: one machine, a Python client on the same host, four folders on one
virtual disk (`RUSTFS_UNSAFE_BYPASS_DISK_CHECK=true`, a test-only switch - RustFS
refuses shared devices by default). Lab numbers, not a cluster benchmark.

**Production checklist from the video**: at least 4 disks - your own `RUSTFS_ACCESS_KEY` /
`RUSTFS_SECRET_KEY` - musl build on older distros - `RUSTFS_CHECK_UPDATE=false` offline -
pin the version before every upgrade.
