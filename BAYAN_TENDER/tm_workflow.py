"""
TM Workflow: Answer clarifications, publish bulletin, close tender, open bids.
"""
import urllib.request, json

API = 'http://localhost:5000/api'
TENDER = 'f9d885cc-03eb-435e-a2df-6ff7f1c14041'

# Login as TM
print('[1] Logging in as TenderManager...')
login_data = json.dumps({'email': 'tendermgr@bayan.ae', 'password': 'Bayan@2024'}).encode()
req = urllib.request.Request(f'{API}/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req).read())['data']['accessToken']
print(f'  Token obtained ({len(token)} chars)')

def api_call(method, path, body=None):
    url = f'{API}/{path}'
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    })
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f'  ERROR {e.code}: {error_body[:300]}')
        return None

# Step 2: Get clarifications
print('\n[2] Fetching clarifications...')
result = api_call('GET', f'tenders/{TENDER}/clarifications')
if result and result.get('success'):
    clarifications = result['data']
    if isinstance(clarifications, dict) and 'items' in clarifications:
        clarifications = clarifications['items']
    print(f'  Found {len(clarifications)} clarifications')
    for c in clarifications:
        cid = c.get('id')
        ref = c.get('referenceNumber', c.get('reference', 'N/A'))
        subject = c.get('subject', 'N/A')
        print(f'  - {ref}: {subject} (ID: {cid})')
else:
    print(f'  Result: {result}')
    clarifications = []

# Step 3: Answer the clarification
if clarifications:
    clar_id = clarifications[0]['id']
    print(f'\n[3] Drafting answer for clarification {clar_id}...')
    answer_text = (
        "Thank you for your clarification request regarding BOQ Item 1.2.\n\n"
        "1. Concrete Grade Requirements:\n"
        "   - C50 grade is required ONLY for raft foundation and pile caps due to the high groundwater table "
        "and sulfate exposure in the Dubai Marina coastal zone.\n"
        "   - C40 grade is acceptable for ground beams, columns, and suspended slabs.\n"
        "   - All concrete must comply with Dubai Municipality Building Code and BS EN 206.\n\n"
        "2. Minimum Cement Content:\n"
        "   - Raft foundation: Minimum 400 kg/m3 (OPC + 30% GGBS replacement)\n"
        "   - Other structural elements: Minimum 350 kg/m3\n"
        "   - Maximum w/c ratio: 0.40 for substructure, 0.45 for superstructure\n\n"
        "3. Admixture Requirements:\n"
        "   - Sulfate-resisting cement (SRC) or GGBS blend is mandatory for all elements below ground level.\n"
        "   - Plasticizer/superplasticizer required to achieve minimum slump of 150mm while maintaining low w/c ratio.\n"
        "   - Silica fume addition (8-10%) recommended for pile caps in aggressive soil conditions.\n\n"
        "The approved mix design will be issued as an addendum (Addendum No. 1) within 5 working days. "
        "All bidders should price based on the above specifications."
    )
    result = api_call('POST', f'tenders/{TENDER}/clarifications/{clar_id}/answer', {'answer': answer_text})
    if result and result.get('success'):
        print('  Answer drafted successfully')
    else:
        print(f'  Draft answer result: {result}')

    # Step 4: Approve the answer
    print(f'\n[4] Approving answer for clarification {clar_id}...')
    result = api_call('POST', f'tenders/{TENDER}/clarifications/{clar_id}/approve', {})
    if result and result.get('success'):
        print('  Answer approved - status: Answered')
    else:
        print(f'  Approve result: {result}')

    # Step 5: Publish Q&A Bulletin
    print(f'\n[5] Publishing Q&A Bulletin...')
    bulletin_data = {
        'clarificationIds': [clar_id],
        'introduction': 'This bulletin addresses clarification requests received from bidders regarding the Dubai Marina Mixed-Use Tower - Phase 2 Construction project. All bidders are required to acknowledge receipt and incorporate these responses into their bid submissions.',
        'closingNotes': 'Please note that this bulletin forms part of the tender documentation and must be read in conjunction with all other tender documents. Any conflict between this bulletin and the original tender documents shall be resolved in favor of this bulletin.'
    }
    result = api_call('POST', f'tenders/{TENDER}/clarifications/bulletins', bulletin_data)
    if result and result.get('success'):
        print(f'  Bulletin published: {json.dumps(result["data"], indent=2, default=str)[:500]}')
    else:
        print(f'  Bulletin result: {result}')

# Step 6: Close tender
print(f'\n[6] Closing tender...')
result = api_call('POST', f'tenders/{TENDER}/cancel', {})
if result and result.get('success'):
    print(f'  Tender closed successfully')
    print(f'  New status: {result["data"].get("status", "N/A")}')
else:
    print(f'  Close result: {result}')

# Step 7: Open bids
print(f'\n[7] Opening bids...')
result = api_call('POST', f'tenders/{TENDER}/bids/open', {})
if result and result.get('success'):
    print(f'  Bids opened successfully!')
    data = result['data']
    print(f'  Result: {json.dumps(data, indent=2, default=str)[:500]}')
else:
    print(f'  Open bids result: {result}')

print('\n=== TM WORKFLOW COMPLETE ===')
