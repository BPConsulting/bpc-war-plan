"""
seed.py
Destructive reseed of Fernando's Odoo To-do (personal kanban ONLY).

Odoo 19 quirk handled here:
  The m2m field personal_stage_type_ids uses an intermediate model
  'project.task.stage.personal' with fields (task_id, user_id, stage_id).
  Writing the m2m directly via XML-RPC fails because user_id isn't
  auto-populated from context. So we write to the intermediate model
  ourselves using set_personal_stage().

Safety guarantees:
  - Uses session.todo_domain_for_stages() which filters project_id=False
    → INTRIX/AVP/MSCCI project tasks are NEVER touched
  - Verifies every current_task has project_id=False before proceeding
  - --dry-run to preview
  - Typed 'SEED BPC WAR ROOM' confirmation
  - Aborts if delete count > 60
"""
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from odoo_client import OdooClient
from session import fetch_personal_stages, todo_domain_for_stages, STAGE_NAMES

CONFIG_PATH = SCRIPTS_DIR / 'config.json'

KEEP_AS_DONE = {
    "ITO+ITR / Townhall talking points + ESS demo flow outline",
    "ITO+ITR / ESS onboarding plan — batches (~20/day), criteria, order",
    "ITO+ITR / Townhall materials — slides, ESS walkthrough, demo flow",
    "ITO+ITR / Employee data certification — first login → TNC validation",
    "ITO+ITR / ESS portal stable + fully tested before townhall",
}

TAGS_NEEDED = ['ITO+ITR', 'ITO', 'AVP', 'BPC', 'MSCCI', 'Personal']


def T(name, tag, stage, deadline=None, description=None, priority='0'):
    return {
        'name': name, 'tag': tag, 'stage': stage,
        'deadline': deadline, 'description': description, 'priority': priority,
    }


