import os
import requests

# Read env variables
DOJO_URL = os.environ["DEFECTDOJO_URL"].rstrip("/")
API_KEY = os.environ["DEFECTDOJO_API_KEY"]
ENGAGEMENT_ID = os.environ["DEFECTDOJO_ENGAGEMENT_ID"]

# API endpoint for import
import_endpoint = f"{DOJO_URL}/api/v2/import-scan/"

# Common headers
headers = {
    "Authorization": f"Token {API_KEY}",
    "Accept": "application/json"
}

def upload_scan(file_path, scan_type, test_title=None):
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {
            "engagement": ENGAGEMENT_ID,
            "scan_type": scan_type,
            "minimum_severity": "Low",
            "active": "true",
            "verified": "false"
        }
        if test_title :
            data["test_title"] = test_title
        response = requests.post(import_endpoint, headers=headers, files=files, data=data, verify=False)
        print(file_path, response.status_code, response.text)

# Upload scans
upload_scan("trivy-dependencies.json", "Trivy", "Trivy FS Dependencies")
upload_scan("trivy-backend.json", "Trivy Scan", "Trivy Backend docker image")
upload_scan("trivy-frontend.json", "Trivy Scan", "Trivy Frontend docker image")
upload_scan("dependency-check.json", "Dependency Check Scan", "OWASP Dependency-Check")
upload_scan("sbom.json", "CycloneDX Scan", "SBOM Inventory")
