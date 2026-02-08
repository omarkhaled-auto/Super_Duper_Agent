"""
Approval Workflow: 3-level sequential approval for tender award.
Creates additional approvers if needed, initiates workflow, then approves at each level.
"""
import urllib.request, json

API = 'http://localhost:5000/api'
TENDER = 'f9d885cc-03eb-435e-a2df-6ff7f1c14041'

def api_call(method, path, body=None, token=None):
    url = f'{API}/{path}'
    data = json.dumps(body).encode() if body else None
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f'  ERROR {e.code}: {error_body[:500]}')
        return None

def login(email, password='Bayan@2024'):
    result = api_call('POST', 'auth/login', {'email': email, 'password': password})
    if result and result.get('success'):
        return result['data']['accessToken']
    return None

# Step 1: Login as admin to create approver accounts
print('[1] Logging in as admin...')
admin_token = login('admin@bayan.ae')
if not admin_token:
    print('  FAILED to login as admin')
    exit(1)
print(f'  Admin token obtained')

# Step 2: Get existing approvers
print('\n[2] Fetching existing approvers...')
result = api_call('GET', 'approvers', token=admin_token)
approver_ids = []
if result and result.get('success'):
    approvers = result['data']
    if isinstance(approvers, dict) and 'items' in approvers:
        approvers = approvers['items']
    elif isinstance(approvers, dict) and 'data' in approvers:
        approvers = approvers['data']
    if isinstance(approvers, list):
        print(f'  Found {len(approvers)} existing approvers:')
        for a in approvers:
            aid = a.get('id')
            name = a.get('fullName', a.get('name', 'N/A'))
            email = a.get('email', 'N/A')
            print(f'    - {name} ({email}) ID: {aid}')
            approver_ids.append(aid)
    else:
        print(f'  Approvers data type: {type(approvers)}, keys: {approvers.keys() if isinstance(approvers, dict) else "N/A"}')
        print(f'  Raw: {json.dumps(result["data"], default=str)[:500]}')
else:
    print(f'  Result: {result}')

# Step 3: Create additional approver accounts if we have fewer than 3
APPROVER_ACCOUNTS = [
    {'email': 'approver2@bayan.ae', 'fullName': 'Sarah Al-Mansouri', 'firstName': 'Sarah', 'lastName': 'Al-Mansouri'},
    {'email': 'approver3@bayan.ae', 'fullName': 'Mohammed Al-Hashimi', 'firstName': 'Mohammed', 'lastName': 'Al-Hashimi'},
]

if len(approver_ids) < 3:
    print(f'\n[3] Creating additional approver accounts (have {len(approver_ids)}, need 3)...')
    for acct in APPROVER_ACCOUNTS:
        if len(approver_ids) >= 3:
            break
        result = api_call('POST', 'admin/users', {
            'email': acct['email'],
            'password': 'Bayan@2024',
            'firstName': acct['firstName'],
            'lastName': acct['lastName'],
            'role': 4,  # Approver role
            'isActive': True
        }, token=admin_token)
        if result and result.get('success'):
            uid = result['data'].get('id') or result['data'].get('userId')
            print(f'  Created: {acct["fullName"]} ({acct["email"]}) ID: {uid}')
            approver_ids.append(uid)
        else:
            # May already exist - try to find by listing users
            print(f'  Create result: {result}')
            # Try to get user by email
            users_result = api_call('GET', f'admin/users?search={acct["email"]}', token=admin_token)
            if users_result and users_result.get('success'):
                users = users_result['data']
                if isinstance(users, dict) and 'items' in users:
                    users = users['items']
                if isinstance(users, list):
                    for u in users:
                        if u.get('email') == acct['email']:
                            uid = u.get('id')
                            print(f'  Found existing: {acct["fullName"]} ID: {uid}')
                            approver_ids.append(uid)
                            break

print(f'\n  Available approver IDs ({len(approver_ids)}): {approver_ids[:3]}')

if len(approver_ids) < 3:
    print('  WARNING: Less than 3 approvers available. Trying with admin/TM as fallback...')
    # Get user IDs for admin and TM as fallback
    users_result = api_call('GET', 'admin/users', token=admin_token)
    if users_result and users_result.get('success'):
        all_users = users_result['data']
        if isinstance(all_users, dict) and 'items' in all_users:
            all_users = all_users['items']
        if isinstance(all_users, list):
            for u in all_users:
                if len(approver_ids) >= 3:
                    break
                uid = u.get('id')
                if uid not in approver_ids and u.get('role') in [0, 4]:  # Admin or Approver
                    approver_ids.append(uid)
                    print(f'  Fallback approver: {u.get("fullName", u.get("email"))} ID: {uid}')

# Step 4: Login as TM to initiate approval
print('\n[4] Logging in as TenderManager...')
tm_token = login('tendermgr@bayan.ae')
print(f'  TM token obtained')

# Step 5: Initiate approval workflow
print('\n[5] Initiating 3-level approval workflow...')
initiate_data = {
    'approverUserIds': approver_ids[:3],
    'levelDeadlines': [
        '2026-02-15T23:59:59Z',
        '2026-02-20T23:59:59Z',
        '2026-02-25T23:59:59Z'
    ]
}
print(f'  Approvers: {approver_ids[:3]}')
result = api_call('POST', f'tenders/{TENDER}/approval/initiate', initiate_data, token=tm_token)
if result and result.get('success'):
    workflow = result['data']
    wf_id = workflow.get('workflowId', workflow.get('id', 'N/A'))
    print(f'  Workflow initiated! ID: {wf_id}')
    print(f'  Level 1 notification sent: {workflow.get("level1NotificationSent", "N/A")}')
