#!/usr/bin/env python3
"""
Slack → Odoo Discuss Import v2 — INTRIX Migration
- Clean text (no HTML garbage)
- User mapping (Slack users → Odoo employees → proper author)
- Skips system messages

Usage:
    python3 slack_to_odoo_v2.py

Run from the same directory as slack_export.json (~/Downloads/).
Delete [Slack] channels from staging before re-running if v1 was already imported.
"""
import json
import os
import re
import sys
import xmlrpc.client
from datetime import datetime

# ── CONFIG ──
SLACK_EXPORT = os.path.expanduser("~/Downloads/slack_export.json")

# STAGING first — switch to production after testing
URL = "https://intrix-staging.bpconsulting.my"
DB = "intrix-staging"
USER = "intrix@bpconsulting.com.my"
PASS = "REPLACE_ME"  # ← paste admin password

# Skip channels with fewer than N messages
MIN_MESSAGES = 1

# Skip system messages
SKIP_SUBTYPES = {'channel_join', 'channel_leave', 'channel_purpose',
                 'channel_topic', 'welcome_party'}


# ══════════════════════════════════════════════════════════
# TEXT CLEANUP
# ══════════════════════════════════════════════════════════

def clean_slack_text(text, users_map):
    """Convert Slack markup to clean plain text."""
    if not text:
        return ''

    # Resolve @mentions: <@U123ABC> → @RealName
    def resolve_mention(match):
        uid = match.group(1)
        name = users_map.get(uid, uid)
        return f"@{name}"
    text = re.sub(r'<@(U[A-Z0-9]+)>', resolve_mention, text)

    # Resolve channel links: <#C123|channel-name> → #channel-name
    text = re.sub(r'<#C[A-Z0-9]+\|([^>]+)>', r'#\1', text)

    # Resolve URLs: <https://example.com|display text> → display text (URL)
    def resolve_url(match):
        url = match.group(1)
        display = match.group(2)
        if display and display != url:
            return f"{display} ({url})"
        return url
    text = re.sub(r'<(https?://[^|>]+)\|([^>]+)>', resolve_url, text)

    # Bare URLs: <https://example.com> → https://example.com
    text = re.sub(r'<(https?://[^>]+)>', r'\1', text)

    # HTML entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&nbsp;', ' ')

    # Slack bold/italic: *bold* → bold, _italic_ → italic
    # Leave as-is for readability in plain text

    # Strip :emoji: to just the name
    text = re.sub(r':([a-z0-9_+-]+):', r'[\1]', text)

    return text.strip()


def ts_to_display(ts_str):
    """Convert Slack timestamp to display string."""
    try:
        dt = datetime.fromtimestamp(float(ts_str))
        return dt.strftime('%d %b %Y %I:%M %p')
    except (ValueError, TypeError):
        return ''


# ══════════════════════════════════════════════════════════
# USER MAPPING
# ══════════════════════════════════════════════════════════

def build_user_mapping(models, uid_odoo, slack_users):
    """Match Slack users to Odoo employees by name → return {slack_uid: partner_id}."""

    # Fetch all employees with their partner_id
    employees = call(models, uid_odoo, 'hr.employee', 'search_read',
                     [[]], {'fields': ['name', 'work_email', 'user_id']})

    # Fetch partner_id for each employee (employee → user → partner)
    # Also try employee name → res.partner directly
    partners = call(models, uid_odoo, 'res.partner', 'search_read',
                    [[('employee', '=', True)]], {'fields': ['name', 'id']})

    # Build lookup: lowercase name → partner_id
    name_to_partner = {}
    for p in partners:
        name_to_partner[p['name'].strip().lower()] = p['id']

    # Also index employees by name for fallback
    emp_name_to_partner = {}
    for e in employees:
        # Employee's related partner via user_id
        if e.get('user_id'):
            user_partner = call(models, uid_odoo, 'res.users', 'read',
                              [e['user_id'][0]], {'fields': ['partner_id']})
            if user_partner and user_partner[0].get('partner_id'):
                emp_name_to_partner[e['name'].strip().lower()] = user_partner[0]['partner_id'][0]

    # Merge (user-based takes priority)
    for k, v in emp_name_to_partner.items():
        name_to_partner[k] = v

    # Match Slack users to partners
    mapping = {}  # slack_uid → partner_id
    matched = 0
    unmatched = []

    for slack_uid, slack_name in slack_users.items():
        clean_name = slack_name.strip().lower()

        # Try exact match
        if clean_name in name_to_partner:
            mapping[slack_uid] = name_to_partner[clean_name]
            matched += 1
            continue

        # Try partial match (first + last name in either order)
        found = False
        for odoo_name, partner_id in name_to_partner.items():
            # Check if all words of one name appear in the other
            slack_words = set(clean_name.split())
            odoo_words = set(odoo_name.split())
            if len(slack_words) >= 2 and len(odoo_words) >= 2:
                if slack_words & odoo_words == min(slack_words, odoo_words, key=len):
                    mapping[slack_uid] = partner_id
                    matched += 1
                    found = True
                    break
        if not found:
            unmatched.append((slack_uid, slack_name))

    print(f"  User mapping: {matched} matched, {len(unmatched)} unmatched")
    if unmatched and len(unmatched) <= 20:
        for uid, name in sorted(unmatched, key=lambda x: x[1]):
            print(f"    ? {name}")

    return mapping


# ══════════════════════════════════════════════════════════
# ODOO HELPERS
# ══════════════════════════════════════════════════════════

def connect():
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    uid = common.authenticate(DB, USER, PASS, {})
    if not uid:
        print("ERROR: Authentication failed")
        sys.exit(1)
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
    print(f"Connected to {URL} as uid={uid}")
    return uid, models


