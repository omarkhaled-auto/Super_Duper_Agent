"""
Setup script for Gap B - Create full tender lifecycle for approval rejection/return testing.
Creates a new tender, adds BOQ, invites bidders, submits bids, closes, opens bids,
and prepares it for approval initiation.
"""
import requests
import json
import time
import sys

API_BASE = "http://localhost:5000/api"
PORTAL_BASE = "http://localhost:5000/api/portal"

def login(email, password="Bayan@2024", portal=False):
    base = PORTAL_BASE if portal else API_BASE
    endpoint = f"{base}/auth/login" if portal else f"{API_BASE}/auth/login"
    resp = requests.post(endpoint, json={"email": email, "password": password})
    d = resp.json()
    if d.get("success"):
        return d["data"]["accessToken"]
    raise Exception(f"Login failed for {email}: {d.get('message')}")

def api_call(method, endpoint, token, data=None, base=API_BASE):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{base}{endpoint}"
    if method == "GET":
        resp = requests.get(url, headers=headers)
    elif method == "POST":
        resp = requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        resp = requests.put(url, headers=headers, json=data)
    elif method == "PATCH":
        resp = requests.patch(url, headers=headers, json=data)
    else:
        raise ValueError(f"Unknown method: {method}")

    result = resp.json() if resp.text else {}
    if isinstance(result, dict) and "data" in result:
        return result.get("data"), result.get("success", False), result.get("message", "")
    return result, resp.status_code == 200, ""

