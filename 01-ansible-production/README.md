# ⚙️ Blueprint 01: Production Ansible Hardening

Enterprise Ansible automation baseline for Linux production servers.

Accompanies the masterclass: **[Mastering Secure Ansible in Production (4K Masterclass)](https://youtu.be/RrKONBKSbRM)**.

---

## ⚡ Execution

```bash
ansible-playbook -i inventory.ini hardening.yml --check
ansible-playbook -i inventory.ini hardening.yml
```