def call(models, uid, model, method, *args, **kwargs):
    return models.execute_kw(DB, uid, PASS, model, method, *args, **kwargs)


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def main():
    # Load export
    print(f"Loading {SLACK_EXPORT}...")
    with open(SLACK_EXPORT) as f:
        data = json.load(f)

    slack_users = data['users']
    channels = data['channels']
    active_channels = [ch for ch in channels if len(ch['messages']) >= MIN_MESSAGES]

    total_msgs = sum(len(ch['messages']) for ch in active_channels)
    print(f"Channels: {len(active_channels)} active (of {len(channels)} total)")
    print(f"Messages: {total_msgs}")
    print(f"Slack users: {len(slack_users)}")

    # Connect
    uid_odoo, models = connect()

    # Get admin partner_id (fallback for unmatched users)
    admin_partner = call(models, uid_odoo, 'res.users', 'read',
                         [uid_odoo], {'fields': ['partner_id']})
    admin_partner_id = admin_partner[0]['partner_id'][0]
    print(f"Admin partner_id: {admin_partner_id}")

    # Build user mapping
    print("\nBuilding Slack → Odoo user mapping...")
    user_partner_map = build_user_mapping(models, uid_odoo, slack_users)

    # ── IMPORT ──
    print(f"\n{'='*60}")
    print(f"  IMPORTING CHANNELS + MESSAGES")
    print(f"{'='*60}")

    channels_created = 0
    channels_skipped = 0
    messages_posted = 0
    messages_skipped = 0
    timestamp_fixes = []  # (msg_id, original_utc_datetime) for SQL batch update

    for ch in sorted(active_channels, key=lambda c: c['name']):
        name = ch['name']
        purpose = ch.get('purpose', '')
        channel_name = f"[Slack] {name}"

        # Check if channel already exists
        existing = call(models, uid_odoo, 'discuss.channel', 'search',
                       [[('name', '=', channel_name)]], {'limit': 1})
        if existing:
            channel_id = existing[0]
            channels_skipped += 1
        else:
            vals = {
                'name': channel_name,
                'channel_type': 'channel',
                'description': purpose or f'Imported from Slack #{name}',
            }
            channel_id = call(models, uid_odoo, 'discuss.channel', 'create', [vals])
            channels_created += 1

        # Post messages (oldest first)
        msgs = sorted(ch['messages'], key=lambda m: float(m.get('ts', '0')))
        msg_count = 0

        for msg in msgs:
            subtype = msg.get('subtype', 'regular')
            if subtype in SKIP_SUBTYPES:
                messages_skipped += 1
                continue

            raw_text = msg.get('text', '')
            if not raw_text:
                messages_skipped += 1
                continue

            slack_uid = msg.get('user', '')
            user_name = slack_users.get(slack_uid, slack_uid)
            ts_display = ts_to_display(msg.get('ts', ''))
            clean_text = clean_slack_text(raw_text, slack_users)

            # Determine author
            author_id = user_partner_map.get(slack_uid, admin_partner_id)

            # Build message body — plain text only
            attachments_note = ''
            if 'files' in msg:
                file_names = [f.get('name', '?') for f in msg['files']]
                attachments_note = f"\n📎 {', '.join(file_names)}"

            body = f"{clean_text}{attachments_note}"

            # Original Slack timestamp (UTC)
            try:
                msg_date = datetime.utcfromtimestamp(float(msg.get('ts', '0'))).strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                msg_date = None

            try:
                msg_id = call(models, uid_odoo, 'discuss.channel', 'message_post',
                     [channel_id], {
                         'body': body,
                         'message_type': 'comment',
                         'subtype_xmlid': 'mail.mt_comment',
                         'author_id': author_id,
                     })
                if msg_date and msg_id:
                    # message_post returns a list in XML-RPC
                    real_id = msg_id[0] if isinstance(msg_id, list) else msg_id
                    timestamp_fixes.append((real_id, msg_date))
                msg_count += 1
                messages_posted += 1
            except Exception as e:
                print(f"    ERROR posting to #{name}: {e}")
                messages_skipped += 1
                break

        print(f"  #{name:<40} {msg_count:>4} msgs ({channels_created + channels_skipped}/{len(active_channels)})")

    # ── SUMMARY ──
    print(f"\n{'='*60}")
    print(f"  DONE!")
    print(f"  Channels created:  {channels_created}")
    print(f"  Channels existing: {channels_skipped}")
    print(f"  Messages posted:   {messages_posted}")
    print(f"  Messages skipped:  {messages_skipped}")
    print(f"  Users matched:     {len(user_partner_map)}")
    print(f"  Timestamp fixes:   {len(timestamp_fixes)}")
    print(f"{'='*60}")

    # ── GENERATE SQL for timestamp corrections ──
    if timestamp_fixes:
        sql_file = os.path.expanduser("~/Downloads/slack_fix_timestamps.sql")
        with open(sql_file, 'w') as f:
            f.write("-- Slack import: fix message timestamps to original Slack dates\n")
            f.write("-- Run on staging: sudo -u odoo psql -d intrix-staging -f /tmp/slack_fix_timestamps.sql\n")
            f.write("BEGIN;\n")
            for msg_id, msg_date in timestamp_fixes:
                f.write(f"UPDATE mail_message SET date = '{msg_date}' WHERE id = {msg_id};\n")
            f.write("COMMIT;\n")
        print(f"\nTimestamp fix SQL: {sql_file}")
        print(f"Copy to server and run:")
        print(f"  scp {sql_file} root@odoo19e:/tmp/")
        print(f"  sudo -u odoo psql -d intrix-staging -f /tmp/slack_fix_timestamps.sql")


if __name__ == '__main__':
    main()
