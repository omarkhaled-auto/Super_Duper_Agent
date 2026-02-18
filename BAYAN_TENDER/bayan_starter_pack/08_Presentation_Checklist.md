# Bayan E2E Presentation Checklist

## Pre-Presentation Setup
- [ ] Bayan application is running and accessible
- [ ] All starter pack files are downloaded and accessible
- [ ] Test user accounts are ready (TenderManager, CommercialAnalyst, etc.)
- [ ] Browser is set up (Chrome recommended)

## Demo Flow

### Phase 1: Tender Creation (5 min)
- [ ] Log in as Tender Manager
- [ ] Click "Create Tender"
- [ ] Fill in details from `06_Tender_Details.md`
  - Title: Construction of Commercial Office Building - Plot C7, Al Reem Island
  - Type: Selective
  - Currency: AED
  - Estimated Value: 45,000,000
  - Dates: Issue=Mar 1, Clarification=Mar 15, Submission=Apr 1, Opening=Apr 2
  - Tech Weight: 40%, Commercial Weight: 60%
- [ ] Save as Draft

### Phase 2: BOQ Upload (3 min)
- [ ] Navigate to BOQ tab
- [ ] Click "Import BOQ"
- [ ] Upload `02_BOQ_Master_No_Prices.xlsx`
- [ ] Review auto-detected column mapping
  - Bill No. -> BillNumber
  - Item No. -> ItemNumber
  - Sub-Item -> SubItem
  - Description -> Description
  - Qty -> Quantity
  - Unit -> Uom
- [ ] Select Pricing Level: **SubItem** (3-level hierarchy)
- [ ] Validate (should show 0 errors)
- [ ] Import and verify hierarchy: 8 bills, ~26 items, ~80 sub-items
- [ ] Show visual hierarchy in BOQ viewer (dark blue bills, light blue groups, indented sub-items)

### Phase 3: Evaluation Criteria (2 min)
- [ ] Navigate to Evaluation tab
- [ ] Add criteria matching `04_Evaluation_Criteria.xlsx`:
  - Compliance: 20%
  - Methodology: 20%
  - Team CVs: 15%
  - Program: 15%
  - QA/QC: 15%
  - HSE: 15%
- [ ] Total = 100% (validation passes)

### Phase 4: Invite Bidders (2 min)
- [ ] Navigate to Bidders tab
- [ ] Add 3 bidders from `05_Bidder_List.xlsx`
- [ ] Show invitation status

### Phase 5: Publish Tender (1 min)
- [ ] Click "Publish" to move from Draft -> Active
- [ ] Show tender is now live

### Phase 6: Bid Submission (5 min)
- [ ] Navigate to Bids/Submissions section
- [ ] Import Bidder A: Upload `03_Priced_BOQ_Bidder_A_*.xlsx`
  - Map columns: Bill No., Item No., Sub-Item, Description, Qty, Unit, Unit Rate, Amount
  - Validate: should show 0 errors, formula check passes
  - Import
- [ ] Import Bidder B: Upload `03_Priced_BOQ_Bidder_B_*.xlsx`
  - Same process
- [ ] Import Bidder C: Upload `03_Priced_BOQ_Bidder_C_*.xlsx`
  - Same process
- [ ] Show all 3 bids imported successfully
- [ ] Verify subtotals per bill and grand total

### Phase 7: Technical Evaluation (3 min)
- [ ] Close tender for evaluation (Active -> Evaluation)
- [ ] Navigate to Technical Evaluation
- [ ] Score each bidder on all criteria (sample scores)
- [ ] Lock technical scores

### Phase 8: Commercial Evaluation (2 min)
- [ ] Navigate to Commercial Evaluation
- [ ] Show auto-calculated commercial scores
- [ ] Show price comparison and breakdown by bill

### Phase 9: Combined Scoring (2 min)
- [ ] Navigate to Combined Scorecard
- [ ] Show final rankings
- [ ] Show weighted formula: (Tech x 0.40) + (Commercial x 0.60)

### Phase 10: Award (2 min)
- [ ] Select winning bidder
- [ ] Initiate approval workflow
- [ ] Show award pack generation

## Key Talking Points
1. **3-Level Hierarchy**: Bills > Items > Sub-items with visual differentiation
2. **Auto-detection**: Bayan auto-maps Excel columns by header names
3. **Subtotals**: Group subtotals, bill totals, and grand total auto-calculated
4. **Validation**: Built-in formula validation (Qty x Rate = Amount, 1% tolerance)
5. **Section hierarchy**: Auto-creates from bill/item/sub-item structure
6. **Fair evaluation**: Blind mode separates technical from commercial
7. **Audit trail**: Full activity log and document versioning
8. **Multi-approval**: Sequential approval workflow for awards

## Troubleshooting
| Issue | Solution |
|-------|----------|
| Column not detected | Check header matches keywords exactly |
| Validation errors | Ensure no empty Item No. or Description |
| Formula mismatch | Verify Amount = Qty x Unit Rate (1% tolerance) |
| UOM warning | Use codes from `07_UOM_Reference.xlsx` |
| Import fails | Ensure .xlsx format, max 50MB |
| Hierarchy not shown | Ensure Pricing Level is set to SubItem |
