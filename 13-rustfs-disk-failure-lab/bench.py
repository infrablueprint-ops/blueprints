"""RustFS 1.0.0 (musl) bench - WSL2, throwaway venv, data in /var/tmp/rustfs_lab.

Usage: python bench.py <scenario>
  startup    : 1 drive, DEFAULT settings (credentials, update check); 3 measured cold starts
  throughput : 4 drives (d{1...4}), own credentials, RUSTFS_CHECK_UPDATE=false; throughput + RAM
  failure    : 4 drives; one 64 MiB object, then wipe 1, 2, 3 drives and read it back
  heal       : 4 drives; wipe d4, read once, watch the shard come back
Every measurement prints its raw value; nothing is rounded here.
"""
import concurrent.futures as cf
import hashlib
import os
import shutil
import statistics
import subprocess
import sys
import time
import urllib.request

import boto3
import psutil
from botocore.config import Config

LAB = "/var/tmp/rustfs_lab"
BIN = f"{LAB}/bin_musl/rustfs"
PORT = 9000


def demarrer(volumes, env_extra, log):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("RUSTFS_", "AWS_"))}
    env.update(env_extra)
    t0 = time.perf_counter()
    p = subprocess.Popen([BIN, "server", "--address", f"127.0.0.1:{PORT}", *volumes],
                         stdout=open(log, "w"), stderr=subprocess.STDOUT, env=env)
    while True:
        if p.poll() is not None:
            raise SystemExit(f"rustfs exited (code {p.returncode}), see {log}")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/minio/health/ready", timeout=1) as r:
                if r.status == 200:
                    return p, time.perf_counter() - t0
        except Exception:
            pass
        if time.perf_counter() - t0 > 120:
            p.kill()
            raise SystemExit("not ready within 120 s")
        time.sleep(0.02)


def arreter(p):
    p.terminate()
    try:
        p.wait(20)
    except subprocess.TimeoutExpired:
        p.kill()


def rss_mib(p):
    return psutil.Process(p.pid).memory_info().rss / 2**20


def client(ak, sk):
    return boto3.client("s3", endpoint_url=f"http://127.0.0.1:{PORT}", aws_access_key_id=ak,
                        aws_secret_access_key=sk, region_name="us-east-1",
                        config=Config(s3={"addressing_style": "path"}, max_pool_connections=32,
                                      retries={"max_attempts": 1}))


def propre(*dirs):
    for d in dirs:
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)


def scenario_demarrage():
    print("# 1 drive, default credentials, RUSTFS_CHECK_UPDATE unset (code default)")
    for i in range(1, 4):
        d = f"{LAB}/data_1drive"
        propre(d)
        log = f"{LAB}/log_startup_{i}.txt"
        p, t = demarrer([d], {}, log)
        time.sleep(10)
        print(f"run {i}: ready_s={t:.3f} idle_rss_10s_mib={rss_mib(p):.1f}")
        arreter(p)
    cles = ("default root credentials", "update_check", "New version", "up to date", "Starting RustFS")

    def extraits(log):
        return [l.rstrip() for l in open(log, encoding="utf-8", errors="replace") if any(k in l for k in cles)]

    print(f"\n# run 3 (default log level): {len(extraits(f'{LAB}/log_startup_3.txt'))} line(s) "
          f"matching {cles}")
    print("\n# run 4: same defaults + RUSTFS_OBS_LOGGER_LEVEL=info, 35 s (update check timeout is 30 s)")
    d = f"{LAB}/data_1drive"
    propre(d)
    p, t = demarrer([d], {"RUSTFS_OBS_LOGGER_LEVEL": "info"}, f"{LAB}/log_startup_4.txt")
    time.sleep(35)
    arreter(p)
    for l in extraits(f"{LAB}/log_startup_4.txt"):
        print(l[:600])


def env_propre():
    return {"RUSTFS_ACCESS_KEY": "labadmin", "RUSTFS_SECRET_KEY": "lab-secret-0123456789",
            "RUSTFS_CHECK_UPDATE": "false",
            # 4 folders on 1 WSL virtual disk: test-only bypass provided by RustFS (endpoints.rs:1604)
            "RUSTFS_UNSAFE_BYPASS_DISK_CHECK": "true"}


def quatre_disques():
    base = f"{LAB}/data4"
    propre(*(f"{base}/d{i}" for i in range(1, 5)))
    return base, [f"{base}/d{{1...4}}"]


