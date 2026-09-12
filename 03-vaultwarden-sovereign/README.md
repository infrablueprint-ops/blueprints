# 🦀 Blueprint 03: Sovereign Vaultwarden Stack

Production-hardened deployment of **Vaultwarden** (lightweight Bitwarden-compatible server in Rust) with automatic HTTPS and defense-in-depth security.

Accompanies the masterclass: **[Vaultwarden: Sovereign Zero-Cloud Password Management in Rust (4K Blueprint)](https://youtu.be/xVttPj_b7nI)**.

---

## 🛡️ Architecture & Security Highlights

- **Ultra-lightweight Rust Core** : Under 50 MB idle memory (vs >3 GB for official MSSQL Bitwarden stack).
- **Hardened Argon2id KDF** : Key derivation parameters tuned against GPU dictionary attacks.
- **Automated TLS & Reverse Proxy** : Caddy 2 with HTTP/3, auto-renewing Let's Encrypt certificates, and HSTS security headers.
- **Resource Constraints** : Strict Docker cgroup limits (`512MB` max RAM, `1.0` CPU) to prevent memory leaks and host starvation.

---

## ⚡ Deployment in 3 Steps

1. **Configure Environment Variables** :
   ```bash
   cp .env.example .env
   # Edit DOMAIN and generate a strong ADMIN_TOKEN:
   # openssl rand -base64 48
   nano .env
   ```

2. **Launch Stack** :
   ```bash
   docker compose up -d
   ```

3. **Verify Health** :
   ```bash
   docker compose ps
   ```