MASTER_TASKS = [
    # ========== TODAY ==========
    T("ITO+ITR / Validate Mar 2026 PCB — ITO0007 + ITO0019",
      'ITO+ITR', 'Today', '2026-04-22',
      "Jan and Feb validated against LHDN. Expected: 16.70 for ITO0007 (RM 4000 Cat 1) and 207.50 for ITO0019 (RM 6000 single). Closes Step 1."),
    T("ITO+ITR / Merge develop → main + Cloudpepper production update (post-Mar)",
      'ITO+ITR', 'Today', '2026-04-22',
      "Once Mar validates: merge develop → main, then Cloudpepper production update + upgrade bpc19_intrix_payroll."),
    T("ITO+ITR / Step 2 — hr.employee tax profile extension",
      'ITO+ITR', 'Today', '2026-04-28',
      "Fields: pcb_category, spouse_disabled, zakat_monthly, tax_region, TP3 x4 (prior-employer YTD), TP1 x16 + computed total. Add 'Tax Profile (PCB)' notebook page on hr.employee form."),
    T("ITO+ITR / Rewrite bpc_pcb() per full LHDN spec",
      'ITO+ITR', 'Today', '2026-04-30',
      "Cat 1/2/3 B values. Formula: D+S+DU+SU+QC+sum(LP)+LP1. K2 projection with K1 floor. Z (zakat) subtraction. RM 400 rebate when chargeable <= RM 35,000. Retain YTD reconciliation."),
    T("ITO+ITR / Import script — Tax Category / Zakat / Handicapped / TP3 from Dec 2025 Intrix export",
      'ITO+ITR', 'Today', '2026-04-30',
      "One-shot Python script to populate hr.employee tax profile fields from the Dec 2025 Intrix export file."),
    T("ITO+ITR / PCB_EXTRA as separate salary rule (Option A)",
      'ITO+ITR', 'Today', '2026-05-02',
      "Voluntary top-up isolation. PCB rule only sums statutory PCB in YTD lookup; PCB_EXTRA reads emp.pcb_extra directly. Prevents voluntary top-ups from corrupting statutory PCB YTD."),
    T("ITO+ITR / Race seed data on production (CHI / MLY / IND / OTH)",
      'ITO+ITR', 'Today', '2026-04-28'),
    T("ITO+ITR / Personal data confirmation form (WhatsApp token + single-shot + TNC approval)",
      'ITO+ITR', 'Today', '2026-04-22',
      "Announced at the townhall. Unique token per employee. Form shows current values, accepts updates, one-time submission. Changes go to TNC approval queue before writing to the DB."),
    T("ITO+ITR / Zoom attendance — run setup_townhall_events.py on production",
      'ITO+ITR', 'Today', '2026-04-21',
      "Creates 4 event.event records with 87 pre-registered employees across the townhall sessions."),
    T("ITO+ITR / Zoom attendance CSV imports — after 21 / 22 (x2) / 24 April sessions",
      'ITO+ITR', 'Today', '2026-04-24',
      "After each session: download Zoom Participants CSV and run import_zoom_attendance.py to mark registrations as Attended."),
    T("ITO+ITR / TNC data cleanup — production employee data",
      'ITO+ITR', 'Today', '2026-04-22'),
    T("ITO+ITR / Run copy_prod_to_staging.py once production data is clean",
      'ITO+ITR', 'Today', '2026-04-23'),

    # ========== THIS WEEK ==========
    T("ITO+ITR / Payroll trial runs Jan/Feb/Mar 2026 — validate all figures",
      'ITO+ITR', 'This Week', '2026-05-02',
      "After Step 2 lands and Odoo PCB matches Intrix 170.85 for ITO0019 (Cat 2 married, non-working spouse), run full trial for all employees across EPF / SOCSO / EIS / PCB / net pay."),
    T("ITO+ITR / Payslip print template design",
      'ITO+ITR', 'This Week', '2026-05-04'),
    T("ITO+ITR / EPF / SOCSO / EIS / LHDN contribution file exports",
      'ITO+ITR', 'This Week', '2026-05-04'),
    T("ITO+ITR / PBB payment file export",
      'ITO+ITR', 'This Week', '2026-05-04'),
    T("ITO+ITR / TNC payroll + employee dump reports",
      'ITO+ITR', 'This Week', '2026-05-04'),
    T("ITO+ITR / ESS feature visibility controls — hide leave+payslips for launch",
      'ITO+ITR', 'This Week', '2026-04-24'),
    T("ITO+ITR / ESS — attendance + WIO only visible at launch",
      'ITO+ITR', 'This Week', '2026-04-24'),
    T("ITO+ITR / boolean_toggle fix — sweep all views",
      'ITO+ITR', 'This Week', '2026-04-24'),
    T("ITO+ITR / TNC new-employee onboarding checklist",
      'ITO+ITR', 'This Week', '2026-04-25'),
    T("ITO+ITR / TNC resigned-employee offboarding checklist",
      'ITO+ITR', 'This Week', '2026-04-25'),
    T("ITO / Dealer portal desktop redesign",
      'ITO', 'This Week', '2026-04-30'),
    T("ITO / Dealer new-agreement button bug — fix",
      'ITO', 'This Week', '2026-04-23'),
    T("ITO / SO deposit separation — implement based on finance decision",
      'ITO', 'This Week', '2026-04-23'),
    T("ITO / Dealer portal RRP + commission breakdown",
      'ITO', 'This Week', '2026-04-30'),
    T("ITO / Dealer configurable date parameters (via Setup Variable)",
      'ITO', 'This Week', '2026-04-30'),
    T("ITO+ITR / Helpdesk queues setup",
      'ITO+ITR', 'This Week', '2026-04-30'),
    T("ITO+ITR / Helpdesk — ESS ticket creation from portal",
      'ITO+ITR', 'This Week', '2026-04-30'),
    T("ITO+ITR / GPS double clock-in entry glitch fix",
      'ITO+ITR', 'This Week', '2026-05-04'),
    T("ITO+ITR / Auto clock-out hours subtraction fix",
      'ITO+ITR', 'This Week', '2026-05-04',
      "Auto clock-out should subtract already-worked hours that day before adding standard_hours. E.g. if employee already worked 3:06, auto checkout = last_checkin + (9:00 - 3:06)."),
    T("ITO+ITR / OT request flow — advance approval + orgchart + auto cash vs leave",
      'ITO+ITR', 'This Week', '2026-05-04'),
    T("ITO+ITR / Leave flow ESS",
      'ITO+ITR', 'This Week', '2026-05-04'),
    T("ITO+ITR / Per-employee comms preferences",
      'ITO+ITR', 'This Week', '2026-05-04'),
    T("ITO+ITR / Editable WhatsApp / email message templates",
      'ITO+ITR', 'This Week', '2026-05-04'),
    T("AVP / AVP dual CRM/Sales — design decision (own vs managed-on-behalf)",
      'AVP', 'This Week', '2026-04-28'),
    T("AVP / AVP dual CRM build — implement agreed design",
      'AVP', 'This Week', '2026-05-02'),
    T("AVP / AVP logbook Phase 1 — avp.logbook model",
      'AVP', 'This Week', '2026-04-30',
      "Fields: title, body, tags, category, author, date. Clean API for Phase 2 AI/BI consumption."),

    # ========== NEXT WEEK ==========
    T("BPC / BPC own Odoo Git migration",
      'BPC', 'Next Week', '2026-05-01'),
    T("BPC / Module renames (fix uppercase) — all 18 BPC modules",
      'BPC', 'Next Week', '2026-05-02'),
    T("ITO+ITR / Dealer flow reorganization (multi-company)",
      'ITO+ITR', 'Next Week', '2026-05-04'),
    T("ITO / HubSpot data import",
      'ITO', 'Next Week', '2026-05-04'),
    T("ITO / Test import of Slack conversations",
      'ITO', 'Next Week', '2026-05-04'),
    T("ITO / iPay88 integration",
      'ITO', 'Next Week', '2026-05-04'),

    # ========== LATER ==========
    T("MSCCI / MSCCI ongoing development",
      'MSCCI', 'Later'),
    T("AVP / AVP logbook Phase 2 — AI/BI layer",
      'AVP', 'Later', description="Anthropic API query layer + Odoo data BI."),
    T("ITO+ITR / Avatar fallback (SVG white-on-white — cosmetic)",
      'ITO+ITR', 'Later'),
    T("ITO+ITR / Medical/hospitalization leave escalation window per leave type",
      'ITO+ITR', 'Later'),
    T("ITO+ITR / Retroactive leave (allow Medical, block Annual)",
      'ITO+ITR', 'Later'),
    T("ITO+ITR / GPS ghost records (0-second attendances) prevention / auto-delete",
      'ITO+ITR', 'Later'),
    T("ITO+ITR / Video handbook",
      'ITO+ITR', 'Later'),
    T("ITO+ITR / Discuss channels config",
      'ITO+ITR', 'Later'),
    T("ITO+ITR / Orgchart",
      'ITO+ITR', 'Later'),
    T("BPC / bpc_kickstart — Odoo post-install wizard for Malaysian SMEs",
      'BPC', 'Later'),
    T("BPC / Timber Plank Vision App — mobile + Odoo CV integration",
      'BPC', 'Later'),
    T("BPC / BPC Odoo TV Dashboard (productise monitoring module)",
      'BPC', 'Later'),
    T("BPC / Apple TV native app (Phase 2, Q3 2026 earliest)",
      'BPC', 'Later'),
    T("Personal / New property — network infrastructure plan (UniFi + HA + cameras)",
      'Personal', 'Later'),
    T("Personal / LED panel lighting spec + supplier shortlist",
      'Personal', 'Later'),
    T("Personal / CAT6A cabling plan",
      'Personal', 'Later'),
    T("Personal / Resell existing TP-Link Deco XE75/XE80 x 4",
      'Personal', 'Later'),
]


