# BPC Session Rules & Standards

## Session startup
At the start of every session, fetch and read:
1. `war-plan.json` — current task list
2. This file — rules and standards

---

## Communication style
- Treat Fernando as a professional peer, not a beginner
- Be direct and concise — no padding, no excessive apologies
- Casual tone unless writing formal communications
- Never repeat the same instruction back before doing it
- When something is unclear, ask ONE question — not a list
- Always provide a clear `clear` command before every local or server command block so Fernando can copy/paste cleanly back

---

## File delivery rules
- Always provide downloadable files — never code snippets only
- When multiple files change, list exactly which files changed and where they go in the module
- Never send a full zip when only 1-2 files changed
- Output format for changed files: present each file individually

---

## Git & deployment flow
**Always follow this sequence — no shortcuts:**
1. Fix goes to `develop` branch first
2. Deploy and test on staging
3. Only after staging confirms OK: merge to `main` and deploy to production

**Never push directly to `main` without staging test.**

### Git commands — always use specific paths, never `git add -A`:
```bash
clear
cd ~/Projects/bpc-intrix-modules
git add <specific_module>/
git commit -m "type: description"
git push origin develop
```

### Cloudpepper: Update staging (always say this explicitly)

### Server — staging:
```bash
clear
cd /var/odoo/intrix-staging && sudo -u odoo venv/bin/python3 src/odoo-bin \
  -c odoo.conf --no-http --stop-after-init \
  -d intrix-staging \
  --update <module_name>
```
Use `-i` instead of `--update` for first-time installs.

### Server — production:
```bash
clear
cd /var/odoo/intrix && sudo -u odoo venv/bin/python3 src/odoo-bin \
  -c odoo.conf --no-http --stop-after-init \
  -d intrix-production \
  --update <module_name>
```

### Module repo path on server:
- Staging: `/var/odoo/intrix-staging/extra-addons/bpc-intrix-modules.git-69cc93e7af530`
- Production: `/var/odoo/intrix/extra-addons/bpc-intrix-modules.git-69cc946aa729e`

---

## Odoo 19 Enterprise — hard rules

### Views
- Use `<list>` not `<tree>` — `<tree>` is deprecated in Odoo 19
- All boolean fields MUST use `widget="boolean_toggle"` — no exceptions, including list views
- Never use `attrs=` or `states=` — use `invisible=` directly on the element
- Never use `tracking=True` on Selection fields — not supported in Odoo 19
- Never use `expand="0"` on `<group>` in search views — not valid in Odoo 19
- Group By filters in search views: flat `<filter>` elements, no `<group>` wrapper
- `decoration-*` attributes on `<field>` widgets inside `<list>` are not valid — put them on `<list>` only

### Models
- `hr.contract` does not exist — use `hr.version`, wage via `payslip.version_id.wage`
- Odoo 19 renamed `groups_id` → `group_ids`
- `portal.wizard.user`: `in_portal` → `is_portal`, `action_apply` → `action_grant_access`
- `crm.group_crm_salesperson` doesn't exist → use `sales_team.group_sale_salesman`
- `type='json'` deprecated → use `type='jsonrpc'`
- `_sql_constraints` on models → use `model.Constraint` instead (generates warnings)

### Payroll
- Salary rule helpers use `categories`, `contract.wage`, and rule code fields — NOT `self.line_ids` (empty during computation)
- EPF/SOCSO/EIS use `_rule_parameter()` method
- PCB uses cumulative bracket method with `wage_minimum - 1` as floor
- PCB rounds UP to nearest 5 cents: `math.ceil(x * 20) / 20`
- RM 400 rebate applies when chargeable income ≤ RM 35,000

---

## INTRIX look and feel

### Brand colors
- Orange: `#D37D3B`
- Dark blue: `#2c3e50`
- Gray: `#95a5a6`
- Card background: `#f8f9fa`
- Dark headers: `#343a40`

### BPC document colors (UAT/URS docs)
- Navy: `#0C243E`
- Blue: `#44546A`
- Orange: `#F0A948`
- Red: `#DD4939`

### Portal / ESS styling
- Inherits `portal.portal_layout` then injects INTRIX CSS
- CSS variable pattern: `--intrix-orange`, `--intrix-blue`, `--intrix-gray`
- Submit buttons: class `btn-intrix` (orange background)
- Section headers: dark blue background, white text, uppercase, small font
- Cards: white background, `border-radius: 8px`, subtle box-shadow
- Form fields: orange focus border/glow

### Data standards
- Address fields (street, city): always stored and displayed in UPPERCASE
- Phone numbers: always stripped to Malaysian format `60XXXXXXXXX` (no +, -, spaces)
- WhatsApp uses `work_phone` first, falls back to `private_phone`

---

## INTRIX-specific terminology
- Use **TNC** (not HR) for the HR/payroll department in all client-facing text
- Use **ESS** for Employee Self-Service portal
- Use **WIO** (not WFO) for Work in Office
- Use **OOO** for Out of Office

---

## WhatsApp / notifications
- All WhatsApp calls use: `self.env['setup.variables'].sudo().send_whatsapp(mobile=mobile, message=message, model_name=..., employee_id=...)`
- All email calls use: `self.env['setup.variables'].sudo().send_email(email_to=..., subject=..., body_html=..., model_name=...)`
- Both methods log to INTRIX Traces automatically

---

## Menu system (Odoo 19 Enterprise)
- Employees app root menu external ID: find via BPC External IDs tool — do NOT guess
- Known working parent for Employees app submenus: `hr.menu_human_resources_configuration`
- Always verify external IDs using the BPC External IDs tool before using in XML

---

## Module naming
- All BPC modules follow pattern: `bpc19_intrix_<name>` (all lowercase)
- Module display names: `BPC19 INTRIX <Name>`
- `application: False` for all modules (prevents showing in Apps list as standalone)

---

## Production discipline
- Production has 87 real employees and live payroll data
- Never run untested code on production
- Always test on staging first, no exceptions
- Failed installs leave the DB untouched — but don't rely on this as a safety net
