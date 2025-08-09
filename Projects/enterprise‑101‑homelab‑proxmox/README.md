# Enterprise 101 Homelab on Proxmox VE  (IN PROGRESS 7/22/25)
_Re‑implementing Project Security’s “From Initial Access to Breached” lab_

# Enterprise 101 (Project Security) — Proxmox Edition

A step-by-step build of the **Project Security: Enterprise 101 – From Initial Access to Breached** homelab using **Proxmox VE** instead of VirtualBox/VMware. You’ll stand up a small enterprise network (AD domain, Windows & Linux clients, “security” hosts, and an attacker box), make it intentionally vulnerable, then simulate an attack and observe/defend.

> Original course & docs credit: ProjectSecurity.io. I followed their host plan, accounts, and sequence; this README just translates it to a Proxmox workflow.


## Table of Contents

- [What You’ll Build](#what-youll-build)
- [Host Plan & IPs](#host-plan--ips)
- [Prereqs & Downloads](#prereqs--downloads)
- [Proxmox Networking (Lab NAT on `vmbr1`)](#proxmox-networking-lab-nat-on-vmbr1)
- [Upload ISOs to Proxmox](#upload-isos-to-proxmox)
- [Create the VMs (Specs)](#create-the-vms-specs)
- [OS-Specific Setup](#os-specific-setup)
  - [1) AD Domain Controller (Windows Server 2025)](#1-ad-domain-controller-windows-server-2025)
  - [2) Windows 11 Enterprise Client](#2-windows-11-enterprise-client)
  - [3) Ubuntu Desktop (Linux Client)](#3-ubuntu-desktop-linux-client)
  - [4) Corporate Server (Ubuntu Server) + MailHog](#4-corporate-server-ubuntu-server--mailhog)
  - [5) Security Workstation & Security Server](#5-security-workstation--security-server)
  - [6) Attacker (Kali)](#6-attacker-kali)
- [Make It Intentionally Vulnerable](#make-it-intentionally-vulnerable)
- [Optional: Add Wazuh SIEM](#optional-add-wazuh-siem)
- [Cyber Attack Simulation](#cyber-attack-simulation)
- [Snapshots & Tips](#snapshots--tips)
- [Troubleshooting Notes (Proxmox)](#troubleshooting-notes-proxmox)
- [Attribution](#attribution)


## What You’ll Build

A contained NAT’d lab on **10.0.0.0/24** with an AD domain (`corp.project-x-dc.com`), one Windows client, a Linux desktop client, “security” hosts, a small “corporate” Ubuntu server (for lab services like MailHog), and a Kali attacker VM. The flow and exercises mirror the Enterprise 101 docs.



## Host Plan & IPs

<img width="2431" height="1496" alt="image" src="https://github.com/user-attachments/assets/e19606c3-7834-426d-86e2-7478d90d6b05" />


**Network:** `10.0.0.0/24` (NAT)  
**Gateway (lab bridge):** `10.0.0.1`

| Hostname suffix (prefix is `project-x-`) | Example FQDN / Name            | IP          | Role |
|---|---|---|---|
| `-dc` | `corp.project-x-dc.com` (domain) | `10.0.0.5` | Domain Controller (AD DS), DNS, DHCP |
| `-win-client` | Windows 11 workstation | `10.0.0.100` (or DHCP) | User workstation |
| `-linux-client` | Ubuntu Desktop | `10.0.0.101` (or DHCP) | Linux workstation |
| `-admin` | `corp-svr` | `10.0.0.8` | Corporate server (Ubuntu) |
| `-sec-box` | `sec-box` | `10.0.0.10` | Security server |
| `-sec-work` | `sec-work` | `10.0.0.103` (or DHCP) | Security playground |
| `attacker` | Kali | DHCP | Attacker box |

> These hostnames, IPs, and the domain name come straight from the Enterprise 101 overview. 

**Default accounts (lab):**  
- `Administrator` on the DC → `@Deeboodah1!`  
- Windows client user `[email protected]` → `@password123!`  
- Linux client user `janed` → `@password123!`  
- Various “sec-*” and “project-x-admin” accounts → `@password123!`  
- Attacker box: `attacker/attacker` (for the demo VM)  
See the docs’ **Accounts & Passwords** table for the full list. 

---

## Prereqs & Downloads

- **Proxmox VE** host with enough CPU/RAM/disk (8C/32GB is comfy; you can scale down).
- **ISOs** (exact versions used in the course are linked in the docs; Windows evals are fine):
  - Windows Server **2025** (or 2022 if your hardware balks at requirements)  
  - Windows 11 Enterprise (or Windows 10 as a fallback)  
  - Ubuntu **22.04** Desktop & Server  
  - Security Onion (used later in other sections; optional for E101)  
  - Kali Linux  
  Download links are listed in the Overview. The doc also offers a Sync.com bundle with the specific versions used. 

---

## Proxmox Networking (Lab NAT on `vmbr1`)

We’ll keep your homelab **isolated** on an internal Proxmox bridge (`vmbr1`) at `10.0.0.1/24`, and NAT traffic out to your WAN bridge (`vmbr0`). On the Proxmox host:

1) **Create an isolated bridge** for the lab:
```bash
# /etc/network/interfaces (add this stanza)
auto vmbr1
iface vmbr1 inet static
    address 10.0.0.1/24
    bridge-ports none
    bridge-stp off
    bridge-fd 0
````

Apply via `ifreload -a` (Proxmox uses ifupdown2) or reboot during a change window.

2. **Enable IP forwarding**:

```bash
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p
```

3. **Add a NAT rule** so lab VMs can reach the internet via `vmbr0`:

```bash
# temporary (until reboot)
iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o vmbr0 -j MASQUERADE

# install persistence if desired
apt-get update && apt-get install -y iptables-persistent
netfilter-persistent save
```

> If your WAN side isn’t `vmbr0`, swap the interface name accordingly. **All lab NICs will attach to `vmbr1`.** DHCP will come from your **AD DC** (set up below), not from Proxmox.

---

## Upload ISOs to Proxmox

In the Proxmox UI: **Datacenter → your node → local (or a storage) → ISO Images → Upload**. Add the Windows, Ubuntu, Kali, and Security Onion ISOs

---

## Create the VMs (Specs)

Create each VM with these **minimum specs** (from the docs). Disk bus choices below aim to minimize driver pain during Windows setup.

| VM Name                  | OS                    |     CPU / RAM | Disk (min) | Notes                                                                      |
| ------------------------ | --------------------- | ------------: | ---------: | -------------------------------------------------------------------------- |
| `project-x-dc`           | Windows Server 2025   | 2 vCPU / 4 GB |      50 GB | Use **SATA** disk for easy install; NIC `E1000e` initially                 |
| `project-x-win-client`   | Windows 11 Enterprise |      2 / 4 GB |      80 GB | Same tip: SATA + E1000e for install, switch to VirtIO later                |
| `project-x-linux-client` | Ubuntu 22.04 Desktop  |      1 / 2 GB |      80 GB | Disk SCSI (VirtIO SCSI), NIC VirtIO                                        |
| `project-x-sec-work`     | Security Onion        |      1 / 2 GB |      55 GB | Optional in E101; used more in later series ([docs.projectsecurity.io][2]) |
| `project-x-sec-box`      | Ubuntu 22.04 Desktop  |      2 / 4 GB |      80 GB |                                                                            |
| `project-x-corp-svr`     | Ubuntu Server 22.04   |      1 / 2 GB |      25 GB | MailHog target later                                                       |
| `project-x-attacker`     | Kali Linux (2024.x)   |      1 / 2 GB |      55 GB |                                                                            |

> Specs are from the Enterprise 101 Overview’s VM table. Attach all NICs to **`vmbr1`**. 

**Proxmox create-VM quick recipe (GUI):**

* **General:** Name as above.
* **OS:** Pick the ISO.
* **System:** Machine `q35`, BIOS `OVMF (UEFI)` is fine; disable TPM if Windows ISO hassles you and you aren’t using pre-patched ISOs.
* **Disks:** Use **SATA** for Windows installs (to avoid VirtIO driver steps), **SCSI (VirtIO SCSI)** for Linux.
* **CPU/RAM:** As per table.
* **Network:** Bridge `vmbr1`. Model `E1000e` for Windows install; VirtIO for Linux. You can switch Windows NIC to VirtIO later after adding VirtIO drivers.

---

## OS-Specific Setup

### 1) AD Domain Controller (Windows Server 2025)

1. Install Windows Server (Desktop Experience). Set the **Administrator** password to `@Deeboodah1!` (per docs). ([docs.projectsecurity.io][3])
2. **Static IP:**

   * IP: `10.0.0.5`, Mask: `255.255.255.0`, GW: `10.0.0.1`. ([docs.projectsecurity.io][3])
3. **Add roles & promote to DC:** AD DS, DNS, DHCP, IIS/File Services. Promote as **new forest** with root domain **`corp.project-x-dc.com`** (yes, that exact string). Leave NetBIOS as `CORP`. Reboot. 
4. **DNS forwarder:** In DNS Manager, set forwarder to `8.8.8.8` so the domain can still resolve internet names. Test with `ping google.com` and `nslookup corp.project-x-dc.com`.
5. **DHCP scope:** Create IPv4 scope **`project-x-scope`**: `10.0.0.100`–`10.0.0.200`, mask `/24`, router **`10.0.0.1`**. Authorize DHCP. (We’ll often use static IPs per the docs, but DHCP is still handy.)

> The domain string and scope values above are exactly what the course uses. ([docs.projectsecurity.io][3])

---

### 2) Windows 11 Enterprise Client

1. Install Windows 11 Enterprise.
2. **Static IP (if not using DHCP):** IP `10.0.0.100`, Mask `/24`, GW `10.0.0.1`, **DNS `10.0.0.5`** (the DC). ([docs.projectsecurity.io][4])
3. **Join domain:** System → “Change workgroup name” → “Change” → **Member of: `corp.project-x-dc.com`**. Log in as `CORP\Administrator` with the `@Deeboodah1!` password when prompted. ([docs.projectsecurity.io][4])
4. Create or verify the user `[email protected]` with password `@password123!` (per docs) and test a domain login. ([docs.projectsecurity.io][1])
5. (Optional) Install VirtIO NIC/storage drivers and switch NIC model to VirtIO in Proxmox for better performance.

---

### 3) Ubuntu Desktop (Linux Client)

1. Install Ubuntu 22.04 Desktop with a local user (e.g., `janed / @password123!`). ([docs.projectsecurity.io][5])
2. Set **static IP** to `10.0.0.101`, GW `10.0.0.1`, and **DNS `10.0.0.5`**. Snap a Proxmox snapshot. ([docs.projectsecurity.io][5])
3. **Join to AD (Winbind path):** The docs outline both realmd/SSSD and Samba Winbind; for Server 2025, Winbind is the working route right now. Follow their steps (`smb.conf`, `nsswitch.conf`, `pam-auth-update`, `net ads join`, restart `winbind`, `wbinfo -u`). ([docs.projectsecurity.io][5])

---

### 4) Corporate Server (Ubuntu Server) + MailHog

1. Install **Ubuntu Server 22.04** (`project-x-corp-svr`) and set **static IP** `10.0.0.8`. Create user `project-x-admin / @password123!`. ([docs.projectsecurity.io][6])
2. **(Optional)** Join to AD or just keep local creds for simplicity.
3. **MailHog (fake SMTP / web UI):** follow the tool guide to install and run MailHog so you can safely capture lab emails (e.g., phishing tests) without sending externally. ([docs.projectsecurity.io][7])

---

### 5) Security Workstation & Security Server

* **`project-x-sec-work`**: lightweight “playground” workstation.
* **`project-x-sec-box`**: Ubuntu Desktop used for security tooling and log collection experiments.
  Provision per the Overview’s specs; you can keep these simple at first and add tools later. ([docs.projectsecurity.io][1])

> Security Onion is not required in **Enterprise 101**; it’s used in later series. If you’re curious, the doc calls that out explicitly. ([docs.projectsecurity.io][2])

---

### 6) Attacker (Kali)

Create a Kali VM on `vmbr1` (DHCP or static in the `10.0.0.0/24` range). This VM is for reconnaissance, phishing, password attacks, and post-exploitation tasks referenced throughout the docs. ([docs.projectsecurity.io][8])

---

## Make It Intentionally Vulnerable

The course includes a short guide where you loosen certain defaults to create realistic misconfigurations (e.g., weak policies, permissive services) that you’ll later exploit. Work through that checklist **after** the core hosts are online. ([docs.projectsecurity.io][9])

---

## Optional: Add Wazuh SIEM

If you want blue-team visibility:

* Deploy **Wazuh Indexer + Server**  and install **Wazuh agents** on the Windows client, DC, and Linux client. The tool guide covers groups and onboarding custom logs.

---

## Cyber Attack Simulation

Follow the doc’s end-to-end attack scenario to phish creds, gain initial access, move laterally, and grab sensitive files. This ties together the AD setup, workstation configs, and any monitoring you added. ([docs.projectsecurity.io][11])

---

## Snapshots & Tips

* **Snapshot** each VM after major milestones: post-OS install, post-domain join, post-vuln-config, etc.
* If Windows install nags about TPM/CPU: the docs explicitly allow **Windows 10** / **Server 2022** as substitutes. ([docs.projectsecurity.io][1])
* For Windows on Proxmox: start with **SATA disk + E1000e NIC** to avoid VirtIO driver steps during installation; switch to VirtIO later for performance.

---

## Troubleshooting Notes (Proxmox)

* **No internet from VMs:** Re-check `vmbr1` IP (`10.0.0.1/24`), `net.ipv4.ip_forward=1`, and the MASQUERADE rule pointing to your WAN bridge (`vmbr0`).
* **Clients can’t resolve names:** Ensure **Windows DC DNS** is set as clients’ primary DNS (`10.0.0.5`) and that the DC has a DNS forwarder (e.g., `8.8.8.8`). ([docs.projectsecurity.io][3])
* **Linux AD join fails (SSSD):** Use the **Winbind** method — the doc notes SSSD currently doesn’t work with Server 2025. ([docs.projectsecurity.io][5])

---

## Attribution

* Enterprise 101 Overview (topology, accounts, VM specs, sequence). ([docs.projectsecurity.io][1])
* Windows 11 client config & domain join example. ([docs.projectsecurity.io][4])
* AD Server (Server 2025) setup, domain name, DHCP scope, DNS forwarder. ([docs.projectsecurity.io][3])
* Ubuntu Desktop client setup and AD join (Winbind path). ([docs.projectsecurity.io][5])
* Security Onion note (not required in E101). ([docs.projectsecurity.io][2])
* Wazuh SIEM tool guide. ([docs.projectsecurity.io][10])

---

```


```

[1]: https://docs.projectsecurity.io/e101/overview/ "Overview - Project Security"
[2]: https://docs.projectsecurity.io/e101/setupsecurityonion/?utm_source=chatgpt.com "Provision & Setup Security Onion"
[3]: https://docs.projectsecurity.io/e101/buildingad/ "AD Server - Provision & Setup Windows Server 2025 - Project Security"
[4]: https://docs.projectsecurity.io/e101/setupwindows/?utm_source=chatgpt.com "Provision & Setup Windows 11 Enterprise"
[5]: https://docs.projectsecurity.io/e101/setupubuntudesktop/ "Provision & Setup Ubuntu Desktop 22.04 - Project Security"
[6]: https://docs.projectsecurity.io/e101/setupcorporateserver/?utm_source=chatgpt.com "Corporate Server - Provision & Setup Ubuntu Desktop 22.04"
[7]: https://docs.projectsecurity.io/e101/toolguide/setupmailhog/?utm_source=chatgpt.com "Email Server - MailHog"
[8]: https://docs.projectsecurity.io/e101/setupattacker/?utm_source=chatgpt.com "Setup The Attacker Machine"
[9]: https://docs.projectsecurity.io/e101/configurevulnenv/?utm_source=chatgpt.com "Configure a Vulnerable Environment - ProjectSecurity.io"
[10]: https://docs.projectsecurity.io/e101/toolguide/setupwazuh/ "SIEM - Setup Wazuh - Project Security"
[11]: https://docs.projectsecurity.io/e101/cyberattacksimulation/?utm_source=chatgpt.com "Cyber Attack Simulation"

