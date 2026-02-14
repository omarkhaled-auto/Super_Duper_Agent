# Bayan Tender — Confirmed Functional Features

**Date:** 2026-02-11
**Updated:** 2026-02-14 (Playwright E2E sessions #3, #4, #5 — 30 new features verified, total 5 sessions)
**Source:** Manual E2E testing + Playwright browser automation (5 sessions)
**Total:** 206 confirmed functional features

---

## Authentication & Login (10)

1. Admin login (admin@bayan.ae)
2. Tender Manager login (tendermgr@bayan.ae)
3. Approver login — Nasser Al-Dosari (approver2@bayan.ae)
4. Approver login — Faisal Al-Qahtani (approver3@bayan.ae)
5. Approver login — Tariq Al-Harbi (approver4@bayan.ae)
6. Approver login — original account (approver@bayan.ae)
7. Portal bidder login — bidder@vendor.ae
8. Portal bidder login — omar@contracting.ae
9. Portal bidder login — info@cubicec.com
10. Logout (admin + portal)
11. Forgot Password page (email input, "Send Reset Link" button) [Playwright-verified]

## Tender Lifecycle (5)

11. Tender creation (CRUD)
12. Tender publishing (Draft → Published)
13. Tender closing (Published → Closed)
14. Bid Opening ceremony (Closed → bids opened)
15. Tender auto-transition to Awarded after final approval

## BOQ & Documents (5)

16. BOQ import from Excel (admin — tender BOQ)
17. BOQ export template download
18. Document upload to folders (tender_documents, drawings, specifications, boq, contract_documents, addenda, other)
19. Document download (streams through API)
20. Master BOQ creation (4 sections, 48 items)

## Bidder Management (5)

21. Bidder creation via UI
22. Bidder editing (prequalification, contact info)
23. Bidder view mode (read-only dialog)
24. Bidder search & filtering
25. Bidder invitation to tender (DB-confirmed)

## Clarifications — Admin (4)

26. View submitted questions with status
27. Answer a question (DraftAnswer flow)
28. Publish Q&A bulletin (auto-approves DraftAnswer, generates PDF, emails bidders)
29. Admin clarification status normalization (integer → string)

## Bid Import Wizard — 5-Step (7)

30. Step 1: Parse Excel file (48 items detected, preview rows shown)
31. Step 2: Map Columns (auto-mapped correctly)
32. Step 3: Match to BOQ (48/48 exact matches)
33. Step 4: Normalize (conversions applied)
34. Step 5: Validate & Import (48 items imported)
35. Second bid import (Cubic Contracting — same wizard, same result)
36. Dual-status tracking: `status='Opened'` (lifecycle) + `import_status='Imported'` (pipeline)

## Evaluation Pipeline (14)

37. Comparable Sheet — single bidder data
38. Comparable Sheet — multi-bidder (2 bidders side-by-side)
39. Evaluation Setup — numeric scoring, blind mode, panel members
40. Technical Scoring — 6 criteria, score input, comment entry
41. Technical Scoring — save scores, persist comments
42. Technical Scoring — final score submission
43. Technical Summary — score matrix display
44. Technical Summary — View Comments dialog
45. Technical Summary — Lock Scores (irreversible)
46. Combined Scorecard — weight configuration (70/30)
47. Combined Scorecard — commercial score auto-calculation
48. Combined Scorecard — multi-bidder ranking with recommendation
49. Sensitivity Analysis — weight sensitivity (9 splits)
50. Generate Award Pack — PDF generation

## Approval Workflow (12)

51. Start Approval — 3-level sequential workflow creation
52. Start Approval — auto-fetches approvers from API
53. Approval — Level 1 approve (with comment)
54. Approval — Level 2 approve (with comment)
55. Approval — Level 3 approve / final approval (with comment)
56. Approval — single approver across all 3 levels (TNR-2025-0001)
57. Approval — 3 different approvers across 3 levels (Tariq → Faisal → Nasser, TNR-2026-0002)
58. Approval — rejection at Level 2 (Faisal rejected)
59. Approval — workflow status transitions: Active → Approved / Rejected
60. Approval — re-initiation after rejection (new workflow created)
61. Approval decision form: Approve / Reject / Return for Revision radio buttons
62. Approval comment field

## Admin Pages (19)

63. User Management — create user (with admin-set password)
64. User Management — edit user (role, name, email)
65. User Management — delete user (with self-deletion guard)
66. User Management — toggle active/inactive
67. User Management — list with pagination, search, role filter
68. User Management — temp password display in toast
69. Client Management — create client (all 12 fields)
70. Client Management — edit client
71. Client Management — view mode (read-only → switch to edit)
72. Client Management — search & filtering
73. Client Management — tender count display
74. Bidder Management — create, edit, view, search (items 21-24)
75. System Settings — General tab (site name, support email, etc.)
76. System Settings — Tender tab (bid validity, currency, etc.)
77. System Settings — Notification tab (email toggles, templates)
78. System Settings — Security tab (session timeout, password policy)
79. System Settings — 38 settings wired to individual DB key-value rows
80. Audit Logs — list with filters
81. Audit Logs — entries verified for PUT operations
122. Audit Logs — advanced filtering (User, Action Type, Entity Type, Date Range, Search) [Playwright-verified]
123. Audit Logs — Export button [Playwright-verified]
124. Tender Wizard — Step 1 Basic Info (Title, Client dropdown, Reference auto-gen, Rich text editor, Type radios, Currency, Validity, Estimated Value) [Playwright-verified]
125. Tender List — advanced filters, search, sort, pagination with 5 real tenders [Playwright-verified]

## Bidder Portal (24)

82. Portal login page
83. Portal tender listing ("Your Tenders")
84. Portal tender card — "Bid Submitted" badge
85. Portal tender card — "Qualified" badge
86. Tab navigation (Documents, Clarifications, Submit Bid)
87. Back to Your Tenders link (arrow icon)
88. Documents tab — file listing grouped by folder category
89. Documents tab — file download (streams through API)
90. Documents tab — Drawings folder with files visible
91. Clarifications tab — Submit Question dialog
92. Clarifications tab — BOQ sections dropdown in question form
93. Clarifications tab — question submission (relatedBoqSection field)
94. Clarifications tab — status display ("Submitted", "Answered", etc.)
95. Clarifications tab — My Questions (persistent across refresh)
96. Clarifications tab — Q&A Bulletins display
97. Clarifications tab — multiple bulletins (2 bulletins verified)
98. Clarifications tab — bulletin PDF download
99. Submit Bid tab — document upload (all 5 categories)
100. Submit Bid tab — bid submission + receipt generation
101. Submit Bid tab — receipt number display (REC-XXXXXXXX-NNNN)
102. Submit Bid tab — receipt PDF download
103. Submit Bid tab — "Already Submitted" card (View Receipt / Back to Tender)
104. Submit Bid tab — bid receipt page (5 documents with file sizes)
105. Portal logout

## Dashboard (8)

106. Dashboard overview — Active Tenders count
107. Dashboard overview — Awarded This Month count
108. Tenders list — status badges (Awarded, etc.)
117. Overview Dashboard — stat cards, recent activity feed [Playwright-verified]
118. Approver Dashboard — pending approvals list, approval history [Playwright-verified]
119. Dashboard error state — error banner with retry button on API failure [Playwright-verified]
120. Unauthorized page — 403 role-based redirect with "Return to Dashboard" [Playwright-verified]
121. Portal Account Activation page — invitation code + set password form [Playwright-verified]

## Cross-Cutting / Infrastructure (8)

109. Angular build succeeds (ng build — 0 errors)
110. .NET API build succeeds (0 errors, 14 pre-existing warnings)
111. Docker Compose — all 7 services running (db, api, ui, minio, redis, mailhog, adminer)
112. PostgreSQL database — all queries verified
113. BCrypt password hashing & verification
114. JWT token generation (admin + portal)
115. File streaming through API (documents, PDFs)
116. Email sending via MailHog (bulletin notifications, invitations)

## Vendor Pricing (4) [Playwright-verified]

126. Vendor Pricing — Priced BOQ tab (imported Excel data, sections, items)
127. Vendor Pricing — Comparison tab (multi-bidder side-by-side pricing)
128. Vendor Pricing — Vendor Search tab (bidder list with currency totals)
129. Vendor Pricing — AED currency formatting (was AEDNaN, now fixed)

## Notification Settings (2) [Playwright-verified]

130. Notification Settings — email notification toggles per event type
131. Notification Settings — save/update preferences

## Portal Extended (6) [Playwright-verified]

132. Portal bidder login — joudbidder1@vendor.ae (Joud Al Khaleej Construction LLC)
133. Portal tenders — welcome banner with company name, tender cards with status
134. Portal documents — layout, nav, "Deadline Passed" status indicator
135. Portal clarifications — Submit Question dialog (Subject, Question with char counter, BOQ Section dropdown, Anonymous checkbox)
136. Portal Submit Bid — "Bid Already Submitted" state with receipt reference
137. Portal Bid Receipt — full details (tender info, bidder info, 5 documents with sizes, Download PDF)

## Tender Details — Deep Verification (15) [Playwright-verified, Session #2]

138. Tender Details — Overview tab (Key Dates, Bidder Status, Tender Info, Timeline, Invited Bidders table, Recent Activity) [Playwright-verified]
139. Tender Details — Bidders tab (3 bidders, sortable columns, action buttons, pagination) [Playwright-verified]
140. Tender Details — Documents tab (search, category filter, upload button, empty state) [Playwright-verified]
141. Tender Details — Clarifications tab (New Internal RFI, Publish Q&A Bulletin, stats, filters) [Playwright-verified]
142. Tender Details — BOQ tab (10 sections, 43 items in hierarchical tree table) [Playwright-verified]
143. Tender Details — Bids tab (3 bids received, amounts, status, file counts, Download All Bids, checkboxes, pagination) [Playwright-verified]
144. Evaluation — Comparable Sheet (3 bidders x 43 items, section/item filters, search, Export to Excel, Hide Outliers, color legend, stats: Max Deviation 173.2%) [Playwright-verified]
145. Evaluation — Setup (locked state, Scoring Method: Numeric 0-10, Blind Mode enabled, Panel Members table: 1 panelist completed) [Playwright-verified]
146. Evaluation — Technical Summary (Raw Scores matrix: panelist x bidder x 5 criteria, Aggregated Scores with rankings, Lock Scores, View Comments) [Playwright-verified]
147. Evaluation — Combined Scorecard (Weight Config 40/60 with Quick Presets, 3-bidder ranking, Recommended Award card, Sensitivity Analysis button, Generate Award Pack, Start Approval) [Playwright-verified]
148. Approval tab — 3-level stepper (Level 1/2/3 all Approved) [Playwright-verified]
149. Approval tab — Approver details (Rashid, Hessa, Sultan Al-Joud with emails, timestamps, comments) [Playwright-verified]
150. Approval tab — Decision History (chronological list with approve badges) [Playwright-verified]
151. Approval tab — Final approval shows award amount (AED 743,605,000) [Playwright-verified]
152. Tender Details — breadcrumb navigation (Home > Tenders > Tender Name) [Playwright-verified]

## Tender Management — Extended (12) [Playwright-verified, Session #2]

153. Tender List — 5 tenders with real data (Joud Tower, Shomoush, The Tower, Cubic Tower, MEP Works) [Playwright-verified]
154. Tender List — Status badges (Draft, Awarded), deadline countdown ("1 days"), estimated values [Playwright-verified]
155. Tender List — Rows per page dropdown, pagination controls [Playwright-verified]
156. Tender Wizard — Step 2 Dates (4 date pickers with Timeline Preview: Issue, Clarification, Submission, Opening) [Playwright-verified]
157. Tender Wizard — Step 3 Criteria (Technical/Commercial weight distribution, 6 default criteria totaling 100%) [Playwright-verified]
158. Tender Wizard — Step 4 Review (complete summary, Save as Draft + Create Tender buttons) [Playwright-verified]
159. Edit Tender — pre-populated wizard with existing data (title, client, reference, description, type, currency, validity, estimated value) [Playwright-verified]
160. Edit Tender — rich text editor with toolbar (Bold, Italic, Underline, Lists, Link) [Playwright-verified]
161. My Bids page — filtered tender list view with full filter panel [Playwright-verified]
162. Saved Tenders page — filtered tender list view [Playwright-verified]
163. Sidebar navigation — Tenders submenu (All Tenders, My Bids, Saved Tenders) [Playwright-verified]
164. Header — profile dropdown (Role display, Home, Notification Settings, User Management, System Settings, Audit Logs, Logout), notifications bell with badge [Playwright-verified]

## Dialog-Level Verification (9) [Playwright-verified, Session #3]

165. Sensitivity Analysis dialog — weight sensitivity chart, 9 splits, export button [Playwright-verified]
166. Bid Details dialog — bidder info, bid amount, status, file list, Download Files button [Playwright-verified]
167. BOQ item context menu — right-click on item row: Edit Item, Delete Item options [Playwright-verified]
168. BOQ Edit Item dialog — pre-populated fields (description, unit, quantity, rate), Save/Cancel [Playwright-verified]
169. BOQ Add Section dialog — Section Name, Description fields, Add Section button [Playwright-verified]
170. BOQ Add Item dialog — Description, Unit dropdown, Quantity, Rate fields, Add Item button [Playwright-verified]
171. New Internal RFI dialog — Subject, Priority dropdown, Assigned To, Message textarea [Playwright-verified]
172. Invite Bidders dialog — bidder search/select, invitation email preview, Send Invitations [Playwright-verified]
173. View Detailed Comments dialog — panelist comments per criteria per bidder, expandable rows [Playwright-verified]

## Dialog & Workflow Deep Verification (21) [Playwright-verified, Sessions #4-5]

174. BOQ Import from Excel dialog — file upload zone, template download link, Import button [Playwright-verified]
175. BOQ Export Template dialog — format selection, section filter, Export button [Playwright-verified]
176. BOQ Section context menu — right-click on section: Edit Section, Delete Section, Add Item options [Playwright-verified]
177. BOQ Edit Section dialog — pre-populated Section Name and Description, Save/Cancel [Playwright-verified]
178. Bid Import BOQ dialog — 5-step wizard (Parse, Map Columns, Match BOQ, Normalize, Validate & Import) [Playwright-verified]
179. Comparable Sheet Settings — bidder filter, section filter, search, Hide Outliers toggle, Export to Excel [Playwright-verified]
180. Initiate Approval Workflow dialog — 3-level approver selection, approver list from API, Start Approval [Playwright-verified]
181. Answer Clarification dialog — question display, "Your Answer" textarea, Save Answer (disabled until text entered) [Playwright-verified]
182. Clarification answer flow — status Submitted → Answered, stats update (Pending/Answered counts), "Ready for bulletin" badge, Edit Answer button [Playwright-verified]
183. Publish Q&A Bulletin Step 1 — select questions table with checkboxes, "select all" header, "N clarification(s) selected" counter [Playwright-verified]
184. Publish Q&A Bulletin Step 2 — Bulletin Number (auto-filled), Issue Date datepicker, Introduction textarea, Closing Notes textarea [Playwright-verified]
185. Publish Q&A Bulletin Step 3 — preview with formatted Q&A, bulletin heading, "Publish & Send" button [Playwright-verified]
186. Upload Document dialog — Category dropdown, Choose File + drag & drop zone ("Drag and drop a file here"), 100MB limit, Upload/Cancel [Playwright-verified]
187. Comparable Sheet — single bidder warning ("Only 1 bidder(s) submitted. Minimum 3 bidders are required") [Playwright-verified]
188. Tender list action buttons — View (eye icon), Edit (pencil, disabled for Awarded tenders), Duplicate (copy icon) [Playwright-verified]
189. Duplicate Tender — URL with ?duplicate=GUID, title appended "(Copy)", all fields cloned, reference blank for re-generation [Playwright-verified]
190. Tender list search — real-time filtering by title/client name (e.g., "Joud" → 1 result) [Playwright-verified]
191. Tender list status filter — Advanced Filters panel with Draft/Active/Evaluation/Awarded/Closed/Cancelled checkboxes [Playwright-verified]
192. Clear All Filters — resets search, status, date range back to full tender list [Playwright-verified]
193. Edit Tender — pre-populated wizard with all existing data (title, client, reference, description, type, currency, validity, estimated value) [Playwright-verified]
194. Tender list — "Showing X to Y of Z tenders" dynamic count reflecting applied filters [Playwright-verified]

## Dashboard & Navigation Deep Verification (10) [Playwright-verified, Session #5]

195. Home redirect — `/home` shows "Redirecting..." spinner, Admin role navigates to `/dashboard` [Playwright-verified]
196. Tender Manager Dashboard — heading "Tender Manager Dashboard", "Welcome back, System!" greeting [Playwright-verified]
197. Dashboard KPI cards — Active Tenders (0), In Evaluation (0), Awarded This Month (4), Overdue Tasks (0) [Playwright-verified]
198. Dashboard quick actions — "New Tender" button (navigates to /tenders/new), "Import Bidders" button [Playwright-verified]
199. Dashboard Active Tenders table — sortable columns (Reference, Title, Client, Status, Bids, Deadline), "View All" navigates to /tenders [Playwright-verified]
200. Dashboard Upcoming Deadlines widget — "Next 7 Days" label, empty state "No upcoming deadlines" [Playwright-verified]
201. Dashboard Recent Activity feed — 9+ real audit entries with user emails, timestamps ("7m ago", "3h ago"), action descriptions [Playwright-verified]
202. Overview Dashboard — 6 KPI stat cards (Total Tenders: 5, Active: 0, Evaluation: 0, Awarded: 4, Pending Approvals: 0, Total Contract Value: 2,440,005,345 SAR) [Playwright-verified]
203. Overview Dashboard — Activity Trend and Award Value Trend chart visualizations [Playwright-verified]
204. Tender list Client filter — searchable dropdown with 3 real clients (Cubic Contracting, Cubic Engineering Consultancy, Joud Tower Development LLC), filters table on selection, clearable [Playwright-verified]
205. Tender list column sorting — clickable headers (Tender Name, Client, Reference, Deadline, Status) with ascending sort, sort indicator icon [Playwright-verified]
206. Audit Logs deep view — 7-column table (Timestamp, User, Action, Entity Type, Entity ID, Changes, IP Address), 5 filters (User, Action Type, Entity Type, Date Range, Search), pagination, Export to Excel [Playwright-verified]

---

## Coverage by Category

| Category | Features Confirmed | Key Highlights |
|----------|-------------------|----------------|
| Authentication | 11 | 9 distinct accounts tested, both admin + portal auth, forgot password |
| Tender Lifecycle | 5 | Full Draft → Published → Closed → Awarded path |
| BOQ & Documents | 5 | Excel import, template export, 7 folder categories |
| Bidder Management | 5 | Full CRUD + view mode + invitation |
| Clarifications (Admin) | 4 | Answer flow, bulletin publishing, enum normalization |
| Bid Import Wizard | 7 | 5-step pipeline, 2 bids imported, 48 items each |
| Evaluation Pipeline | 14 | Full pipeline: comparable → scoring → lock → combined → sensitivity → award pack |
| Approval Workflow | 12 | Approve (3 levels), reject, re-initiate, multi-approver |
| Admin Pages | 23 | Users, Clients, Bidders, Settings (4 tabs), Audit Logs, Tender Wizard, Tender List |
| Bidder Portal | 24 | Documents, Clarifications (bulletins + my questions), Bid submission + receipt |
| Dashboard | 8 | Overview KPIs, approver dashboard, error state, unauthorized page, portal activation |
| Vendor Pricing | 4 | Priced BOQ, Comparison, Vendor Search, AED formatting |
| Notification Settings | 2 | Email toggles, save preferences |
| Portal Extended | 6 | Additional bidder account, tender cards, documents, clarifications dialog, receipt |
| Tender Details (Deep) | 15 | All 8 tabs verified: Overview, Bidders, Documents, Clarifications, BOQ, Bids, Evaluation (4 sub-views), Approval (3-level workflow) |
| Tender Management (Extended) | 12 | Full wizard (4 steps), edit mode, My Bids, Saved, tender list with 5 tenders, sidebar/header nav |
| Infrastructure | 8 | Builds, Docker, DB, JWT, file streaming, email |
| Dialog-Level Verification | 9 | Sensitivity Analysis, Bid Details, BOQ CRUD dialogs, Internal RFI, Invite Bidders, Comments |
| Dialog & Workflow Deep | 21 | BOQ Import/Export, Bulletin 3-step wizard, Answer Clarification, Upload Document, Duplicate Tender, Search/Filter |
| Dashboard & Nav Deep | 12 | Home redirect, Manager Dashboard (KPIs, quick actions, activity feed), Overview Dashboard (6 KPIs, charts), Client filter, column sorting, Audit Logs deep |
| **TOTAL** | **206** | **Across 2 tender lifecycles + 5 Playwright E2E sessions** |
