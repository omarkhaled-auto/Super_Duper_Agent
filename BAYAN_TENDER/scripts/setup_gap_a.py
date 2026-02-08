"""
Setup script for Gap A - Upload Excel to MinIO and set OriginalFilePath on bid.
This solves the blocker where ParseBidFileCommandHandler requires bid.OriginalFilePath to be set.
"""
import requests
import json
import subprocess
import sys
import os

API_BASE = "http://localhost:5000/api"
DOCKER = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"

def login(email, password="Bayan@2024"):
    resp = requests.post(f"{API_BASE}/auth/login", json={"email": email, "password": password})
    d = resp.json()
    if d.get("success"):
        return d["data"]["accessToken"]
    raise Exception(f"Login failed for {email}: {d.get('message')}")

def api_get(endpoint, token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE}{endpoint}", headers=headers)
    data = resp.json()
    # API wraps responses in {success, data, message} envelope
    if isinstance(data, dict) and "data" in data and data.get("success"):
        return data["data"]
    return data

def main():
    print("=== Gap A Setup: Upload Excel to MinIO + Set OriginalFilePath ===\n")

    # 1. Login as tender manager
    token = login("tendermgr@bayan.ae")
    print("[OK] Logged in as tendermgr@bayan.ae")

    # 2. Get TNR-2026-0003 tender ID
    tenders = api_get("/tenders", token)
    items = tenders.get("items", tenders if isinstance(tenders, list) else [])

    tender_id = None
    for t in items:
        ref = t.get("reference", "")
        print(f"  Tender: {ref} | ID: {t['id']} | Status: {t.get('status')}")
        if ref == "TNR-2026-0003":
            tender_id = t["id"]

    if not tender_id:
        print("ERROR: TNR-2026-0003 not found!")
        sys.exit(1)

    print(f"\n[OK] TNR-2026-0003 ID: {tender_id}")

    # 3. Get bids
    bids_data = api_get(f"/tenders/{tender_id}/bids", token)
    bid_items = bids_data.get("items", bids_data if isinstance(bids_data, list) else [])

    if not bid_items:
        print("ERROR: No bids found!")
        sys.exit(1)

    bid = bid_items[0]  # Use first bid
    bid_id = bid["id"]
    bidder_id = bid.get("bidderId", bid.get("bidder", {}).get("id", "unknown"))
    bidder_name = bid.get("bidderName", bid.get("bidder", {}).get("companyName", "unknown"))
    orig_file = bid.get("originalFilePath", "NOT SET")

    print(f"\n[OK] Using Bid: {bid_id}")
    print(f"  Bidder: {bidder_name} (ID: {bidder_id})")
    print(f"  Current OriginalFilePath: {orig_file}")
    print(f"  ImportStatus: {bid.get('importStatus', 'unknown')}")

    # 4. Upload Excel file to MinIO
    excel_path = os.path.join(os.path.dirname(__file__), "..", "test-bid-files", "priced-boq-wizard-test.xlsx")
    excel_path = os.path.abspath(excel_path)

    if not os.path.exists(excel_path):
        print(f"ERROR: Excel file not found at {excel_path}")
        sys.exit(1)

    file_size = os.path.getsize(excel_path)
    print(f"\n[OK] Excel file: {excel_path} ({file_size} bytes)")

    # MinIO storage path format from UploadBidFileCommandHandler:
    # bid-submissions/{tenderId}/{bidderId}/priced_boq/{filename}
    minio_path = f"bid-submissions/{tender_id}/{bidder_id}/priced_boq/priced-boq-wizard-test.xlsx"
    print(f"  MinIO path: {minio_path}")

    # First, copy the file into the Docker container
    print("\n[STEP] Copying Excel file into MinIO container...")
    result = subprocess.run(
        [DOCKER, "cp", excel_path, "bayan-minio:/tmp/priced-boq-wizard-test.xlsx"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERROR: Docker cp failed: {result.stderr}")
        sys.exit(1)
    print("  [OK] File copied to container")

    # Use mc (MinIO Client) inside the container to upload
    print("\n[STEP] Uploading file to MinIO bucket...")

    # Configure mc alias
    mc_cmds = [
        f"mc alias set local http://localhost:9000 minioadmin minioadmin",
        f"mc cp /tmp/priced-boq-wizard-test.xlsx local/bayan-documents/{minio_path}"
    ]

    for cmd in mc_cmds:
        result = subprocess.run(
            [DOCKER, "exec", "bayan-minio", "sh", "-c", cmd],
            capture_output=True, text=True
        )
        print(f"  > {cmd[:80]}...")
        if result.stdout:
            print(f"    stdout: {result.stdout[:200]}")
        if result.returncode != 0 and result.stderr:
            print(f"    stderr: {result.stderr[:200]}")

    # Verify file exists in MinIO
    result = subprocess.run(
        [DOCKER, "exec", "bayan-minio", "sh", "-c",
         f"mc ls local/bayan-documents/{minio_path}"],
        capture_output=True, text=True
    )
    print(f"\n  MinIO ls result: {result.stdout.strip()}")

    if "priced-boq-wizard-test.xlsx" not in result.stdout:
        print("WARNING: File may not have been uploaded correctly")
    else:
        print("  [OK] File verified in MinIO!")

    # 5. Update bid.OriginalFilePath in PostgreSQL
    print(f"\n[STEP] Updating bid OriginalFilePath in database...")

    db_cmd = f"""UPDATE bayan.bid_submissions
SET original_file_path = '{minio_path}',
    import_status = 0
WHERE id = '{bid_id}';"""

    result = subprocess.run(
        [DOCKER, "exec", "bayan-db", "psql", "-U", "bayan_user", "-d", "bayan", "-c", db_cmd],
        capture_output=True, text=True
    )
    print(f"  DB result: {result.stdout.strip()}")
    if result.returncode != 0:
        print(f"  DB error: {result.stderr}")
    else:
        print("  [OK] OriginalFilePath updated!")

    # 6. Verify the update
    verify_cmd = f"SELECT id, original_file_path, import_status FROM bayan.bid_submissions WHERE id = '{bid_id}';"
    result = subprocess.run(
        [DOCKER, "exec", "bayan-db", "psql", "-U", "bayan_user", "-d", "bayan", "-c", verify_cmd],
        capture_output=True, text=True
    )
    print(f"\n  Verification:\n{result.stdout}")

    # 7. Test the parse endpoint
    print("\n[STEP] Testing parse endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    parse_resp = requests.post(
        f"{API_BASE}/tenders/{tender_id}/bids/{bid_id}/import/parse",
        headers=headers,
        json={"previewRowCount": 20}
    )
    print(f"  Status: {parse_resp.status_code}")
    parse_data = parse_resp.json()
    if parse_resp.status_code == 200:
        if parse_data.get("success"):
            data = parse_data.get("data", {})
            print(f"  [OK] Parse successful!")
            print(f"  Columns: {data.get('detectedColumns', [])}")
            print(f"  Total rows: {data.get('totalRows', 'N/A')}")
            print(f"  Preview rows: {len(data.get('previewData', []))}")
        else:
            print(f"  Parse response: {json.dumps(parse_data, indent=2)[:500]}")
    else:
        print(f"  Parse error: {json.dumps(parse_data, indent=2)[:500]}")

    print("\n=== Setup Complete ===")

if __name__ == "__main__":
    main()
