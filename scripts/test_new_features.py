import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from bgv_app.main import app


def run_tests():
    client = TestClient(app)
    
    # 1. Health check
    r = client.get("/")
    print("Health:", r.status_code, r.json())
    assert r.status_code == 200

    # 2. List cases
    r = client.get("/agentic-bgv/cases")
    print("Cases count:", len(r.json()))
    assert r.status_code == 200
    cases = r.json()
    assert len(cases) > 0

    first_case = cases[0]
    cid = first_case["id"]
    print("Case 1 candidate:", first_case["candidate"]["name"])
    print("Case 1 components count:", len(first_case.get("components", [])))
    print("Case 1 integrity score:", first_case.get("integrity_score"))

    # 3. Report JSON
    r = client.get(f"/agentic-bgv/cases/{cid}/report")
    assert r.status_code == 200
    report_data = r.json()
    print("Report ID:", report_data["report_id"])
    print("Integrity score in report:", report_data["integrity_score"])

    # 4. Report HTML
    r = client.get(f"/agentic-bgv/cases/{cid}/report/html")
    assert r.status_code == 200
    print("Report HTML status:", r.status_code, "Length:", len(r.text))
    assert "Background Verification Audit Dossier" in r.text

    # 5. Component preview
    r = client.get("/analysis/preview-components")
    assert r.status_code == 200
    print("Preview integrity:", r.json()["integrity_score"], r.json()["risk_level"])

    print("\nSUCCESS: All new feature endpoints tested and verified!")

if __name__ == "__main__":
    run_tests()
