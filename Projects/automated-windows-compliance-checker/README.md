# 🛡️ Automated Windows Compliance Checker

This is a simple Python-based tool to help assess basic Windows system settings against common cybersecurity baselines like **NIST 800-171** and **CIS Benchmarks**.

# 📘 Compliance References
| Control Area         | Framework           |
| -------------------- | ------------------- |
| Password Policy      | NIST 800-171 3.5.8  |
| RDP Access           | NIST 800-171 3.1.13 |
| Malware Protection   | NIST 800-171 3.14.1 |
| System Configuration | NIST 800-171 3.4.1  |
| Firewall Enforcement | CIS 9.1, 9.2        |



## ✅ Checks Performed

- ✔ Minimum password length (>=12)
- ✔ Password complexity enabled
- ✔ Remote Desktop (RDP) status
- ✔ Windows Firewall status
- ✔ Windows Defender running

🔍 Note: If password complexity is not set in the local registry, but appears as enabled in the GUI, it may be enforced by domain or Microsoft account policy.
## 🛠 Requirements

- Python 3.x
- Windows OS
- Must run from an Administrator Command Prompt


## 🚀 How to Use

From the root of your Portfolio repo (or wherever this is cloned):

```bash
python projects/automated-windows-compliance-checker/run_checker.py
```

Output reports are saved locally in the 'results/' folder and are not tracked in version control.
