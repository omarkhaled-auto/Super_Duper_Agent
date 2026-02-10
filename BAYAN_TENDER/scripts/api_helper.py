#!/usr/bin/env python3
"""API helper for Bayan Tender System"""
import json
import urllib.request
import urllib.error
import sys

API_BASE = "http://localhost:5000/api"

def login(email, password):
    """Login and return access token"""
    data = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(f"{API_BASE}/auth/login", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        return result["data"]["accessToken"]

def api_get(token, path):
    """Make authenticated GET request"""
    req = urllib.request.Request(f"{API_BASE}{path}", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def api_post(token, path, body=None):
    """Make authenticated POST request"""
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{API_BASE}{path}", data=data, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tenders"

    token = login("tendermgr@bayan.ae", "Bayan@2024")

    if cmd == "tenders":
        result = api_get(token, "/tenders?page=1&pageSize=20")
        items = result.get("data", {}).get("items", [])
        for t in items:
            print(f"ID: {t['id']}, Ref: {t.get('reference','?')}, Status: {t.get('status','?')}, Title: {t.get('title','?')[:60]}")

    elif cmd == "boq":
        tender_id = sys.argv[2]
        result = api_get(token, f"/tenders/{tender_id}/boq")
        print(json.dumps(result, indent=2)[:3000])

    elif cmd == "bids":
        tender_id = sys.argv[2]
        result = api_get(token, f"/tenders/{tender_id}/bids?page=1&pageSize=10")
        print(json.dumps(result, indent=2)[:3000])

    elif cmd == "tender":
        tender_id = sys.argv[2]
        result = api_get(token, f"/tenders/{tender_id}")
        print(json.dumps(result, indent=2)[:3000])

    elif cmd == "approval":
        tender_id = sys.argv[2]
        result = api_get(token, f"/tenders/{tender_id}/approval")
        print(json.dumps(result, indent=2)[:3000])

    elif cmd == "approvers":
        result = api_get(token, "/approvers")
        print(json.dumps(result, indent=2)[:3000])

    elif cmd == "users":
        admin_token = login("admin@bayan.ae", "Bayan@2024")
        result = api_get(admin_token, "/admin/users?page=1&pageSize=20")
        items = result.get("data", {}).get("items", [])
        for u in items:
            print(f"ID: {u['id']}, Email: {u.get('email','?')}, Role: {u.get('roleName','?')}")
