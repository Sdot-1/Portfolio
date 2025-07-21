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

%% ----------------------------------------------------
%% Enterprise‑101 lab topology (Proxmox edition)
%% ----------------------------------------------------
flowchart TD
    %% --- Theme colours (optional) -------------------
    classDef srv fill:#f4edff,stroke:#bb6fff,stroke-width:2px,color:#6b28b6;
    classDef node fill:#ffffff,stroke:#bb6fff,stroke-width:2px,color:#6b28b6;
    classDef label fill:#bb6fff,color:#ffffff,stroke:#bb6fff,stroke-width:0px;

    %% --- Core infrastructure ------------------------
    DIR[["<b>Directory<br/>Services&nbsp;Server</b>"]]:::srv
    HYP["<b>Hypervisor</b>"]:::label
    HYPcore[( )]:::srv  %% empty circle to centre links

    %% --- Security servers ---------------------------
    SEC_L[["<b>Security&nbsp;Server</b>"]]:::srv
    SEC_R[["<b>Security&nbsp;Server</b>"]]:::srv

    %% --- Peripheral services ------------------------
    EMAIL[["Email&nbsp;Server"]]:::node
    SIEM[["SIEM"]]:::node
    EDR[["EDR"]]:::node
    VULN[["VulnScan"]]:::node

    %% --- Workstations -------------------------------
    WS1[["Enterprise&nbsp;Workstation"]]:::node
    WS2[["Enterprise&nbsp;Workstation"]]:::node
    SWS[["Security&nbsp;Workstation"]]:::node

    %% === Connections ================================
    DIR --- HYPcore
    HYPcore --- HYP

    %% Left branch
    EMAIL --- SEC_L
    SEC_L --- HYPcore

    %% Right branch
    HYPcore --- SEC_R
    SEC_R --- SIEM
    SEC_R --- EDR
    SEC_R --- VULN

    %% Downward branch to VDI / user devices
    HYPcore --- WS1
    HYPcore --- WS2
    HYPcore --- SWS

    %% --- Styling tweaks to mimic the screenshot -----
    %% Square servers vs. rounded PCs
    class DIR,SEC_L,SEC_R srv;
    class EMAIL,SIEM,EDR,VULN,WS1,WS2,SWS node;



| Hostname (prefix `project-x-`) | OS / Role                              | vCPU | RAM | Disk | IP            |
|--------------------------------|----------------------------------------|------|-----|------|---------------|
| `dc` (`corp.project-x-dc.com`) | **Windows Server 2025** – AD/DNS/DHCP  | 2    | 4 GB| 50 GB| 10.0.0.5      |
| `win-client`                   | **Windows 11 Enterprise** – workstation| 2    | 4 GB| 80 GB| 10.0.0.100    |
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

## 4  Host Preparation

```bash
# Proxmox network file: /etc/network/interfaces
auto vmbr1
iface vmbr1 inet static
    address 10.0.0.1/24
    bridge_ports none
    bridge_stp off
    bridge_fd 0
    post-up   iptables -t nat -A POSTROUTING -s 10.0.0.0/24 ! -d 10.0.0.0/24 -j MASQUERADE
    post-down iptables -t nat -D POSTROUTING -s 10.0.0.0/24 ! -d 10.0.0.0/24 -j MASQUERADE
