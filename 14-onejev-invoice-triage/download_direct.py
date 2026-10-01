"""Download a OneJev GGUF model, its vision projector and its tokenizer into models/.

    uv run python download_direct.py                 # OneJev-4B, Q4_K_M (3.2 GB + 0.7 GB)
    uv run python download_direct.py --size 0.8B     # smallest: 0.7 GB + 0.2 GB
    uv run python download_direct.py --size 9B --quant Q4_K_M

Everything lands in models/: nothing is written to the user-wide Hugging Face cache, and the
tokenizer copy lets `qev serve --tokenizer` run fully offline afterwards. Downloads resume after an
interruption, and every file is checked against the SHA-256 published by Hugging Face.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download, snapshot_download

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MODELS = Path(__file__).parent / "models"
SIZES = ("0.8B", "4B", "9B", "27B")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(16 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(repo: str, filename: str, expected: dict[str, str]) -> Path:
    print(f"\n-> {repo}/{filename}")
    path = Path(hf_hub_download(repo_id=repo, filename=filename, local_dir=MODELS))
    digest = sha256(path)
    if digest != expected[filename]:
        raise SystemExit(f"SHA-256 mismatch for {path.name}: got {digest}, expected {expected[filename]}. "
                         f"Delete the file and run this script again.")
    print(f"   {path.stat().st_size / 1e9:.2f} GB, SHA-256 verified ({digest[:16]}...)")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description="Download OneJev GGUF weights, vision projector and tokenizer into models/")
    ap.add_argument("--size", default="4B", choices=SIZES)
    ap.add_argument("--quant", default="Q4_K_M", help="GGUF quantisation (Q4_K_M, Q5_K_M, Q8_0...)")
    args = ap.parse_args()

    repo = f"bartowski/OmniJev_OneJev-{args.size}-GGUF"
    model = f"OmniJev_OneJev-{args.size}-{args.quant}.gguf"
    mmproj = f"mmproj-OmniJev_OneJev-{args.size}-f16.gguf"
    info = HfApi().model_info(repo, files_metadata=True)
    expected = {s.rfilename: s.lfs.sha256 for s in info.siblings if s.lfs}
    if model not in expected:
        quants = sorted(f.rsplit("-", 1)[-1].removesuffix(".gguf") for f in expected if not f.startswith("mmproj"))
        raise SystemExit(f"{model} is not in {repo}; available: {', '.join(quants)}")

    MODELS.mkdir(exist_ok=True)
    fetch(repo, model, expected)
    fetch(repo, mmproj, expected)

    tok_dir = MODELS / f"OneJev-{args.size}-tokenizer"
    print(f"\n-> OmniJev/OneJev-{args.size} tokenizer files")
    snapshot_download(f"OmniJev/OneJev-{args.size}", allow_patterns=["*.json", "*.jinja", "*.txt"], local_dir=tok_dir)
    print(f"   {tok_dir}")

    print("\nReady. Start the OneJev server with:")
    print(f"  uv run qev serve --gguf models/{model} --mmproj models/{mmproj} "
          f"--tokenizer models/{tok_dir.name} --host 127.0.0.1 --port 8000")


if __name__ == "__main__":
    main()
