# 14 - OneJev invoice triage, from zero (tested for real)

Companion code for the Infra Blueprint video [OmniJev OneJev: Local AI Invoice Categorization, From Zero](https://youtu.be/EZT_4F5IiOw) ([30-second Short](https://youtu.be/oM1gAXkBdAc)).
One invoice image in, six accounting decisions out, each with a calibrated probability:
document type, expense category, payment status, VAT shown, amount band and urgency.
100% local, no OCR step, no JSON parsing.

[OneJev](https://github.com/OmniJev/OneJev) (OmniJev, Apache 2.0, on Hugging Face since 2026-09-27) is a *System One*
decision model: you ask typed questions about an image and it answers each one with probabilities over the
options **you** define. Tested here: OneJev-4B Q4_K_M GGUF, `qev` at commit
`81ce62f1597c91e46767d4d02d6ac2e18534fe94`, llama.cpp b11193 (Vulkan), AMD Radeon RX 6950 XT 16 GB,
Windows 11. Raw outputs of every command used in the video: [`captures/`](captures/).

## Install from zero (Windows)

```powershell
winget install ggml.llamacpp          # llama.cpp (llama-server)
winget install astral-sh.uv           # Python package manager
llama-server --list-devices           # your GPU must be listed

git clone https://github.com/infrablueprint-ops/blueprints.git
cd blueprints/14-onejev-invoice-triage
uv sync                               # .venv + qev (OneJev server and client), pinned commit
uv run python download_direct.py      # 3.2 GB weights + 0.7 GB vision projector + tokenizer, SHA-256 checked
```

Start the server (keep this terminal open):

```powershell
$env:LLAMA_ARG_FLASH_ATTN = "off"     # AMD / Vulkan only, see "Tuning"
uv run qev serve --gguf models/OmniJev_OneJev-4B-Q4_K_M.gguf `
  --mmproj models/mmproj-OmniJev_OneJev-4B-f16.gguf `
  --tokenizer models/OneJev-4B-tokenizer --host 127.0.0.1 --port 8000
```

Triage invoices (second terminal):

```powershell
uv run python invoice_triage.py samples/invoices/12_stratus_overdue_reminder.pdf --dpi 72
uv run python invoice_triage.py "samples/invoices/*.pdf" "samples/invoices/*.jpg" --labels samples/invoices/labels.json --dpi 72
uv run python invoice_triage.py my_scan.jpg --config my_categories.json
```

- Always pass `--mmproj`: without it, qev takes the first `*mmproj*f16*` file next to the model.
- Keep `--host 127.0.0.1`: the qev default is `0.0.0.0`, and the API has no authentication.
- Smaller GPU: `uv run python download_direct.py --size 0.8B` (0.7 GB + 0.2 GB). Also `9B` and `27B`.

## Customise

Every question, option and description lives in `invoice_categories.json`. The descriptions **are** the
decision boundaries: write them like notes for a new accountant. Business rules go in plain English in
`instructions` (e.g. *"Book a refund or credit note under the category of the original purchase."*).
`samples/invoice_categories_tuned.json` is the tuned version used in the video.
Question types: `choice` (up to 255 options), `noul` (yes/no probability), `score` (up to 10 levels).

## Results on 16 fictional documents

`samples/invoices/` holds 16 invented supplier documents (typed invoices, receipts, a quote, a credit note,
an overdue reminder, a hand-filled invoice, a blurred phone photo) and their expected answers in `labels.json`.
`uv run python make_samples.py` rebuilds them. Flash attention off, RX 6950 XT:

| | 72 DPI | 100 DPI | 72 DPI, tuned descriptions |
|---|:---:|:---:|:---:|
| Decisions right (of 78 scored) | 77 | 77 | 78 |
| Mean time per document, 6 questions | 14.0 s | 20.1 s | 12.7 s |

Each run has one miss, and both came with low confidence (60% and 51%): send everything below ~70% to a
human (some correct answers go to review too). The 72 DPI miss is the VAT question on the overdue reminder;
the tuned description fixes it. Raw outputs are in `captures/`. The tuned descriptions were written after looking at these same 16 documents, so 78/78 is a best
case: measure on your own documents.

## Tuning (AMD / Vulkan) and honest limits

- **Flash attention off.** `llama-bench`, 3,072-token prompt: 1,485 tokens/s with flash attention, 2,402 without
  (`captures/c13`). On the server, a 3,045-token text prompt went from 244 to ~1,900 tokens/s.
- **Keep pages near 1 megapixel (72-100 DPI).** A 150 DPI A4 page is 2,176 image tokens. With flash attention
  off, one invoice took 12 s at 72 DPI, 17 s at 100 DPI and 247 s at 150 DPI (`captures/c11`). Without
  flash attention, llama.cpp warns that the vision encoder graph uses unsupported operators
  (`captures/c14`).
- **One pass per question on llama.cpp.** qev's PyTorch backend shares the image prefix across questions;
  its llama.cpp backend sends one prompt per question, so each question re-encodes the image.
  Ask only the questions you need.
- **It decides, it does not extract.** No invoice number, no exact total: amounts come in bands. Pair it
  with an OCR model when you need values.
- Not tested here: NVIDIA GPUs, the PyTorch backend, the 0.8B, 9B and 27B models.

Every company, person, address and identifier in `samples/` is invented.
