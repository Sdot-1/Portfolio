# 🛡️ Automated Windows Compliance Checker

This is a simple Python-based tool to help assess basic Windows system settings against common cybersecurity baselines like **NIST 800-171** and **CIS Benchmarks**.


## ✅ Checks Performed

- ✔ Minimum password length (>=12)
- ✔ Password complexity enabled
- ✔ Remote Desktop (RDP) status
- ✔ Windows Firewall status
- ✔ Windows Defender running


## 🛠 Requirements

- Python 3.x
- Windows OS
- Must run from an Administrator Command Prompt


## 🚀 How to Use

From the root of your Portfolio repo (or wherever this is cloned):

```bash
python projects/automated-windows-compliance-checker/run_checker.py

