# Enterprise 101 Homelab on Proxmox VE  
_Re‑implementing Project Security’s “From Initial Access to Breached” lab_

> **Course reference:** <https://docs.projectsecurity.io/e101/overview/>  
> **Original hypervisors:** VirtualBox / VMware  
> **This build:** Proxmox VE 8.x on bare‑metal (Intel i7, 64 GB RAM)

---

## 1  Overview

Project Security’s **Enterprise 101 (E101)** course walks through standing up a mini‑enterprise, hardening it, then breaching it to practice blue‑team and red‑team skills.  
This repo documents a complete **Proxmox VE** adaptation.  All steps match the original guide—just substitute each “VirtualBox/VMware” action with its Proxmox equivalent.

---

## 2  Lab Topology

| Hostname (prefix `project-x-`) | OS / Role                              | vCPU | RAM | Disk | IP            |
|--------------------------------|----------------------------------------|------|-----|------|---------------|
| `dc` (`corp.project-x-dc.com`) | **Windows Server 2025** – AD/DNS/DHCP  | 2    | 4 GB| 50 GB| 10.0.0.5      |
| `win-client`                   | **Windows 10 Enterprise** – workstation| 2    | 4 GB| 80 GB| 10.0.0.100    |
| `linux-client`                 | **Ubuntu 22.04 Desktop** – dev box     | 1    | 2 GB| 80 GB| 10.0.0.101    |
| `sec-box`                      | **Ubuntu 22.04** – Wazuh manager GUI   | 2    | 4 GB| 80 GB| 10.0.0.10     |
| `sec-work`                     | **Security Onion** – analyst console   | 2    | 4 GB|100 GB| 10.0.0.103    |
| `corp-svr`                     | **Ubuntu 22.04 Server** – MailHog      | 1    | 4 GB| 80 GB| 10.0.0.8      |
| `attacker`                     | **Kali Linux 2024.4**                  | 2    | 4 GB| 55 GB| DHCP (dynamic)|

---

## 3  Why Proxmox?

* **Type‑1 performance** – KVM/QEMU sits on the host kernel.  
* **Snapshots & backups** – ZFS thin‑clones, scheduled `vzdump`.  
* **Built‑in NAT** – A single `vmbr1` bridge with masquerade rules replaces the desktop‑hypervisor NAT network.  
* **Automation** – REST API, Terraform, and Ansible support.  
* **Free & on‑prem** – No per‑VM licensing headaches.

---

## 🧠 Lessons Learned

- **ARM-based Macs have compatibility limitations**  
  Tools like Windows Server and Security Onion don't support ARM natively, making them unsuitable for full-stack x86-based cybersecurity labs.

- **Old hardware still has value**  
  Repurposing an older laptop (e.g., a ThinkPad T450) as a bare-metal Proxmox server is an effective workaround for running x86 VMs.

- **Proxmox enables flexible network segmentation**  
  By configuring virtual bridges (e.g., `vmbr0`, `vmbr1`, `vmbr2`), you can separate lab environments, isolate honeypots, and manage internal vs. external access cleanly.

- **Windows 10 supports SSH between local users**  
  With the OpenSSH Server enabled and proper firewall settings, you can SSH into a separate user account or even simulate a client-server interaction locally.

- **Consumer-grade routers (e.g., Verizon Fios) limit segmentation**  
  Native VLAN or firewall isolation isn't feasible on most ISP-provided hardware, so adding a secondary router or VLAN-capable switch is often necessary for true lab isolation.

- **You can isolate traffic while maintaining selective internet access**  
  Using Proxmox’s networking options and careful VM gateway/DNS configuration, you can allow or block internet traffic per VM — ideal for safely running honeypots or simulated attacks.

* **Avoid pointing MASQUERADE to a physical iface**; always use the bridge device (vmbr0)
* tcpdump is extremely useful to isolate where packets drop
* iptables -t nat -L -n -v and ip route give the clearest picture for NAT and routing flow
* Clock/time issues were unrelated, but caused confusion during diagnosis

Lessons Learned – Wazuh ⚙️ Docker Setup
- **Docker Engine + Compose v2** are required.  
  - Modern syntax is `docker compose …`; legacy `docker-compose` needs the separate binary.
- Ensure `vm.max_map_count=262144` on the host *before* launching the stack:
  ```bash
  sudo sysctl -w vm.max_map_count=262144
  echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
