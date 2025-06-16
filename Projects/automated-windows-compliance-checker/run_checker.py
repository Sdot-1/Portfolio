from checks.basic_checks import run_all_checks
import os

# Ensure results directory exists
os.makedirs("projects/automated-windows-compliance-checker/results", exist_ok=True)

def main():
    report_path = "projects/automated-windows-compliance-checker/results/compliance_report.txt"
    results = run_all_checks()

    with open(report_path, "w") as report:
        for item in results:
            report.write(f"{item}\n")

    print(f"[+] Compliance check complete. Report saved to {report_path}")

if __name__ == "__main__":
    main()

