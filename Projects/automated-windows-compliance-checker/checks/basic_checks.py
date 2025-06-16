import subprocess

def check_password_policy():
    try:
        output = subprocess.check_output("net accounts", shell=True, text=True)
        lines = output.splitlines()
        min_len = None
        complexity = "Unknown"
        for line in lines:
            if "Minimum password length" in line:
                min_len = int(line.split(":")[1].strip())
            elif "Password complexity" in line:
                complexity = line.split(":")[1].strip()
        return [
            f"✔ Minimum password length: {min_len}" if min_len and min_len >= 12 else f"✘ Minimum password length too short: {min_len}",
            f"✔ Password complexity: Enabled" if complexity.lower() == "enabled" else "✘ Password complexity: Disabled"
        ]
    except Exception as e:
        return [f"✘ Error checking password policy: {e}"]

def check_rdp_status():
    try:
        output = subprocess.check_output('reg query "HKLM\\System\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections', shell=True, text=True)
        if "0x0" in output:
            return "✘ Remote Desktop: Enabled"
        else:
            return "✔ Remote Desktop: Disabled"
    except Exception as e:
        return f"✘ Error checking RDP status: {e}"

def check_firewall_status():
    try:
        output = subprocess.check_output("netsh advfirewall show allprofiles", shell=True, text=True)
        if "State ON" in output.upper():
            return "✔ Windows Firewall: Enabled"
        else:
            return "✘ Windows Firewall: Disabled"
    except Exception as e:
        return f"✘ Error checking firewall: {e}"

def check_windows_defender():
    try:
        output = subprocess.check_output('sc query Windefend', shell=True, text=True)
        if "RUNNING" in output:
            return "✔ Windows Defender: Running"
        else:
            return "✘ Windows Defender: Not Running"
    except Exception as e:
        return f"✘ Error checking Defender: {e}"

def run_all_checks():
    results = []
    results.extend(check_password_policy())
    results.append(check_rdp_status())
    results.append(check_firewall_status())
    results.append(check_windows_defender())
    return results

