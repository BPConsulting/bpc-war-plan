# INTRIX Module Reference

## Repos

| Repo | Purpose |
|------|---------|
| `github.com/BPConsulting/bpc-intrix-modules` | All INTRIX client modules |
| `github.com/BPConsulting/bpc-avp-modules` | AVP client modules |
| `github.com/BPConsulting/bpc-site-modules` | BPC site/shared modules |
| `github.com/BPConsulting/bpc-war-plan` | War plan, rules, module reference |

---

## bpc-intrix-modules — complete module list

| Module | Description | Status |
|--------|-------------|--------|
| `bpc19_intrix_attendance_portal` | GPS check-in portal, device locking, WIO/OOO, Haversine | Production |
| `BPC19_INTRIX_Company` | Company-level config | Production |
| `bpc19_intrix_data_certification` | Token-based employee data verification, TNC approval workflow | Production |
| `bpc19_intrix_dealer_mgmt` | Dealer agreement lifecycle, tiers, portal | Production |
| `bpc19_intrix_discuss` | WebSocket portal chat replacing Slack for portal users | Production |
| `BPC19_INTRIX_Employees` | Employee custom fields, religion, race, job grade, level | Production |
| `bpc19_intrix_handbook` | Employee handbook portal with TOC and PDF export | Production |
| `bpc19_intrix_helpdesk` | ESS helpdesk with ESS+Attendance teams, public route | Production |
| `BPC19_INTRIX_IoT` | IoT integration | Production |
| `bpc19_intrix_leave` | Leave ESS portal | Production |
| `bpc19_intrix_mfgdemo` | Manufacturing demo module | Production |
| `bpc19_intrix_monitoring` | Multi-dashboard system monitoring with TV rotator | Production |
| `bpc19_intrix_orgchart` | PDF org chart export | Production |
| `bpc19_intrix_payroll` | Malaysian payroll — EPF, SOCSO, EIS, PCB, ITO+ITR structures | Production |
| `bpc19_intrix_permissions` | Permission Matrix App — system-wide admin UI | Production |
| `BPC19_INTRIX_Sequences` | Sequence management | Production |
| `BPC19_INTRIX_Setup` | **Core** — Setup Variables, WhatsApp, Email, Notifications, Traces | Production |
| `BPC19_INTRIX_Statutory` | EPF/SOCSO/EIS/PCB tables, payroll adjustments, sub-groups | Production |
| `BPC19_INTRIX_Tests` | Test utilities | Production |
| `BPC19_INTRIX_Trace` | Communication trace/log system | Production |
| `bpc19_intrix_userguides` | User guides portal | Production |
| `bpc19_intrix_users_tree_extend` | Users tree view extension | Production |
| `bpc19_intrix_woo` | WIO/OOO management, three-layer enforcement | Production |

---

## bpc-avp-modules — complete module list

| Module | Description | Status |
|--------|-------------|--------|
| `avp_base` | CRM stages, contact tags, asset models | Production |
| `avp_mail_force_from` | Force outgoing email through single sender | Production |
| `seeds` | Seed data | Production |

---

## bpc-site-modules — complete module list

| Module | Description | Status |
|--------|-------------|--------|
| `bpc_project_website` | Public project dashboard with Gantt chart and PDF export | Production |
| `bpc_userguide` | BPC-level user guide module | Production |
| `seeds` | Seed data | Production |

---

## Key field locations on hr.employee

| Field | Odoo field name | Location |
|-------|----------------|----------|
| Personal email | `private_email` | `hr.employee` direct |
| Personal phone | `private_phone` | `hr.employee` direct — stored as `60XXXXXXXXX` |
| NRIC | `identification_id` | `hr.version` (current_version_id) |
| Tax number | `stat_tax` | `hr.employee` direct (BPC custom) |
| EPF number | `stat_epf` | `hr.employee` direct (BPC custom) |
| SOCSO number | `stat_socso` | `hr.employee` direct (BPC custom) |
| Handicapped | `handicapped` | `hr.employee` direct (BPC custom) |
| Children under 18 | `pcb_children_ordinary` | `hr.employee` direct (BPC statutory) |
| Children 18+ education | `pcb_children_18plus` | `hr.employee` direct (BPC statutory) |
| Disabled children | `pcb_children_disabled` | `hr.employee` direct (BPC statutory) |
| Birthday | `birthday` | `hr.employee` direct |
| Gender | `sex` | `hr.employee` direct — selection: male/female/other |
| Marital status | `marital` | `hr.version` |
| Street 1 | `private_street` | `hr.version` |
| Street 2 | `private_street2` | `hr.version` |
| City | `private_city` | `hr.version` — stored UPPERCASE |
| ZIP | `private_zip` | `hr.version` |
| State | `private_state_id` | `hr.version` — Many2one res.country.state |
| Religion | `religion_id` | `hr.employee` direct — Many2one hr.employee.religion |
| Race | `race_id` | `hr.employee` direct — Many2one hr.employee.race |
| Bumiputera | `bumiputera` | `hr.employee` direct (BPC custom) |
| Nationality | `nationality_id` | `hr.employee` direct (BPC custom) |
| Bank | via `res.partner.bank` | linked to `work_contact_id` partner |
| Job grade | `job_grade_id` | Many2one hr.employee.job_grade |
| Level | `level_id` | Many2one hr.employee.level |
| EPF employee rate | `epf_employee_id` | Many2one hr.statutory.epfee |
| EPF employer rate | `epf_employer_id` | Many2one hr.statutory.epfer |
| Extra EPF EE | `epf_ee_extra` | Float |
| Extra PCB | `pcb_extra` | Float — voluntary monthly top-up |
| OT eligible | `ot_eligible` | Boolean |
| HRDF liable | `hrdf_liable` | Boolean |

