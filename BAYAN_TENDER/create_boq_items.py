import urllib.request, json

# Login
login_data = json.dumps({'email': 'tendermgr@bayan.ae', 'password': 'Bayan@2024'}).encode()
req = urllib.request.Request('http://localhost:5000/api/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req).read())['data']['accessToken']

TENDER = 'f9d885cc-03eb-435e-a2df-6ff7f1c14041'
CIVIL = '733b9969-b7b7-4373-af3c-05b06b37f620'
MEP = '05ec8287-f001-4c36-b16a-2ff1d5892903'
FINISH = '028c189f-1bdf-4b5e-bad7-3180e206d450'
EXT = 'fd8488bc-03dc-400d-b3ce-899a2783f621'

items = [
    # Civil Works (1.2 - 1.6)
    {'sectionId': CIVIL, 'itemNumber': '1.2', 'description': 'Reinforced concrete for foundations, columns, beams, and slabs (Grade C40/50) including formwork and rebar', 'quantity': 3200, 'uom': 'm3', 'itemType': 0, 'notes': 'Rebar to ASTM A615 Grade 60', 'sortOrder': 2},
    {'sectionId': CIVIL, 'itemNumber': '1.3', 'description': 'Structural steel framework supply, fabrication, and erection including connections and fire protection', 'quantity': 850, 'uom': 'ton', 'itemType': 0, 'notes': 'Grade S355JR to EN 10025', 'sortOrder': 3},
    {'sectionId': CIVIL, 'itemNumber': '1.4', 'description': 'Concrete block masonry walls (200mm thick) including mortar joints and reinforcement', 'quantity': 4600, 'uom': 'm2', 'itemType': 0, 'notes': 'Hollow blocks to BS 6073', 'sortOrder': 4},
    {'sectionId': CIVIL, 'itemNumber': '1.5', 'description': 'Waterproofing membrane system to basement walls and raft foundation with protection board', 'quantity': 2800, 'uom': 'm2', 'itemType': 0, 'notes': 'Torch-applied modified bitumen, 10-year warranty', 'sortOrder': 5},
    {'sectionId': CIVIL, 'itemNumber': '1.6', 'description': 'Premium Italian marble cladding to main lobby walls and floor (Calacatta Gold)', 'quantity': 450, 'uom': 'm2', 'itemType': 1, 'notes': 'ALTERNATE: Subject to client approval of material selection', 'sortOrder': 6},

    # MEP Works (2.1 - 2.6)
    {'sectionId': MEP, 'itemNumber': '2.1', 'description': 'HVAC system complete - chillers, AHUs, FCUs, ductwork, controls, and BMS integration', 'quantity': 1, 'uom': 'LS', 'itemType': 0, 'notes': 'Energy efficiency to ASHRAE 90.1-2019', 'sortOrder': 1},
    {'sectionId': MEP, 'itemNumber': '2.2', 'description': 'Electrical distribution system - HV/LV panels, transformers, cable trays, wiring, and earthing', 'quantity': 1, 'uom': 'LS', 'itemType': 0, 'notes': 'DEWA approved equipment only', 'sortOrder': 2},
    {'sectionId': MEP, 'itemNumber': '2.3', 'description': 'Fire fighting system - wet riser, sprinklers, hydrants, fire pump set, and alarm system', 'quantity': 45, 'uom': 'nos', 'itemType': 0, 'notes': 'Per DCD requirements and NFPA standards', 'sortOrder': 3},
    {'sectionId': MEP, 'itemNumber': '2.4', 'description': 'Plumbing and drainage - hot/cold water supply, soil and waste drainage, rainwater pipes', 'quantity': 3200, 'uom': 'lm', 'itemType': 0, 'notes': 'PPR pipes for supply, uPVC for drainage', 'sortOrder': 4},
    {'sectionId': MEP, 'itemNumber': '2.5', 'description': 'Low current systems - CCTV, access control, structured cabling, BMS, and intercom', 'quantity': 1, 'uom': 'LS', 'itemType': 0, 'notes': 'Category 6A cabling throughout', 'sortOrder': 5},
    {'sectionId': MEP, 'itemNumber': '2.6', 'description': 'Specialized MEP testing, commissioning, and balancing of all systems', 'quantity': 1, 'uom': 'LS', 'itemType': 2, 'notes': 'PROVISIONAL SUM: Final scope to be defined at commissioning stage', 'sortOrder': 6},

    # Finishing Works (3.1 - 3.4)
    {'sectionId': FINISH, 'itemNumber': '3.1', 'description': 'Porcelain floor tiling (600x600mm rectified) including screed bed, adhesive, and grouting', 'quantity': 8500, 'uom': 'm2', 'itemType': 0, 'notes': 'Anti-slip R10 rating for common areas', 'sortOrder': 1},
    {'sectionId': FINISH, 'itemNumber': '3.2', 'description': 'Gypsum board suspended false ceiling with access panels and integrated lighting provisions', 'quantity': 6200, 'uom': 'm2', 'itemType': 0, 'notes': 'Moisture-resistant type in wet areas', 'sortOrder': 2},
    {'sectionId': FINISH, 'itemNumber': '3.3', 'description': 'Interior painting - primer and 3 coats of premium emulsion paint to walls and ceilings', 'quantity': 15000, 'uom': 'm2', 'itemType': 0, 'notes': 'Jotun or approved equivalent', 'sortOrder': 3},
    {'sectionId': FINISH, 'itemNumber': '3.4', 'description': 'Aluminum and glass curtain wall system including structural glazing and weather seals', 'quantity': 3800, 'uom': 'm2', 'itemType': 0, 'notes': 'Double-glazed low-E glass, U-value < 1.9 W/m2K', 'sortOrder': 4},

    # External Works (4.1 - 4.4)
    {'sectionId': EXT, 'itemNumber': '4.1', 'description': 'Interlocking concrete paver roads, parking areas, and pedestrian walkways with sub-base', 'quantity': 4200, 'uom': 'm2', 'itemType': 0, 'notes': '80mm thick for vehicular areas, 60mm for walkways', 'sortOrder': 1},
    {'sectionId': EXT, 'itemNumber': '4.2', 'description': 'Reinforced concrete boundary wall (2.4m high) with decorative stone cladding and steel railing', 'quantity': 620, 'uom': 'lm', 'itemType': 0, 'notes': 'Per municipality approved design', 'sortOrder': 2},
    {'sectionId': EXT, 'itemNumber': '4.3', 'description': 'Soft landscaping including topsoil, turf, trees, shrubs, and automatic irrigation system', 'quantity': 2500, 'uom': 'm2', 'itemType': 0, 'notes': 'Drought-resistant species per landscape plan', 'sortOrder': 3},
    {'sectionId': EXT, 'itemNumber': '4.4', 'description': 'External lighting - LED pole lights, bollard lights, facade lighting, and control system', 'quantity': 1, 'uom': 'LS', 'itemType': 0, 'notes': 'Energy-efficient LED with smart controls', 'sortOrder': 4},
]

url = f'http://localhost:5000/api/tenders/{TENDER}/boq/items'
success = 0
fail = 0

for item in items:
    try:
        data = json.dumps(item).encode()
        req = urllib.request.Request(url, data=data, headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        })
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        if result.get('success'):
            success += 1
            print(f'OK: {item["itemNumber"]} - {item["description"][:50]}')
        else:
            fail += 1
            print(f'FAIL: {item["itemNumber"]} - {result}')
    except Exception as e:
        fail += 1
        print(f'ERROR: {item["itemNumber"]} - {e}')

print(f'\n=== SUMMARY: {success} created, {fail} failed ===')
