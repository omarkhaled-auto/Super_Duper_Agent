-- BIDDER 3: Joud Emirates Build - OUTLIER pricing (~785M AED)
-- Strategy: Very low on some high-value items (front-loading risk), very high on others
-- Deliberate outliers marked with is_outlier=true
INSERT INTO bid_pricing (id, bid_submission_id, boq_item_id, bidder_item_number, bidder_description, bidder_quantity, bidder_uom, native_unit_rate, native_amount, native_currency, normalized_unit_rate, normalized_amount, fx_rate_applied, match_type, match_confidence, is_included_in_total, is_outlier, outlier_severity, deviation_from_average, created_at)
VALUES
-- OUTLIER HIGH: Site establishment 3x average (front-loading)
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', 'da0fcb19-0a3c-42fe-9607-3d201516aa9d', '1.1', 'Site establishment', 1, 'LS', 25000000, 25000000, 'AED', 25000000, 25000000, 1.0, 'Exact', 100, true, true, 'High', 173.17, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '27aff901-0cd9-4bd4-8b0f-33632013780a', '1.2', 'Insurance CAR', 1, 'LS', 5500000, 5500000, 'AED', 5500000, 5500000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
-- OUTLIER HIGH: Performance bond 2.5x average
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '5527d534-e2af-4154-8d8a-5fc4439df09d', '1.3', 'Performance bond', 1, 'LS', 18000000, 18000000, 'AED', 18000000, 18000000, 1.0, 'Exact', 100, true, true, 'Medium', 136.84, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '74c02597-c336-491f-a0c6-ea4efb2330a2', '1.4', 'Tower crane (2 nos)', 24, 'month', 300000, 7200000, 'AED', 300000, 7200000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '3f5ee6d3-032c-4571-9c51-dda0a14671eb', '1.5', 'Construction hoist (3 nos)', 24, 'month', 195000, 4680000, 'AED', 195000, 4680000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
-- OUTLIER LOW: Excavation at 50% below average (buying work)
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '83d8a79d-36af-4d59-97a8-3e1b41a8f96c', '2.1', 'Excavation', 45000, 'm3', 45, 2025000, 'AED', 45, 2025000, 1.0, 'Exact', 100, true, true, 'High', -50.00, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '5d44f5d7-c235-4349-98d2-910ddea636ca', '2.2', 'Diaphragm wall', 8500, 'm2', 2950, 25075000, 'AED', 2950, 25075000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', 'e76b9c95-ae01-4ea5-bf6e-ee1ce25df7bf', '2.3', 'Bored piles', 120, 'nos', 155000, 18600000, 'AED', 155000, 18600000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '63b995f9-b0b2-4c38-84a4-a63c45b7dd1c', '2.4', 'Pile caps', 3200, 'm3', 3400, 10880000, 'AED', 3400, 10880000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', 'd94db8b0-80aa-4c54-9771-2a42ec33a6dc', '2.5', 'Raft foundation', 4500, 'm3', 4500, 20250000, 'AED', 4500, 20250000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
-- OUTLIER LOW: Waterproofing at 40% below (cutting corners risk)
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '7129f83b-5010-4f0e-9053-b87410c9ba74', '2.6', 'Waterproofing', 12000, 'm2', 175, 2100000, 'AED', 175, 2100000, 1.0, 'Exact', 100, true, true, 'Medium', -40.68, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '9e77416a-19f1-4715-be7b-9a435cc90586', '3.1', 'Core wall concrete', 18000, 'm3', 4000, 72000000, 'AED', 4000, 72000000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '7a64ab8e-39a1-4790-8a3b-8d2ca4556427', '3.2', 'Column concrete', 8500, 'm3', 3700, 31450000, 'AED', 3700, 31450000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '833409bc-629d-4769-a6a7-ceb4b15de57e', '3.3', 'PT flat slab', 95000, 'm2', 450, 42750000, 'AED', 450, 42750000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
-- OUTLIER HIGH: Transfer slab 45% above average (padding)
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', 'f2b9596e-9eff-46d6-8be4-8ab8face9544', '3.4', 'Transfer slab', 2800, 'm3', 8500, 23800000, 'AED', 8500, 23800000, 1.0, 'Exact', 100, true, true, 'High', 45.30, NOW()),
-- OUTLIER LOW: Rebar significantly below market
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '06aabd49-ee4f-47a5-bda0-0bd876bcd8d7', '3.5', 'Rebar Grade 500B', 22000, 'ton', 2400, 52800000, 'AED', 2400, 52800000, 1.0, 'Exact', 100, true, true, 'High', -29.41, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', 'ab529a59-685f-41a8-94fa-2ec44b06b9d4', '3.6', 'Formwork system', 185000, 'm2', 118, 21830000, 'AED', 118, 21830000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', 'c7634747-2656-4bd9-b89e-2d7d4ae7135d', '4.1', 'Structural steel outrigger', 2400, 'ton', 15200, 36480000, 'AED', 15200, 36480000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', 'ca89b6b7-71ff-4bb2-9f3d-91108e5ea9d6', '4.2', 'Steel roof helipad', 850, 'ton', 12800, 10880000, 'AED', 12800, 10880000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '3c56f820-4f70-420e-b3fd-8ab17dc165d0', '4.3', 'Misc steel', 1200, 'ton', 9000, 10800000, 'AED', 9000, 10800000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
-- OUTLIER HIGH: HVAC 40% above (specialist trade markup)
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '0a26775f-3b0d-4bca-9b16-831667438474', '5.1', 'HVAC chiller plant', 4, 'nos', 6300000, 25200000, 'AED', 6300000, 25200000, 1.0, 'Exact', 100, true, true, 'High', 40.00, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '82455cb7-b304-4d87-9942-7c0a464ef3fb', '5.2', 'AHU and FCU', 1, 'lot', 19500000, 19500000, 'AED', 19500000, 19500000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '5f7dc11f-8307-4103-8004-a6822b561d7d', '5.3', 'Plumbing drainage', 60, 'nos', 175000, 10500000, 'AED', 175000, 10500000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '8a176be2-c72c-4d3b-b115-2a47f8f04b33', '5.4', 'Fire fighting', 95000, 'm2', 130, 12350000, 'AED', 130, 12350000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
-- OUTLIER LOW: Elevators 35% below (suspect quality/brand)
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', 'cbb03225-9ac6-41f9-b4e5-2bd558af6c40', '5.5', 'Elevators 24 units', 24, 'nos', 950000, 22800000, 'AED', 950000, 22800000, 1.0, 'Exact', 100, true, true, 'High', -34.48, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '75ffd3a1-ab8c-4f7f-849f-f5986b6e2195', '6.1', 'HV/LV switchgear', 4, 'nos', 3400000, 13600000, 'AED', 3400000, 13600000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '3d101b31-edd2-40a5-b0d4-335a5a23d96d', '6.2', 'Diesel generators', 2, 'nos', 4000000, 8000000, 'AED', 4000000, 8000000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '9908a3da-b7d5-4479-a5b6-50c2b3628b31', '6.3', 'Electrical distribution', 1, 'lot', 13000000, 13000000, 'AED', 13000000, 13000000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '544794ba-4676-4e45-9ecd-8dd840639f3e', '6.4', 'Lighting small power', 95000, 'm2', 145, 13775000, 'AED', 145, 13775000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', 'd1736800-d2cb-4d78-a398-c6ddb3f72d33', '6.5', 'BMS ELV IT', 1, 'lot', 15200000, 15200000, 'AED', 15200000, 15200000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
-- OUTLIER HIGH: Curtain wall 50% above (premium facade bid)
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', 'c070e7fd-a411-48b8-9ed1-6420d12086f2', '7.1', 'Curtain wall', 42000, 'm2', 2100, 88200000, 'AED', 2100, 88200000, 1.0, 'Exact', 100, true, true, 'High', 47.37, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', 'b5a4449b-5cc1-41b3-ae2c-2f3f7134591a', '7.2', 'ACP cladding', 5500, 'm2', 680, 3740000, 'AED', 680, 3740000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
-- OUTLIER LOW: Crown feature at 40% below (cut scope risk)
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '378ede39-7a7e-4910-907f-7530a4059017', '7.3', 'Crown feature', 1, 'LS', 7800000, 7800000, 'AED', 7800000, 7800000, 1.0, 'Exact', 100, true, true, 'Medium', -41.13, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '8cd5a293-1bec-48df-926c-4bce751efd3b', '8.1', 'Lobby fit-out', 3500, 'm2', 3400, 11900000, 'AED', 3400, 11900000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '4e3466a1-9e42-4f6f-9be1-a266eaa79f4f', '8.2', 'Residential fit-out', 78000, 'm2', 195, 15210000, 'AED', 195, 15210000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', 'aace6482-fbac-484a-acbd-1e2f4d75623a', '8.3', 'Raised floor ceiling', 12000, 'm2', 450, 5400000, 'AED', 450, 5400000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '652282ba-fdbc-45c5-9207-543e5f14cea9', '8.4', 'Internal painting', 180000, 'm2', 48, 8640000, 'AED', 48, 8640000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '6dd254de-347c-44e1-bfc4-847f580c42de', '9.1', 'Hardscaping', 8000, 'm2', 480, 3840000, 'AED', 480, 3840000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '3a6aafeb-bd1d-453c-b499-c8566a9795e1', '9.2', 'Soft landscaping', 4500, 'm2', 350, 1575000, 'AED', 350, 1575000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '27e1e3af-dd2e-4ecd-8a3f-9d8ec2bffe33', '9.3', 'Swimming pools', 2, 'nos', 4500000, 9000000, 'AED', 4500000, 9000000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '77171301-ff5f-4f6c-be55-5da345077522', '10.1', 'Authority fees', 1, 'LS', 16500000, 16500000, 'AED', 16500000, 16500000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', '03293089-cf11-45c3-af4c-27989aab3457', '10.2', 'Design consultancy', 1, 'LS', 13000000, 13000000, 'AED', 13000000, 13000000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW()),
(gen_random_uuid(), '33333333-cccc-4000-8000-000000000003', 'be342df0-333a-414e-b649-5622685091e9', '10.3', 'Contingency 5%', 1, 'LS', 38000000, 38000000, 'AED', 38000000, 38000000, 1.0, 'Exact', 100, true, false, NULL, NULL, NOW());

UPDATE bid_submissions SET native_total_amount = (SELECT SUM(native_amount) FROM bid_pricing WHERE bid_submission_id = '33333333-cccc-4000-8000-000000000003'), normalized_total_amount = (SELECT SUM(normalized_amount) FROM bid_pricing WHERE bid_submission_id = '33333333-cccc-4000-8000-000000000003') WHERE id = '33333333-cccc-4000-8000-000000000003';