---

## WhatsApp & email patterns

```python
# WhatsApp
self.env['setup.variables'].sudo().send_whatsapp(
    mobile=mobile,           # format: 60XXXXXXXXX
    message=message,
    model_name='model.name',
    employee_id=employee.id,
)

# Email
self.env['setup.variables'].sudo().send_email(
    email_to=recipients_email,
    subject='Subject',
    body_html=body,
    model_name='model.name',
)

# Setup variable lookup
rec = self.env['setup.variables'].sudo().search([('name', '=', 'var_name')], limit=1)
value = rec.val_char  # or val_integer, val_float
```

---

## bpc19_intrix_data_certification — key facts

- Model: `bpc.employee.certification`
- States: `draft` → `sent` → `opened` → `submitted` → `approved` / `rejected`
- Token: `secrets.token_urlsafe(32)` — 43 chars, URL-safe
- Portal route: `/employee/certify/<token>` (auth=public)
- Reject creates new record with `parent_id` FK + auto-sends WhatsApp
- Approve writes directly to `hr.employee` and `hr.version`
- Menu: Employees → Configuration → Data Certification
- Malaysian banks pre-loaded in `data/malaysia_banks.xml`
- Malaysian religions pre-loaded in `data/malaysia_religions_races.xml`
- Race (INTRIX official): CHI, MLY, IND, OTH — **not yet seeded on production**

---

## Payroll — ITO and ITR structures

- ITO salary structure: `bpc19_intrix_payroll/data/salary_structure_ito.xml`
- ITR salary structure: `bpc19_intrix_payroll/data/salary_structure_itr.xml`
- Helpers: `bpc19_intrix_payroll/models/payroll_helpers.py`
- Statutory variables: `bpc.statutory.variable` model (code + value)
- Key codes: `PERSONAL_RELIEF` (9000), `EPF_PCB_ANNUAL_CAP` (4000), `PCB_REBATE_THRESHOLD` (35000), `PCB_REBATE_AMOUNT` (400)
- PCB_EXTRA: **pending** — implement as separate salary rule so it doesn't corrupt YTD

---

## ITO dealer model

Three tiers:
- Solo: 20%
- Gold: 28% (3 units/12mo, MYR 1,500 deposit deducted at units 1 and 3)
- Platinum: 38% (6 units, MYR 2,500 deposit)

30% ITO invoices direct / 70% dealer invoices.
Termination requires Sean's explicit approval.
Multiple same-tier packages allowed per dealer.

---

## HQ coordinates (for GPS/Haversine)
- Default lat: `3.154817`
- Default lng: `101.570061`
- WIO radius default: `25.0` metres
- All configurable via `setup.variables`

---

## MYT timezone
- Always use `pytz.timezone('Asia/Kuala_Lumpur')`
- Server stores UTC, display in MYT

---

## Pending items to track
- Race seed data on production (CHI/MLY/IND/OTH) — `bpc19_intrix_data_certification`
- PCB_EXTRA as separate salary rule — `bpc19_intrix_payroll`
- Feb+Mar payslip validation for ITO0007 and ITO0019
---

## New payroll fields added 20 Apr 2026 (LHDN 2026 compliance)

### hr.employee — Tax Profile (PCB)
| Field | Odoo field name | Type | Default |
|-------|----------------|------|---------|
| PCB Category | `pcb_category` | Selection 1/2/3 | '1' |
| Tax Resident | `is_resident` | Boolean | True |
| Tax Region | `tax_region` | Selection peninsular/east | 'peninsular' |
| Spouse Disabled | `spouse_disabled` | Boolean | False |
| Zakat Monthly | `zakat_monthly` | Float | 0.0 |
| Disabled Children (studying) | `pcb_children_disabled_studying` | Integer | 0 |
| TP3 Taxable Gross | `tp3_taxable_gross` | Float | 0.0 |
| TP3 EPF Paid | `tp3_epf_paid` | Float | 0.0 |
| TP3 PCB Paid | `tp3_pcb_paid` | Float | 0.0 |
| TP3 Zakat Paid | `tp3_zakat_paid` | Float | 0.0 |
| TP3 Deductions | `tp3_deductions` | Float | 0.0 |

### hr.statutory.pcb — LHDN Table 1 B values
| Field | Odoo field name | Type |
|-------|----------------|------|
| B (Cat 1 & 3) | `b_cat1_3` | Float |
| B (Cat 2) | `b_cat2` | Float |

### bpc.employee.tp1.claim — TP1 Deduction Claims
| Field | Odoo field name | Type |
|-------|----------------|------|
| Employee | `employee_id` | Many2one hr.employee |
| Year | `year` | Integer |
| Month | `month` | Integer |
| Category | `category` | Selection C1-C17 |
| Amount | `amount` | Float |
| Approved | `approved` | Boolean |

### Payroll engine methods (payroll_helpers.py)
| Method | Purpose |
|--------|---------|
| `bpc_pcb()` | LHDN 2026 normal remuneration — complete rewrite |
| `bpc_pcb_additional()` | LHDN 2026 bonus 5-step formula — NEW |
| `_bpc_pcb_bracket_lookup()` | Table 1 M/R/B lookup by P and category — NEW |
| `_bpc_tp1_sum_lp()` | TP1 accumulated deductions prior months — NEW |
| `_bpc_tp1_lp1()` | TP1 deductions current month — NEW |