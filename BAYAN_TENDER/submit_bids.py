"""
Submit bids for both bidders via API.
Bidder 1 (ABC Construction LLC) - AED 42,500,000 total
Bidder 2 (Gulf MEP Services) - AED 44,800,000 total
"""
import urllib.request, json, os, sys

API = 'http://localhost:5000/api'
TENDER = 'f9d885cc-03eb-435e-a2df-6ff7f1c14041'
FILES_DIR = os.path.join(os.path.dirname(__file__), 'test-bid-files')

BIDDERS = [
    {
        'email': 'bidder@vendor.ae',
        'name': 'ABC Construction LLC',
        'bidValidity': 120,  # 120 days
    },
    {
        'email': 'bidder2@vendor.ae',
        'name': 'Gulf MEP Services',
        'bidValidity': 90,  # 90 days
    }
]

DOC_TYPES = [
    ('PricedBOQ', 'priced-boq.xlsx'),
    ('Methodology', 'methodology.pdf'),
    ('TeamCVs', 'team-cvs.pdf'),
    ('Program', 'work-program.pdf'),
    ('HSEPlan', 'hse-plan.pdf'),
]

def portal_login(email):
    """Login to bidder portal and return token."""
    data = json.dumps({
        'email': email,
        'password': 'Bayan@2024',
        'tenderId': TENDER
    }).encode()
    req = urllib.request.Request(
        f'{API}/portal/auth/login',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    if resp.get('success'):
        return resp['data']['accessToken']
    else:
        print(f'  LOGIN FAILED: {resp}')
        return None

def upload_file(token, doc_type, filename):
    """Upload a bid document using multipart form data."""
    filepath = os.path.join(FILES_DIR, filename)
    if not os.path.exists(filepath):
        print(f'  FILE NOT FOUND: {filepath}')
        return None

    # Build multipart form data manually
    boundary = '----BayanBidUpload2026'
    file_content = open(filepath, 'rb').read()

    # Determine content type
    ext = filename.split('.')[-1].lower()
    content_types = {
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    ct = content_types.get(ext, 'application/octet-stream')

    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f'Content-Type: {ct}\r\n'
        f'\r\n'
    ).encode() + file_content + f'\r\n--{boundary}--\r\n'.encode()

    url = f'{API}/portal/tenders/{TENDER}/bids/upload?documentType={doc_type}'
    req = urllib.request.Request(url, data=body, headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Authorization': f'Bearer {token}'
    })

    try:
        resp = json.loads(urllib.request.urlopen(req).read())
        if resp.get('success'):
            doc_id = resp['data'].get('id') or resp['data'].get('documentId')
            print(f'  UPLOADED: {doc_type} ({filename}) -> ID: {doc_id}')
            return doc_id
        else:
            print(f'  UPLOAD FAIL: {doc_type} -> {resp}')
            return None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f'  UPLOAD ERROR {e.code}: {doc_type} -> {error_body[:200]}')
        return None

def submit_bid(token, bid_validity_days):
    """Submit the bid."""
    data = json.dumps({
        'bidValidityDays': bid_validity_days
    }).encode()
    url = f'{API}/portal/tenders/{TENDER}/bids/submit'
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    })
    try:
        resp = json.loads(urllib.request.urlopen(req).read())
        if resp.get('success'):
            bid_data = resp['data']
            print(f'  BID SUBMITTED! ID: {bid_data.get("bidId") or bid_data.get("id")}')
            print(f'  Receipt: {json.dumps(bid_data, indent=2, default=str)}')
            return bid_data
        else:
            print(f'  SUBMIT FAIL: {resp}')
            return None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f'  SUBMIT ERROR {e.code}: {error_body[:300]}')
        return None

def process_bidder(bidder):
    """Process a single bidder: login, upload docs, submit bid."""
    print(f'\n{"="*60}')
    print(f'BIDDER: {bidder["name"]} ({bidder["email"]})')
    print(f'{"="*60}')

    # Step 1: Login
    print('\n[1] Logging in...')
    token = portal_login(bidder['email'])
    if not token:
        return None
    print(f'  Token obtained ({len(token)} chars)')

    # Step 2: Upload documents
    print('\n[2] Uploading bid documents...')
    doc_ids = []
    for doc_type, filename in DOC_TYPES:
        doc_id = upload_file(token, doc_type, filename)
        if doc_id:
            doc_ids.append(doc_id)

    print(f'\n  Uploaded {len(doc_ids)}/{len(DOC_TYPES)} documents')

    # Step 3: Submit bid
    print(f'\n[3] Submitting bid (validity: {bidder["bidValidity"]} days)...')
    result = submit_bid(token, bidder['bidValidity'])

    return result

# Main execution
if __name__ == '__main__':
    results = {}
    for bidder in BIDDERS:
        result = process_bidder(bidder)
        results[bidder['email']] = result

    print(f'\n\n{"="*60}')
    print('FINAL SUMMARY')
    print(f'{"="*60}')
    for email, result in results.items():
        status = 'SUCCESS' if result else 'FAILED'
        bid_id = (result.get('bidId') or result.get('id') or 'N/A') if result else 'N/A'
        print(f'  {email}: {status} (Bid ID: {bid_id})')
