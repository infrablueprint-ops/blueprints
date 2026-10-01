"""Invoice triage with OneJev: one image in, every accounting decision out, in a single request.

Start the OneJev server first (see README), then:

    uv run python invoice_triage.py samples/invoices/01_nimbus_saas_invoice.pdf
    uv run python invoice_triage.py samples/invoices/*.pdf samples/invoices/*.jpg --labels samples/invoices/labels.json
    uv run python invoice_triage.py my_scan.jpg --config my_categories.json

The questions and every category description live in a JSON file (default: invoice_categories.json),
so the triage is customised by editing text, not code. The model never generates free text: for each
question it returns calibrated probabilities over the options you defined.
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import sys
import time
from pathlib import Path

import pymupdf
from PIL import Image
from qev import Client
from qev.media import data_uri

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_page(path: Path, dpi: int) -> Image.Image:
    """First page of a PDF rendered at `dpi`, or an image file as is."""
    if path.suffix.lower() == ".pdf":
        with pymupdf.open(path) as doc:
            pix = doc[0].get_pixmap(dpi=dpi)
        return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    return Image.open(path).convert("RGB")


def triage(client: Client, image: Image.Image, config: dict) -> tuple[dict, float]:
    """Ask every question of `config` about one document image; return the answers and the latency."""
    t0 = time.perf_counter()
    r = client.system_one(
        state={"task": config["task"], "document": "<image:1>"},
        questions=config["questions"],
        media=[{"type": "image", "data": data_uri(image)}],
    )
    return {k: v.raw for k, v in r.answers.items()}, (time.perf_counter() - t0) * 1000


def top(answer: dict) -> tuple[str, float]:
    """Predicted label and its probability, for any answer type."""
    if answer["type"] == "noul":
        p = answer["noul"]
        return ("yes", p) if p >= 0.5 else ("no", 1 - p)
    if answer["type"] == "choice":
        return answer["choice"], answer["probabilities"][answer["choice"]]
    level = round(answer["score"])
    return answer["legend"][str(level)], answer["probabilities"][str(level)]


def print_document(name: str, answers: dict, ms: float) -> None:
    print(f"\n{name}  ({ms:.0f} ms, {len(answers)} questions)")
    for qid, ans in answers.items():
        label, p = top(ans)
        extra = f"   score {ans['score']:.2f}" if ans["type"] == "score" else ""
        print(f"  {qid:15s} {label:24s} {p * 100:5.1f}%{extra}")


def score_against(labels: dict, results: dict) -> dict:
    """Accuracy per question against the ground truth; `null` labels are not scored."""
    per_q: dict[str, list[int]] = {}
    misses = []
    for name, res in results.items():
        truth = labels.get(name)
        if truth is None:
            continue
        for qid, expected in truth.items():
            if expected is None or qid not in res["answers"]:
                continue
            ans = res["answers"][qid]
            got, p = top(ans)
            want = ("yes" if expected else "no") if isinstance(expected, bool) else expected
            ok = got == want
            per_q.setdefault(qid, []).append(int(ok))
            if not ok:
                misses.append({"document": name, "question": qid, "expected": want, "got": got,
                               "probability": round(p, 3)})
    summary = {q: {"correct": sum(v), "total": len(v)} for q, v in per_q.items()}
    return {"per_question": summary, "misses": misses}


def main() -> None:
    ap = argparse.ArgumentParser(description="Categorise invoices and receipts with OneJev in one request per document")
    ap.add_argument("files", nargs="+", help="PDF or image files (globs accepted)")
    ap.add_argument("--config", default="invoice_categories.json", help="questions and category descriptions")
    ap.add_argument("--url", default="http://127.0.0.1:8000", help="OneJev server (qev serve)")
    ap.add_argument("--dpi", type=int, default=150, help="PDF rendering resolution")
    ap.add_argument("--labels", default=None, help="ground-truth JSON to score the run (simulation mode)")
    ap.add_argument("--out", default="output/invoice_triage.json", help="where to write the full report")
    args = ap.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    paths = sorted({Path(p) for pattern in args.files for p in (glob.glob(pattern) or [pattern])})
    client = Client(args.url, timeout=600)

    results = {}
    for path in paths:
        answers, ms = triage(client, load_page(path, args.dpi), config)
        results[path.name] = {"answers": answers, "latency_ms": round(ms, 1)}
        print_document(path.name, answers, ms)

    latencies = [r["latency_ms"] for r in results.values()]
    print(f"\n{len(results)} documents, {len(config['questions'])} questions each, "
          f"mean {sum(latencies) / len(latencies):.0f} ms per document")

    report = {"config": args.config, "url": args.url, "results": results}
    if args.labels:
        scored = score_against(json.loads(Path(args.labels).read_text(encoding="utf-8")), results)
        report["score"] = scored
        print("\nAccuracy against labels:")
        for qid, s in scored["per_question"].items():
            print(f"  {qid:15s} {s['correct']:2d}/{s['total']:<2d}")
        for m in scored["misses"]:
            print(f"  MISS {m['document']}: {m['question']} expected {m['expected']}, "
                  f"got {m['got']} ({m['probability'] * 100:.1f}%)")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nReport written to {args.out}")


if __name__ == "__main__":
    main()