else:
    print(f'  Initiate result: {result}')
    # Check if already initiated
    print('  Checking existing approval status...')
    status = api_call('GET', f'tenders/{TENDER}/approval', token=tm_token)
    if status and status.get('success'):
        print(f'  Existing workflow: {json.dumps(status["data"], indent=2, default=str)[:800]}')

# Step 6: Check approval status
print('\n[6] Checking approval status...')
status = api_call('GET', f'tenders/{TENDER}/approval', token=tm_token)
if status and status.get('success'):
    wf = status['data']
    print(f'  Workflow status: {wf.get("status")}')
    print(f'  Current level: {wf.get("currentLevel")} of {wf.get("totalLevels")}')
    levels = wf.get('levels', [])
    for lvl in levels:
        print(f'  Level {lvl["levelNumber"]}: {lvl.get("approverName", lvl.get("approverEmail", "N/A"))} - Status: {lvl.get("status")}')

# Step 7: Level 1 Approval
print('\n[7] === LEVEL 1 APPROVAL ===')
if levels and len(levels) >= 1:
    lvl1_email = levels[0].get('approverEmail')
    print(f'  Logging in as Level 1 approver: {lvl1_email}')
    approver1_token = login(lvl1_email)
    if approver1_token:
        result = api_call('POST', f'tenders/{TENDER}/approval/decide', {
            'decision': 0,  # Approve
            'comment': 'Level 1 approved. Commercial evaluation confirms ABC Construction LLC offers the most competitive pricing with comprehensive methodology. Recommend proceeding to Level 2.'
        }, token=approver1_token)
        if result and result.get('success'):
            print(f'  Level 1 APPROVED!')
            print(f'  Message: {result["data"].get("message", "N/A")}')
            print(f'  Workflow complete: {result["data"].get("isWorkflowComplete", False)}')
        else:
            print(f'  Level 1 result: {result}')
    else:
        print(f'  Failed to login as {lvl1_email}')

# Step 8: Level 2 Approval
print('\n[8] === LEVEL 2 APPROVAL ===')
if levels and len(levels) >= 2:
    lvl2_email = levels[1].get('approverEmail')
    print(f'  Logging in as Level 2 approver: {lvl2_email}')
    approver2_token = login(lvl2_email)
    if approver2_token:
        result = api_call('POST', f'tenders/{TENDER}/approval/decide', {
            'decision': 0,  # Approve
            'comment': 'Level 2 approved. Technical compliance verified - all submissions meet Dubai Municipality Building Code requirements. HSE plans reviewed and found satisfactory. Escalating to final authority.'
        }, token=approver2_token)
        if result and result.get('success'):
            print(f'  Level 2 APPROVED!')
            print(f'  Message: {result["data"].get("message", "N/A")}')
            print(f'  Workflow complete: {result["data"].get("isWorkflowComplete", False)}')
        else:
            print(f'  Level 2 result: {result}')
    else:
        print(f'  Failed to login as {lvl2_email}')

# Step 9: Level 3 Approval (Final - triggers Award)
print('\n[9] === LEVEL 3 APPROVAL (FINAL) ===')
if levels and len(levels) >= 3:
    lvl3_email = levels[2].get('approverEmail')
    print(f'  Logging in as Level 3 approver: {lvl3_email}')
    approver3_token = login(lvl3_email)
    if approver3_token:
        result = api_call('POST', f'tenders/{TENDER}/approval/decide', {
            'decision': 0,  # Approve
            'comment': 'Final approval granted. Award recommendation for Dubai Marina Mixed-Use Tower Phase 2 Construction is hereby authorized. Contract value and terms confirmed per evaluation committee recommendation. Proceed with Letter of Award issuance.'
        }, token=approver3_token)
        if result and result.get('success'):
            print(f'  Level 3 APPROVED! (FINAL)')
            print(f'  Message: {result["data"].get("message", "N/A")}')
            print(f'  Workflow COMPLETE: {result["data"].get("isWorkflowComplete", False)}')
            print(f'  Tender should now be AWARDED!')
        else:
            print(f'  Level 3 result: {result}')
    else:
        print(f'  Failed to login as {lvl3_email}')

# Step 10: Final verification
print('\n[10] Final verification...')
final_status = api_call('GET', f'tenders/{TENDER}/approval', token=tm_token)
if final_status and final_status.get('success'):
    wf = final_status['data']
    print(f'  Final workflow status: {wf.get("status")}')
    print(f'  Completed at: {wf.get("completedAt", "N/A")}')
    for lvl in wf.get('levels', []):
        print(f'  Level {lvl["levelNumber"]}: {lvl.get("approverName", "N/A")} - Decision: {lvl.get("decision")} at {lvl.get("decidedAt", "N/A")}')

# Check tender status
tender_result = api_call('GET', f'tenders/{TENDER}', token=tm_token)
if tender_result and tender_result.get('success'):
    t = tender_result['data']
    print(f'\n  Tender status: {t.get("status")}')
    print(f'  Tender reference: {t.get("referenceNumber", "N/A")}')
    print(f'  Title: {t.get("title", "N/A")}')

print('\n=== APPROVAL WORKFLOW COMPLETE ===')