# -------------------- personal stage helpers --------------------

def set_personal_stage(c, task_id, stage_id):
    """Set the personal stage for a single task for the current user,
    using the project.task.stage.personal intermediate model directly.
    Writes user_id explicitly (Odoo's m2m write would need it in context)."""
    existing = c.search_read(
        'project.task.stage.personal',
        domain=[('task_id', '=', task_id), ('user_id', '=', c._uid)],
        fields=['id'],
    )
    if existing:
        c.write('project.task.stage.personal', [existing[0]['id']], {
            'stage_id': stage_id,
        })
    else:
        c.create('project.task.stage.personal', {
            'task_id': task_id,
            'user_id': c._uid,
            'stage_id': stage_id,
        })


# -------------------- discovery --------------------

def discover(c):
    open_stage_map = fetch_personal_stages(c)
    missing = [n for n in STAGE_NAMES if n not in open_stage_map]
    if missing:
        print(f"ERROR: missing open personal stages: {missing}")
        print(f"Found: {list(open_stage_map.keys())}")
        return None
    open_stage_ids = list(open_stage_map.values())

    done_stages = c.search_read(
        'project.task.type',
        domain=[('user_id', '=', c._uid), ('name', '=', 'Done')],
        fields=['id', 'name'],
    )
    done_stage_id = done_stages[0]['id'] if done_stages else None

    current = c.search_read(
        'project.task',
        domain=todo_domain_for_stages(c._uid, open_stage_ids),
        fields=['id', 'name', 'project_id', 'state'],
    )

    # Defense in depth: verify every task is project-less
    leaks = [t for t in current if t.get('project_id')]
    if leaks:
        print("CRITICAL: filter leak — tasks with project_id set got through.")
        for t in leaks[:5]:
            print(f"   project={t['project_id']}  task={t['name']}")
        return None

    return {
        'open_stages': open_stage_map,
        'done_stage_id': done_stage_id,
        'current_tasks': current,
    }


