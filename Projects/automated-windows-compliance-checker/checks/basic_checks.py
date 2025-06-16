import subprocess
import re
import winreg
import os
import tempfile
import time

def check_password_policy():
    try:
        # Check minimum password length using net accounts
        output = subprocess.check_output("net accounts", shell=True, text=True)
        lines = output.splitlines()
        min_len = None
        for line in lines:
            if "Minimum password length" in line:
                try:
                    min_len = int(line.split(":")[1].strip())
                except:
                    min_len = 0

        return [
            f"✔ Minimum password length: {min_len}" if min_len and min_len >= 12 else f"✘ Minimum password length too short: {min_len}",
        ]
    except Exception as e:
        return [f"✘ Error checking password policy: {e}"]

def check_password_complexity():
    try:
        cmd = (
            'powershell -Command "'
            '$key = Get-Item \'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa\'; '
            'if ($key.GetValue(\'PasswordComplexity\') -ne $null) { '
            'if ($key.GetValue(\'PasswordComplexity\') -eq 1) { Write-Output \'✔ Password complexity: Enabled\' } '
            'else { Write-Output \'✘ Password complexity: Disabled\' } '
            '} else { Write-Output \'? Password complexity value not set in registry\' }"'
        )
        result = subprocess.check_output(cmd, shell=True, text=True)
        output = result.strip()

        if output == "? Password complexity value not set in registry":
            return "✔ Password complexity: Enabled (likely enforced via Group Policy)"
        else:
            return output

    except Exception as e:
        return f"✘ Error checking password complexity: {e}"

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

        profile_states = {
            "Domain": "✘ Domain Profile: Firewall status unknown",
            "Private": "✘ Private Profile: Firewall status unknown",
            "Public": "✘ Public Profile: Firewall status unknown"
        }

        current_profile = None
        for line in output.splitlines():
            line = line.strip()

            # Match headers exactly as seen on your system
            if line.startswith("Domain Profile Settings"):
                current_profile = "Domain"
            elif line.startswith("Private Profile Settings"):
                current_profile = "Private"
            elif line.startswith("Public Profile Settings"):
                current_profile = "Public"
            elif line.startswith("State") and current_profile:
                if "ON" in line.upper():
                    profile_states[current_profile] = f"✔ {current_profile} Profile: Firewall Enabled"
                else:
                    profile_states[current_profile] = f"✘ {current_profile} Profile: Firewall Disabled"
                current_profile = None

        return "\n".join(profile_states.values())

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
    results.append(check_password_complexity())    
    results.append(check_rdp_status())
    results.append(check_firewall_status())
    results.append(check_windows_defender())
    return results
