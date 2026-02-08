#!/usr/bin/env python3
"""Check bid documents for TNR-2026-0003"""
import json
import urllib.request

API_BASE = "http://localhost:5000/api"

def login(email, password):
    data = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(f"{API_BASE}/auth/login", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        return result["data"]["accessToken"]

def api_get(token, path):
    req = urllib.request.Request(f"{API_BASE}{path}", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

token = login("tendermgr@bayan.ae", "Bayan@2024")
tender_id = "f9d885cc-03eb-435e-a2df-6ff7f1c14041"

# Get bid details for each bid
for bid_id in ["6350a0bb-e7f7-4694-8136-48b6ef2e02bc", "38eb0715-1624-42eb-bb59-e4d0281de045"]:
    print(f"\n--- Bid {bid_id[:8]}... ---")
    try:
        bid = api_get(token, f"/tenders/{tender_id}/bids/{bid_id}")
        bid_data = bid.get("data", {})
        print(f"Bidder: {bid_data.get('bidderName', '?')}")
        print(f"Status: {bid_data.get('status', '?')}")
        print(f"Import Status: {bid_data.get('importStatus', '?')}")
        docs = bid_data.get("documents", [])
        print(f"Documents ({len(docs)}):")
        for doc in docs:
            print(f"  - {doc.get('originalFilename','?')} (type: {doc.get('documentType','?')}, "
                  f"category: {doc.get('category','?')}, size: {doc.get('fileSize','?')} bytes, "
                  f"mime: {doc.get('mimeType','?')})")
            print(f"    id: {doc.get('id','?')}")
    except Exception as e:
        print(f"Error: {e}")

# Also check the import endpoint availability
print("\n--- Checking import endpoint ---")
try:
    bid_id = "6350a0bb-e7f7-4694-8136-48b6ef2e02bc"
    parse_url = f"{API_BASE}/tenders/{tender_id}/bids/{bid_id}/import/parse"
    data = json.dumps({"previewRowCount": 10}).encode()
    req = urllib.request.Request(parse_url, data=data, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        print(f"Parse result: {json.dumps(result, indent=2)[:1000]}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body[:500]}")
except Exception as e:
    print(f"Error: {e}")
