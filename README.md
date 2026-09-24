# 🏗️ InfraBlueprint Ops — Official Production Blueprints

<div align="center">

[![YouTube Channel](https://img.shields.io/badge/YouTube-@infrablueprint--ops-red?style=for-the-badge&logo=youtube)](https://www.youtube.com/@infrablueprint-ops)
[![Resolution](https://img.shields.io/badge/Resolution-4K%20UHD%20(3840x2160)-blue?style=for-the-badge)](https://www.youtube.com/@infrablueprint-ops)
[![License](https://img.shields.io/badge/License-MIT-emerald?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Code-Production%20Hardened-green?style=for-the-badge)]()

**Industrial infrastructure code, hardened Docker Compose stacks, automation playbooks, and research benchmarks from the [InfraBlueprint Ops](https://www.youtube.com/@infrablueprint-ops) masterclasses.**

[📺 Watch on YouTube](https://www.youtube.com/@infrablueprint-ops) • [🎬 Video Walkthroughs](#-featured-video-walkthroughs) • [📋 Blueprints Index](#-blueprints-index) • [⚡ Quickstart](#-quickstart)

</div>

---

## 🎬 Featured Video Walkthroughs

Click any preview below to watch the complete 4K step-by-step masterclass with full architecture diagrams and real-time terminal telemetry:

| ⚙️ 01. Hardened Ansible in Production | 🐙 02. Crawl4AI High-Throughput Crawler |
| :---: | :---: |
| [![Ansible Masterclass](https://img.youtube.com/vi/RrKONBKSbRM/hqdefault.jpg)](https://youtu.be/RrKONBKSbRM)<br>▶️ **[Watch 4K Masterclass](https://youtu.be/RrKONBKSbRM)** | [![Crawl4AI Spotlight](https://img.youtube.com/vi/bf8qtNK4KUU/hqdefault.jpg)](https://youtu.be/bf8qtNK4KUU)<br>▶️ **[Watch 4K Spotlight](https://youtu.be/bf8qtNK4KUU)** |

| 🦀 03. Sovereign Vaultwarden in Rust | ⚛️ 04. Autonomous SRE & eBPF Benchmark |
| :---: | :---: |
| [![Vaultwarden Spotlight](https://img.youtube.com/vi/dVSgt6lcXlw/hqdefault.jpg)](https://youtu.be/dVSgt6lcXlw)<br>▶️ **[Watch 4K Spotlight](https://youtu.be/dVSgt6lcXlw)** | [![Autonomous SRE Brief](https://img.youtube.com/vi/yNRBWfI_qRw/hqdefault.jpg)](https://youtu.be/yNRBWfI_qRw)<br>▶️ **[Watch 4K Brief](https://youtu.be/yNRBWfI_qRw)** |

| 🏗️ 05. Production Terraform Foundations | 🧠 06. JEV — Typed AI Decisions |
| :---: | :---: |
| [![Terraform Masterclass](https://img.youtube.com/vi/s9Piakl4s-g/hqdefault.jpg)](https://youtu.be/s9Piakl4s-g)<br>▶️ **[Watch 4K Masterclass](https://youtu.be/s9Piakl4s-g)** | [![JEV Brief](https://img.youtube.com/vi/P1FfigH033Q/hqdefault.jpg)](https://youtu.be/P1FfigH033Q)<br>▶️ **[Watch 4K Blueprint](https://youtu.be/P1FfigH033Q)** |

---

## 🧭 Philosophy & DNA

Every blueprint in this repository follows strict industrial engineering standards:
1. **Zero Toy Examples** : No hello-world setups. Everything is pre-configured with memory limits, least-privilege security, healthchecks, and proper volume persistence.
2. **Reproducible in 1 Command** : Clone, configure `.env`, and launch with `docker compose up -d` or `ansible-playbook`.
3. **1:1 Alignment with Masterclasses** : Every directory corresponds exactly to an episode of our YouTube channel, complete with architecture diagrams and timecoded explanations.

---

## 📋 Blueprints Index

| Blueprint | Category | Description | Video Masterclass | Status |
| :--- | :---: | :--- | :---: | :---: |
| [`01-ansible-production`](./01-ansible-production) | ⚙️ Ops Core | Hardened Ansible inventory, SSH hardening, and idempotent production playbooks | [📺 Watch (10:00)](https://youtu.be/RrKONBKSbRM) | ✅ Live |
| [`02-crawl4ai-pipeline`](./02-crawl4ai-pipeline) | 🐙 AI Ops | High-throughput asynchronous LLM web crawler with markdown extraction | [📺 Watch (08:58)](https://youtu.be/bf8qtNK4KUU) | 🗓️ 13 Sept (15h) |
| [`03-vaultwarden-sovereign`](./03-vaultwarden-sovereign) | 🦀 Security | Sovereign zero-cloud password manager with SQLite WAL, Argon2id & Caddy HTTPS | [📺 Watch (09:05)](https://youtu.be/dVSgt6lcXlw) | 🗓️ 20 Sept (15h) |
| [`04-autonomous-sre-ebpf`](./04-autonomous-sre-ebpf) | ⚛️ arXiv Research | SREGym triage benchmark, live eBPF kernel probes & anti-sabotage guardrails | [📺 Watch (08:54)](https://youtu.be/yNRBWfI_qRw) | 🗓️ 15 Sept (18h) |
| [`13-rustfs-disk-failure-lab`](./13-rustfs-disk-failure-lab) | 🦀 Storage | RustFS 1.0.0 disk-failure lab: 4 drives, wipe 2 then 3, self-heal timing, throughput bench, raw captures | [📺 Watch (08:52)](https://youtu.be/K7dxVI5F__Q) | 🗓️ 8 Nov (15h) |

---

## ⚡ Quickstart

Clone the entire repository:

```bash
git clone https://github.com/infrablueprint-ops/blueprints.git
cd blueprints
```

Navigate to any blueprint directory and follow its dedicated `README.md`:

```bash
# Example: Deploy Sovereign Vaultwarden
cd 03-vaultwarden-sovereign
cp .env.example .env
docker compose up -d
```

---

## 📜 License

All code in this repository is licensed under the [MIT License](LICENSE).  
Content and architecture designs © 2026 **InfraBlueprint Ops**.
