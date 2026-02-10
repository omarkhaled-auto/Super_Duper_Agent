"""
Approval Workflow v2: Use known approver accounts (approver@, approver2@, approver3@bayan.ae)
"""
import urllib.request, json

API = 'http://localhost:5000/api'
TENDER = 'f9d885cc-03eb-435e-a2df-6ff7f1c14041'

# Known approver IDs from /api/approvers
APPROVER_IDS = [
    'b6d60ec6-fdfa-4f02-9db7-34e26024ae1a',  # approver@bayan.ae - Khalid Al-Mansour
    '69369dcf-eb05-4a45-9b5e-51b0e91a92b7',  # approver2@bayan.ae - Omar Al-Sayed
    '87878433-8b59-4014-9084-d619bf2facc9',   # approver3@bayan.ae - Noor Al-Qasimi
]

APPROVER_EMAILS = [
    'approver@bayan.ae',
    'approver2@bayan.ae',
    'approver3@bayan.ae',
]

def api_call(method, path, body=None, token=None):
    url = f'{API}/{path}'
    data = json.dumps(body).encode() if body else None
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f'  ERROR {e.code}: {error_body[:500]}')
        return None

def login(email, password='Bayan@2024'):
    result = api_call('POST', 'auth/login', {'email': email, 'password': password})
    if result and result.get('success'):
        return result['data']['accessToken']
    print(f'  Login failed for {email}')
    return None

# Step 1: Verify all approvers can login
print('[1] Verifying approver logins...')
tokens = {}
for email in APPROVER_EMAILS:
    token = login(email)
    if token:
        tokens[email] = token
        print(f'  OK: {email}')
    else:
        print(f'  FAIL: {email}')

if len(tokens) < 3:
    print(f'\n  Only {len(tokens)}/3 approvers can login. Aborting.')
    exit(1)

# Step 2: Login as TM
print('\n[2] Logging in as TenderManager...')
tm_token = login('tendermgr@bayan.ae')
print(f'  TM token obtained')

# Step 3: Initiate approval
print('\n[3] Initiating 3-level approval workflow...')
print(f'  Level 1: approver@bayan.ae (Khalid Al-Mansour)')
print(f'  Level 2: approver2@bayan.ae (Omar Al-Sayed)')
print(f'  Level 3: approver3@bayan.ae (Noor Al-Qasimi)')
result = api_call('POST', f'tenders/{TENDER}/approval/initiate', {
    'approverUserIds': APPROVER_IDS,
    'levelDeadlines': [
        '2026-02-15T23:59:59Z',
        '2026-02-20T23:59:59Z',
        '2026-02-25T23:59:59Z'
    ]
}, token=tm_token)
if result and result.get('success'):
    wf = result['data']
    print(f'  Workflow initiated! ID: {wf.get("workflowId", wf.get("id"))}')
    print(f'  Level 1 notification sent: {wf.get("level1NotificationSent")}')
else:
    print(f'  FAILED: {result}')
    exit(1)

# Step 4: Check status
print('\n[4] Approval status:')
status = api_call('GET', f'tenders/{TENDER}/approval', token=tm_token)
if status and status.get('success'):
    wf = status['data']
    print(f'  Status: {wf.get("status")} (1=InProgress)')
    print(f'  Current level: {wf.get("currentLevel")}/{wf.get("totalLevels")}')
    for lvl in wf.get('levels', []):
        smap = {0:'Waiting', 1:'Active', 2:'Approved', 3:'Rejected', 4:'Returned'}
        print(f'  Level {lvl["levelNumber"]}: {lvl.get("approverName", "N/A")} ({lvl.get("approverEmail")}) - {smap.get(lvl.get("status"), lvl.get("status"))}')

# Step 5: Level 1 Approval
print('\n' + '='*60)
print('[5] LEVEL 1 APPROVAL - Khalid Al-Mansour (approver@bayan.ae)')
print('='*60)
result = api_call('POST', f'tenders/{TENDER}/approval/decide', {
    'decision': 0,
    'comment': 'Level 1 approved. Commercial evaluation confirms ABC Construction LLC offers the most competitive pricing at AED 42.5M with comprehensive methodology and proven track record in similar high-rise projects in Dubai Marina. Technical submission meets all mandatory requirements. Recommend proceeding to Level 2 review.'
}, token=tokens['approver@bayan.ae'])
if result and result.get('success'):
    d = result['data']
    print(f'  APPROVED!')
    print(f'  Message: {d.get("message")}')
    print(f'  Workflow complete: {d.get("isWorkflowComplete")}')
    print(f'  Notification sent: {d.get("notificationSent")}')
