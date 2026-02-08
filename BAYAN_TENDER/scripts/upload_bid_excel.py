#!/usr/bin/env python3
"""Upload real Excel BOQ file as a bid document for TNR-2026-0003"""
import json
import urllib.request
import urllib.error
import os
import uuid
import http.client
import mimetypes

API_BASE = "http://localhost:5000"

def login(email, password):
    data = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(f"{API_BASE}/api/auth/login", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        return result["data"]["accessToken"]

def multipart_upload(token, url_path, file_path, fields=None):
    """Upload file using multipart form data"""
    boundary = f"----BoundaryString{uuid.uuid4().hex}"

    body_parts = []

    # Add regular fields
    if fields:
        for key, value in fields.items():
            body_parts.append(f'--{boundary}\r\n'.encode())
            body_parts.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
            body_parts.append(f'{value}\r\n'.encode())

    # Add file
    filename = os.path.basename(file_path)
    mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'

    with open(file_path, 'rb') as f:
        file_data = f.read()

    body_parts.append(f'--{boundary}\r\n'.encode())
    body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    body_parts.append(f'Content-Type: {mime_type}\r\n\r\n'.encode())
    body_parts.append(file_data)
    body_parts.append(b'\r\n')
    body_parts.append(f'--{boundary}--\r\n'.encode())

    body = b''.join(body_parts)

    # Use http.client for more control
    conn = http.client.HTTPConnection("localhost", 5000)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Content-Length': str(len(body))
    }

    conn.request("POST", url_path, body=body, headers=headers)
    response = conn.getresponse()
    result = response.read().decode()
    print(f"Status: {response.status}")
    print(f"Response: {result[:500]}")
    conn.close()
    return response.status, result

# Login as bidder (the one who submitted the bid)
print("Logging in as bidder@vendor.ae...")
bidder_token = login("bidder@vendor.ae", "Bayan@2024")
print("Logged in!")

# Also try as tender manager
print("\nLogging in as tendermgr@bayan.ae...")
tm_token = login("tendermgr@bayan.ae", "Bayan@2024")
print("Logged in!")

tender_id = "f9d885cc-03eb-435e-a2df-6ff7f1c14041"
bid_id = "6350a0bb-e7f7-4694-8136-48b6ef2e02bc"  # ABC Construction LLC

excel_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "test-bid-files", "priced-boq-wizard-test.xlsx")
print(f"\nExcel file: {excel_path}")
print(f"File exists: {os.path.exists(excel_path)}")
print(f"File size: {os.path.getsize(excel_path)} bytes")

# Try uploading via the bid import upload endpoint
# Check if there's a specific upload path for bid documents
print("\n--- Trying bid document upload ---")

# Try portal bid file upload first (as bidder)
try:
    upload_path = f"/api/portal/bids/{bid_id}/documents"
    print(f"Trying: POST {upload_path}")
    status, result = multipart_upload(bidder_token, upload_path, excel_path, {
        "documentType": "0",  # PricedBoq = 0
        "description": "Priced BOQ Excel"
    })
except Exception as e:
    print(f"Error: {e}")

# Try tender manager upload path
print("\n--- Trying as tender manager ---")
try:
    upload_path = f"/api/tenders/{tender_id}/bids/{bid_id}/import/upload"
    print(f"Trying: POST {upload_path}")
    status, result = multipart_upload(tm_token, upload_path, excel_path)
except Exception as e:
    print(f"Error: {e}")

# Try another approach - direct bid file upload
print("\n--- Trying direct file upload ---")
try:
    upload_path = f"/api/tenders/{tender_id}/bids/{bid_id}/files"
    print(f"Trying: POST {upload_path}")
    status, result = multipart_upload(tm_token, upload_path, excel_path, {
        "documentType": "0",
        "category": "commercial"
    })
except Exception as e:
    print(f"Error: {e}")