def ensure_tags(c):
    existing = c.search_read(
        'project.tags',
        domain=[('name', 'in', TAGS_NEEDED)],
        fields=['id', 'name'],
    )
    by_name = {t['name']: t['id'] for t in existing}
    for name in TAGS_NEEDED:
        if name not in by_name:
            new_id = c.create('project.tags', {'name': name})
            by_name[name] = new_id
            print(f"   created tag: {name} (id={new_id})")
    return by_name


def show_preview(disc, tag_by_name):
    print(f"Current OPEN To-do:      {len(disc['current_tasks'])} project-less tasks in 5 open stages")
    print(f"Open stages:             {list(disc['open_stages'].keys())}")
    print(f"Done stage:              {'yes (id=' + str(disc['done_stage_id']) + ')' if disc['done_stage_id'] else 'not found — will fall back to state=1_done'}")
    print(f"Tags:                    {list(tag_by_name.keys())}")
    print()

    to_done = [t for t in disc['current_tasks']
               if t['name'].strip() in KEEP_AS_DONE]
    to_delete = [t for t in disc['current_tasks'] if t not in to_done]

    print(f"MOVE TO DONE ({len(to_done)}):")
    for t in to_done:
        print(f"   {t['name']}")
    if len(to_done) < len(KEEP_AS_DONE):
        missing = KEEP_AS_DONE - {t['name'].strip() for t in to_done}
        print(f"\n   (NOT FOUND in current open tasks — will be skipped:)")
        for name in missing:
            print(f"   !  {name}")

    print(f"\nDELETE ({len(to_delete)}):")
    for t in to_delete[:15]:
        print(f"   {t['name']}")
    if len(to_delete) > 15:
        print(f"   ... and {len(to_delete) - 15} more")

    print(f"\nCREATE ({len(MASTER_TASKS)}):")
    by_stage = {}
    for spec in MASTER_TASKS:
        by_stage.setdefault(spec['stage'], []).append(spec)
    for stage in STAGE_NAMES:
        count = len(by_stage.get(stage, []))
        print(f"   {stage:<12} {count} tasks")


