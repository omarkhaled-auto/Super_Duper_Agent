"""
Test the full bid import pipeline end-to-end via API.
Parse -> Map Columns -> Match to BOQ -> Normalize -> Validate -> Execute
"""
import requests
import json

API_BASE = "http://localhost:5000/api"
TENDER_ID = "f9d885cc-03eb-435e-a2df-6ff7f1c14041"
BID_ID = "38eb0715-1624-42eb-bb59-e4d0281de045"

def login():
    resp = requests.post(f"{API_BASE}/auth/login", json={"email": "tendermgr@bayan.ae", "password": "Bayan@2024"})
    return resp.json()["data"]["accessToken"]

def api_post(endpoint, token, data=None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(f"{API_BASE}{endpoint}", headers=headers, json=data or {})
    return resp

def main():
    token = login()
    print("[OK] Logged in\n")
    base = f"/tenders/{TENDER_ID}/bids/{BID_ID}/import"

    # Step 1: Parse
    print("=" * 60)
    print("STEP 1: PARSE")
    print("=" * 60)
    resp = api_post(f"{base}/parse", token, {"previewRowCount": 25})
    parse_data = resp.json()
    if resp.status_code == 200 and parse_data.get("success"):
        data = parse_data["data"]
        print(f"  Sheets: {len(data.get('sheets', []))}")
        for s in data.get("sheets", []):
            print(f"    - {s['name']}: {s['rowCount']} rows x {s['columnCount']} cols")
        print(f"  Columns: {len(data.get('columns', []))}")
        for c in data.get("columns", []):
            print(f"    [{c['letter']}] {c['header']} -> {c['suggestedMapping']} ({c['dataType']})")
        print(f"  Preview rows: {len(data.get('previewRows', []))}")
        if data.get("previewRows"):
            print(f"    First row: {json.dumps(data['previewRows'][0])[:200]}")
    else:
        print(f"  ERROR: {json.dumps(parse_data, indent=2)[:500]}")
        return

    # Step 2: Map Columns
    print(f"\n{'=' * 60}")
    print("STEP 2: MAP COLUMNS")
    print("=" * 60)
    # Use the suggested mappings from parse
    column_mappings = []
    for c in data.get("columns", []):
        mapping = c.get("suggestedMapping", "Ignore")
        # Fix incorrect mappings
        if c["header"] == "Unit Rate (AED)" and mapping != "UnitRate":
            mapping = "UnitRate"
        if c["header"] == "Amount (AED)" and mapping != "Amount":
            mapping = "Amount"
        column_mappings.append({
            "columnIndex": c["index"],
            "columnLetter": c["letter"],
            "header": c["header"],
            "mappedTo": mapping
        })
        print(f"    [{c['letter']}] {c['header']} -> {mapping}")

    resp = api_post(f"{base}/map-columns", token, {
        "sheetIndex": 0,
        "columnMappings": column_mappings
    })
    map_data = resp.json()
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"  Response: {json.dumps(map_data.get('data', map_data), indent=2)[:500]}")
    else:
        print(f"  ERROR: {json.dumps(map_data, indent=2)[:500]}")

    # Step 3: Match to BOQ
    print(f"\n{'=' * 60}")
    print("STEP 3: MATCH TO BOQ")
    print("=" * 60)
    # Build items from preview rows using our mappings
    items = []
    for row in data.get("previewRows", []):
        item = {
            "itemNumber": str(row.get("Item No.", "")),
            "description": str(row.get("Description", "")),
            "quantity": float(row.get("Qty", 0)),
            "unit": str(row.get("UOM", "")),
            "unitRate": float(row.get("Unit Rate (AED)", 0)),
            "amount": float(row.get("Amount (AED)", 0)),
            "currency": str(row.get("Currency", "AED"))
        }
        items.append(item)

    print(f"  Sending {len(items)} items for matching...")
    resp = api_post(f"{base}/match", token, {
        "items": items,
        "fuzzyMatchThreshold": 70
    })
    match_data = resp.json()
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        md = match_data.get("data", match_data)
        print(f"  Matched: {md.get('matchedCount', 'N/A')}")
        print(f"  Unmatched: {md.get('unmatchedCount', 'N/A')}")
        print(f"  Total BOQ items: {md.get('totalBoqItems', 'N/A')}")
        matched_items = md.get("matchedItems", [])
        if matched_items:
            for mi in matched_items[:3]:
                print(f"    - {mi.get('itemNumber', 'N/A')}: {mi.get('description', 'N/A')[:60]} -> {mi.get('matchConfidence', 'N/A')}%")
    else:
        print(f"  ERROR: {json.dumps(match_data, indent=2)[:500]}")

    # Step 4: Normalize
    print(f"\n{'=' * 60}")
    print("STEP 4: NORMALIZE")
    print("=" * 60)
    resp = api_post(f"{base}/normalize", token, {
        "baseCurrency": "AED",
        "items": items
    })
    norm_data = resp.json()
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        nd = norm_data.get("data", norm_data)
        print(f"  Normalized items: {len(nd.get('normalizedItems', []))}")
        print(f"  Currency conversions: {nd.get('currencyConversions', 'N/A')}")
        print(f"  UOM normalizations: {nd.get('uomNormalizations', 'N/A')}")
    else:
        print(f"  ERROR: {json.dumps(norm_data, indent=2)[:500]}")

    # Step 5: Validate
    print(f"\n{'=' * 60}")
    print("STEP 5: VALIDATE")
    print("=" * 60)
    resp = api_post(f"{base}/validate", token, {
        "items": items
    })
    val_data = resp.json()
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        vd = val_data.get("data", val_data)
        print(f"  Is valid: {vd.get('isValid', 'N/A')}")
        print(f"  Errors: {vd.get('errors', [])}")
        print(f"  Warnings: {vd.get('warnings', [])}")
    else:
        print(f"  ERROR: {json.dumps(val_data, indent=2)[:500]}")

    # Step 6: Execute
    print(f"\n{'=' * 60}")
    print("STEP 6: EXECUTE IMPORT")
    print("=" * 60)
    resp = api_post(f"{base}/execute", token, {
        "items": items,
        "overwriteExisting": True
    })
    exec_data = resp.json()
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        ed = exec_data.get("data", exec_data)
        print(f"  Success: {ed.get('success', 'N/A')}")
        print(f"  Imported count: {ed.get('importedCount', 'N/A')}")
        print(f"  Skipped: {ed.get('skippedCount', 'N/A')}")
        print(f"  Total amount: {ed.get('totalAmount', 'N/A')}")
    else:
        print(f"  ERROR: {json.dumps(exec_data, indent=2)[:500]}")

    print(f"\n{'=' * 60}")
    print("PIPELINE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