def main():
    print("=== Gap B Setup: Full Tender Lifecycle for Approval Testing ===\n")

    # 1. Login as tender manager
    tm_token = login("tendermgr@bayan.ae")
    print("[OK] Logged in as tendermgr@bayan.ae")

    # 2. Check if we have approver users
    approvers_data, ok, msg = api_call("GET", "/approvals/approvers", tm_token)
    if ok and approvers_data:
        print(f"[OK] Approvers available: {len(approvers_data) if isinstance(approvers_data, list) else 'unknown'}")
        if isinstance(approvers_data, list):
            for a in approvers_data[:5]:
                print(f"  - {a.get('email', a.get('Email', 'N/A'))} ({a.get('firstName', '')} {a.get('lastName', '')})")
    else:
        print(f"[WARN] Approvers endpoint: {msg}")

    # 3. Check existing tenders - we need one in a state ready for approval
    tenders_data, ok, _ = api_call("GET", "/tenders", tm_token)
    items = tenders_data.get("items", []) if isinstance(tenders_data, dict) else tenders_data if isinstance(tenders_data, list) else []

    # Find TNR-2026-0003 which is already awarded (Status 3) - it went through approval already
    target_tender = None
    for t in items:
        ref = t.get("reference", "")
        status = t.get("status")
        print(f"  Tender: {ref} | Status: {status} | {t.get('title', '')[:50]}")
        # We need a tender that's in evaluation or approval state
        # Status 3 = Awarded, Status 2 = UnderEvaluation, Status 1 = Active
        if ref == "TNR-2026-0003":
            target_tender = t

    # We'll create a new tender TNR-2026-0004 for the approval rejection test
    print("\n[STEP] Creating new tender for approval rejection/return testing...")

    new_tender_data = {
        "title": "Al Fahidi Heritage District - Restoration Project Phase 3",
        "titleAr": "منطقة الفهيدي التراثية - مشروع الترميم المرحلة الثالثة",
        "description": "Complete restoration and preservation of heritage buildings including structural reinforcement, traditional architectural restoration, and modern MEP integration.",
        "tenderType": 0,
        "baseCurrency": "AED",
        "submissionDeadline": "2026-02-28T10:00:00Z",
        "technicalWeightPercentage": 60,
        "commercialWeightPercentage": 40,
        "estimatedValue": 15000000,
        "projectDuration": 18,
        "projectDurationUnit": "months"
    }

    result, ok, msg = api_call("POST", "/tenders", tm_token, new_tender_data)
    if ok and result:
        tender_id = result.get("id")
        reference = result.get("reference", "N/A")
        print(f"  [OK] Created tender: {reference} | ID: {tender_id}")
    else:
        print(f"  [ERROR] Failed to create tender: {msg}")
        print(f"  Response: {json.dumps(result, indent=2)[:500]}")
        # Try using TNR-2026-0001 (Active) instead
        print("\n[FALLBACK] Will use existing TNR-2026-0001 (Active)...")
        for t in items:
            if t.get("reference") == "TNR-2026-0001":
                tender_id = t["id"]
                reference = "TNR-2026-0001"
                print(f"  Using: {reference} | ID: {tender_id}")
                break
        else:
            print("  [ERROR] No Active tender found!")
            sys.exit(1)

    # 4. Add BOQ sections and items
    print(f"\n[STEP] Adding BOQ sections and items to {reference}...")

    sections = [
        {"name": "Structural Works", "nameAr": "الأعمال الإنشائية", "sortOrder": 1},
        {"name": "Heritage Restoration", "nameAr": "أعمال الترميم التراثي", "sortOrder": 2},
        {"name": "MEP Works", "nameAr": "أعمال الميكانيكية والكهربائية والسباكة", "sortOrder": 3}
    ]

    section_ids = []
    for s in sections:
        result, ok, msg = api_call("POST", f"/tenders/{tender_id}/boq/sections", tm_token, s)
        if ok and result:
            sid = result.get("id")
            section_ids.append(sid)
            print(f"  [OK] Section: {s['name']} (ID: {sid})")
        else:
            print(f"  [WARN] Section {s['name']}: {msg}")
            # Try to get existing sections
            secs_result, _, _ = api_call("GET", f"/tenders/{tender_id}/boq/sections", tm_token)
            if isinstance(secs_result, list):
                section_ids = [s2.get("id") for s2 in secs_result]
                print(f"  Using existing sections: {section_ids}")
            break

    if not section_ids:
        print("  [ERROR] No sections created/found!")
        sys.exit(1)

    # Add items to sections
    boq_items_by_section = {
        0: [  # Structural Works
            {"itemNumber": "1.1", "description": "Foundation reinforcement with carbon fiber wrapping", "quantity": 500, "unit": "m2", "estimatedRate": 450},
            {"itemNumber": "1.2", "description": "Steel structural frame repair and replacement", "quantity": 120, "unit": "ton", "estimatedRate": 8500},
            {"itemNumber": "1.3", "description": "Load-bearing masonry wall restoration", "quantity": 800, "unit": "m2", "estimatedRate": 350},
        ],
        1: [  # Heritage Restoration
            {"itemNumber": "2.1", "description": "Traditional wind tower (barjeel) reconstruction", "quantity": 6, "unit": "Nr", "estimatedRate": 150000},
            {"itemNumber": "2.2", "description": "Decorative gypsum plasterwork restoration", "quantity": 1200, "unit": "m2", "estimatedRate": 280},
            {"itemNumber": "2.3", "description": "Heritage wooden door and window restoration", "quantity": 45, "unit": "Nr", "estimatedRate": 12000},
        ],
        2: [  # MEP
            {"itemNumber": "3.1", "description": "Concealed electrical wiring in heritage buildings", "quantity": 1, "unit": "LS", "estimatedRate": 850000},
            {"itemNumber": "3.2", "description": "Discreet HVAC system with heritage-compatible grilles", "quantity": 1, "unit": "LS", "estimatedRate": 1200000},
        ]
    }

    total_items = 0
    for idx, items_list in boq_items_by_section.items():
        if idx >= len(section_ids):
            break
        sid = section_ids[idx]
        for item in items_list:
            item["sectionId"] = sid
            result, ok, msg = api_call("POST", f"/tenders/{tender_id}/boq/items", tm_token, item)
            if ok:
                total_items += 1
            else:
                print(f"  [WARN] Item {item['itemNumber']}: {msg}")

    print(f"  [OK] Added {total_items} BOQ items")

    # 5. Invite bidders
    print(f"\n[STEP] Inviting bidders...")
    bidders_to_invite = ["bidder@vendor.ae", "bidder2@vendor.ae"]

    for bidder_email in bidders_to_invite:
        result, ok, msg = api_call("POST", f"/tenders/{tender_id}/bidders/invite",
                                   tm_token, {"email": bidder_email})
        if ok:
            print(f"  [OK] Invited: {bidder_email}")
        else:
            print(f"  [WARN] Invite {bidder_email}: {msg}")

    # 6. Submit bids as bidders
    print(f"\n[STEP] Submitting bids as bidders...")

    for bidder_email in bidders_to_invite:
        try:
            bidder_token = login(bidder_email)
            print(f"  [OK] Logged in as {bidder_email}")

            # Get available tenders for this bidder through portal
            portal_tenders, ok, _ = api_call("GET", f"/tenders/{tender_id}/portal", bidder_token)
            print(f"  Portal tenders response: {ok}")

            # Submit a basic bid
            bid_data = {
                "tenderId": tender_id,
                "totalAmount": 12500000 if bidder_email == "bidder@vendor.ae" else 13200000,
                "currency": "AED",
                "technicalProposal": "Comprehensive heritage restoration with modern techniques",
                "validityPeriod": 90
            }

            result, ok, msg = api_call("POST", f"/portal/tenders/{tender_id}/bids/submit",
                                       bidder_token, bid_data, base=API_BASE)
            if ok:
                print(f"  [OK] Bid submitted by {bidder_email}")
            else:
                print(f"  [WARN] Bid submission: {msg}")
                # Try alternative endpoint
                result2, ok2, msg2 = api_call("POST", f"/tenders/{tender_id}/bids",
                                              tm_token, {
                                                  "bidderEmail": bidder_email,
                                                  "totalAmount": bid_data["totalAmount"],
                                                  "currency": "AED"
                                              })
                if ok2:
                    print(f"  [OK] Bid created via admin endpoint")
                else:
                    print(f"  [WARN] Admin bid creation: {msg2}")
        except Exception as e:
            print(f"  [ERROR] {bidder_email}: {str(e)}")

    # 7. Close tender and open bids
    print(f"\n[STEP] Closing tender and opening bids...")

    result, ok, msg = api_call("POST", f"/tenders/{tender_id}/close", tm_token)
    if ok:
        print(f"  [OK] Tender closed")
    else:
        print(f"  [WARN] Close: {msg}")

    result, ok, msg = api_call("POST", f"/tenders/{tender_id}/bids/open", tm_token)
    if ok:
        print(f"  [OK] Bids opened")
    else:
        print(f"  [WARN] Open bids: {msg}")

    # 8. Enter evaluation scores
    print(f"\n[STEP] Entering evaluation data...")
    # This may need technical scoring and commercial scoring

    # Check current status
    tender_data, ok, _ = api_call("GET", f"/tenders/{tender_id}", tm_token)
    if ok:
        current_status = tender_data.get("status") if isinstance(tender_data, dict) else "unknown"
        print(f"  Current tender status: {current_status}")
    else:
        print(f"  Could not get tender status")

    print(f"\n=== Gap B Setup Complete ===")
    print(f"Tender: {reference} | ID: {tender_id}")
    print(f"Next steps: Initiate approval workflow, test Return/Reject flows")
    print(f"Save this tender_id for browser testing: {tender_id}")

if __name__ == "__main__":
    main()
