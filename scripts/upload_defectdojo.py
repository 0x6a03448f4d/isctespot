import os
from defectdojo_api import DefectDojoAPI

dojo = DefectDojoAPIv2(
    url=os.environ["DEFECTDOJO_URL"],
    api_key=os.environ["DEFECTDOJO_API_KEY"],
    verify_ssl=False
)

ENGAGEMENT_ID = int(os.environ["DEFECTDOJO_ENGAGEMENT_ID"])

def upload(scan_type, file_path):
    dojo.import_scan(
        engagement_id=ENGAGEMENT_ID,
        scan_type=scan_type,
        file_path=file_path,
        active=True,
        verified=False
    )
upload("Trivy Dependencies", "trivy-dependencies.json")
upload("Trivy Scan", "trivy-backend.json")
upload("Trivy Scan", "trivy-frontend.json")
upload("Dependency Check Scan", "dependency-check.json")
upload("CycloneDX Scan", "sbom.json")