else:
    print(f'  FAILED')

# Step 6: Level 2 Approval
print('\n' + '='*60)
print('[6] LEVEL 2 APPROVAL - Omar Al-Sayed (approver2@bayan.ae)')
print('='*60)
result = api_call('POST', f'tenders/{TENDER}/approval/decide', {
    'decision': 0,
    'comment': 'Level 2 approved. Technical compliance verified — all structural specifications meet Dubai Municipality Building Code and BS EN standards. HSE plans reviewed against DEWA, DCD, and TRAKHEES requirements. MEP scope aligns with ASHRAE 90.1-2019 energy efficiency targets. Risk assessment satisfactory. Escalating to final authority for contract award authorization.'
}, token=tokens['approver2@bayan.ae'])
if result and result.get('success'):
    d = result['data']
    print(f'  APPROVED!')
    print(f'  Message: {d.get("message")}')
    print(f'  Workflow complete: {d.get("isWorkflowComplete")}')
    print(f'  Notification sent: {d.get("notificationSent")}')
else:
    print(f'  FAILED')

# Step 7: Level 3 Approval (FINAL - triggers tender award)
print('\n' + '='*60)
print('[7] LEVEL 3 APPROVAL (FINAL) - Noor Al-Qasimi (approver3@bayan.ae)')
print('='*60)
result = api_call('POST', f'tenders/{TENDER}/approval/decide', {
    'decision': 0,
    'comment': 'Final approval granted. Award recommendation for Dubai Marina Mixed-Use Tower — Phase 2 Construction (TNR-2026-0003) is hereby authorized. Contract to be awarded to ABC Construction LLC for the tendered sum. All evaluation criteria have been satisfactorily reviewed across three levels of authority. Proceed with issuance of Letter of Award and contract documentation per BAYAN procurement protocols.'
}, token=tokens['approver3@bayan.ae'])
if result and result.get('success'):
    d = result['data']
    print(f'  APPROVED! (FINAL)')
    print(f'  Message: {d.get("message")}')
    print(f'  WORKFLOW COMPLETE: {d.get("isWorkflowComplete")}')
    print(f'  Notification sent: {d.get("notificationSent")}')
else:
    print(f'  FAILED')

# Step 8: Final verification
print('\n' + '='*60)
print('[8] FINAL VERIFICATION')
print('='*60)
status = api_call('GET', f'tenders/{TENDER}/approval', token=tm_token)
if status and status.get('success'):
    wf = status['data']
    smap = {0:'Pending', 1:'InProgress', 2:'Approved', 3:'Rejected', 4:'RevisionNeeded'}
    print(f'  Workflow status: {smap.get(wf.get("status"), wf.get("status"))}')
    print(f'  Initiated by: {wf.get("initiatedByName")}')
    print(f'  Initiated at: {wf.get("initiatedAt")}')
    print(f'  Completed at: {wf.get("completedAt", "N/A")}')
    for lvl in wf.get('levels', []):
        dmap = {0:'Approve', 1:'Reject', 2:'ReturnForRevision'}
        lsmap = {0:'Waiting', 1:'Active', 2:'Approved', 3:'Rejected', 4:'Returned'}
        print(f'  Level {lvl["levelNumber"]}: {lvl.get("approverName")} - {lsmap.get(lvl.get("status"), "?")} - Decision: {dmap.get(lvl.get("decision"), "Pending")} at {lvl.get("decidedAt", "N/A")}')

# Check tender status
tender = api_call('GET', f'tenders/{TENDER}', token=tm_token)
if tender and tender.get('success'):
    t = tender['data']
    tmap = {0:'Draft', 1:'Active', 2:'Evaluation', 3:'Awarded', 4:'Cancelled'}
    print(f'\n  TENDER STATUS: {tmap.get(t.get("status"), t.get("status"))}')
    print(f'  Reference: {t.get("referenceNumber", "N/A")}')
    print(f'  Title: {t.get("title")}')

print('\n=== 3-LEVEL APPROVAL WORKFLOW COMPLETE ===')