# -------------------- main --------------------

def run(dry_run=False):
    print("=" * 60)
    print("BPC WAR ROOM — DESTRUCTIVE RESEED")
    print("=" * 60)
    print()

    c = OdooClient(CONFIG_PATH)
    c.connect()
    print(f"Connected to {c.url}, uid={c._uid}\n")

    disc = discover(c)
    if disc is None:
        sys.exit(1)
    tag_by_name = ensure_tags(c)

    print()
    show_preview(disc, tag_by_name)
    print()

    if dry_run:
        print("DRY RUN — nothing changed. Run without --dry-run to apply.")
        return

    to_delete_count = len([t for t in disc['current_tasks']
                           if t['name'].strip() not in KEEP_AS_DONE])
    if to_delete_count > 60:
        print(f"SAFETY CHECK: {to_delete_count} tasks would be deleted.")
        print("That is higher than expected (~33). Abort.")
        sys.exit(1)

    confirm = input("\nType 'SEED BPC WAR ROOM' (exact) to proceed: ").strip()
    if confirm != 'SEED BPC WAR ROOM':
        print("Aborted.")
        return

    # 1. Move keep-as-done to Done personal stage
    print("\n[1/3] Moving keep-as-done tasks to Done personal stage...")
    done_task_ids = [t['id'] for t in disc['current_tasks']
                     if t['name'].strip() in KEEP_AS_DONE]
    if done_task_ids:
        if disc['done_stage_id']:
            for tid in done_task_ids:
                set_personal_stage(c, tid, disc['done_stage_id'])
            print(f"       Moved {len(done_task_ids)} to Done stage (id={disc['done_stage_id']})")
        else:
            c.write('project.task', done_task_ids, {'state': '1_done'})
            print(f"       No Done stage; set state=1_done on {len(done_task_ids)}")
    else:
        print("       No matches (check titles)")

    # 2. Delete remaining open tasks
    print("\n[2/3] Deleting remaining open tasks...")
    to_delete = [t['id'] for t in disc['current_tasks']
                 if t['id'] not in done_task_ids]
    if to_delete:
        c.unlink('project.task', to_delete)
        print(f"       Deleted: {len(to_delete)}")
    else:
        print("       Nothing to delete")

    # 3. Create new tasks (two-step: create task, then set personal stage)
    print(f"\n[3/3] Creating {len(MASTER_TASKS)} new tasks...")
    created = 0
    failed = 0
    for spec in MASTER_TASKS:
        # Build task vals WITHOUT personal_stage_type_ids
        # (that m2m field has the user_id-required quirk over XML-RPC)
        vals = {
            'name': spec['name'],
            'user_ids': [(6, 0, [c._uid])],
            'tag_ids': [(6, 0, [tag_by_name[spec['tag']]])],
            'priority': spec.get('priority', '0'),
        }
        if spec.get('deadline'):
            vals['date_deadline'] = spec['deadline']
        if spec.get('description'):
            vals['description'] = spec['description']
        try:
            new_id = c.create('project.task', vals)
            # Now set the personal stage via the intermediate model
            set_personal_stage(c, new_id, disc['open_stages'][spec['stage']])
            created += 1
        except Exception as e:
            failed += 1
            print(f"       FAILED: {spec['name'][:60]}...")
            print(f"               -> {e}")
    print(f"       Created: {created}, failed: {failed}")

    print("\n" + "=" * 60)
    print("SEED DONE. Check Odoo To-do now.")
    print("=" * 60)
    print("\nNext:")
    print("   session pull")
    print("   session close")


def main():
    dry = '--dry-run' in sys.argv or '-n' in sys.argv
    run(dry_run=dry)


if __name__ == '__main__':
    main()