def scenario_debit():
    base, vols = quatre_disques()
    p, t = demarrer(vols, env_propre(), f"{LAB}/log_throughput.txt")
    print(f"4 drives: ready_s={t:.3f} idle_rss_mib={rss_mib(p):.1f}")
    s3 = client("labadmin", "lab-secret-0123456789")
    s3.create_bucket(Bucket="bench")
    petit = os.urandom(4096)
    pic = 0.0
    for rep in range(1, 4):
        for conc in (1, 16):
            n = 1000
            cles = [f"small/{rep}/{conc}/{i:05d}" for i in range(n)]
            t0 = time.perf_counter()
            with cf.ThreadPoolExecutor(conc) as ex:
                list(ex.map(lambda k: s3.put_object(Bucket="bench", Key=k, Body=petit), cles))
            put = n / (time.perf_counter() - t0)
            t0 = time.perf_counter()
            with cf.ThreadPoolExecutor(conc) as ex:
                list(ex.map(lambda k: s3.get_object(Bucket="bench", Key=k)["Body"].read(), cles))
            get = n / (time.perf_counter() - t0)
            pic = max(pic, rss_mib(p))
            print(f"rep {rep} conc {conc:2d}: PUT_4KiB_obj_s={put:.0f} GET_4KiB_obj_s={get:.0f}")
    gros = f"{LAB}/gros_1GiB.bin"
    if not os.path.exists(gros):
        with open(gros, "wb") as f:
            for _ in range(1024):
                f.write(os.urandom(2**20))
    for rep in range(1, 4):
        t0 = time.perf_counter()
        s3.upload_file(gros, "bench", f"big/{rep}")
        up = 1024 / (time.perf_counter() - t0)
        t0 = time.perf_counter()
        s3.download_file("bench", f"big/{rep}", f"{LAB}/relu.bin")
        down = 1024 / (time.perf_counter() - t0)
        pic = max(pic, rss_mib(p))
        print(f"rep {rep}: PUT_1GiB_MiB_s={up:.0f} GET_1GiB_MiB_s={down:.0f}")
    print(f"rss_pic_mib={pic:.1f}")
    s3.put_object(Bucket="bench", Key="ratio/64MiB", Body=os.urandom(64 * 2**20))
    du = subprocess.run(["du", "-sb", *(f"{base}/d{i}/bench/ratio" for i in range(1, 5))],
                        capture_output=True, text=True).stdout
    print("du -sb of the 4 drives for one 64 MiB object:\n" + du)
    total = sum(int(l.split()[0]) for l in du.splitlines())
    print(f"bytes_on_disk={total} ratio={total / (64 * 2**20):.3f}")
    arreter(p)


def scenario_panne():
    base, vols = quatre_disques()
    p, _ = demarrer(vols, env_propre(), f"{LAB}/log_failure.txt")
    s3 = client("labadmin", "lab-secret-0123456789")
    s3.create_bucket(Bucket="failure")
    data = os.urandom(64 * 2**20)
    ref = hashlib.sha256(data).hexdigest()
    s3.put_object(Bucket="failure", Key="precious.bin", Body=data)
    print(f"object written: 64 MiB sha256={ref[:16]}")
    print("object files on d1:", sorted(os.listdir(f"{base}/d1/failure/precious.bin")))
    for perdus in (1, 2, 3):
        cible = f"{base}/d{5 - perdus}"
        shutil.rmtree(cible)
        os.makedirs(cible)  # empty "replacement" drive
        try:
            lu = s3.get_object(Bucket="failure", Key="precious.bin")["Body"].read()
            ok = hashlib.sha256(lu).hexdigest() == ref
            print(f"{perdus} drive(s) wiped (d{5 - perdus}): GET OK, sha256_identical={ok}")
        except Exception as e:  # noqa: BLE001 - we want the exact error on screen
            print(f"{perdus} drive(s) wiped (d{5 - perdus}): GET FAILED -> {type(e).__name__}: {str(e)[:300]}")
    arreter(p)


def scenario_soin():
    """d4 replaced by an empty folder: does the object come back on d4, and when?"""
    base, vols = quatre_disques()
    p, _ = demarrer(vols, env_propre(), f"{LAB}/log_heal.txt")
    s3 = client("labadmin", "lab-secret-0123456789")
    s3.create_bucket(Bucket="heal")
    s3.put_object(Bucket="heal", Key="precious.bin", Body=os.urandom(64 * 2**20))
    shutil.rmtree(f"{base}/d4")
    os.makedirs(f"{base}/d4")
    t0 = time.perf_counter()
    s3.get_object(Bucket="heal", Key="precious.bin")["Body"].read()  # read after the "failure"
    chemin = f"{base}/d4/heal/precious.bin"
    for _ in range(120):
        if os.path.isdir(chemin) and "xl.meta" in os.listdir(chemin):
            du = subprocess.run(["du", "-sb", chemin], capture_output=True, text=True).stdout.split()[0]
            print(f"d4 rebuilt {time.perf_counter() - t0:.2f} s after the read: {sorted(os.listdir(chemin))}, {du} bytes")
            break
        time.sleep(0.5)
    else:
        print("d4 NOT rebuilt within 60 s")
    arreter(p)


if __name__ == "__main__":
    {"startup": scenario_demarrage, "throughput": scenario_debit, "failure": scenario_panne,
     "heal": scenario_soin}[sys.argv[1]]()
