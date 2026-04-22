#!/usr/bin/env python3
"""
Slack Attachments → Odoo — INTRIX Migration (last 14 days only)
Downloads files from Slack and attaches them to the matching Odoo Discuss messages.

Usage:
    python3 slack_attachments.py

Run from the same directory as slack_export.json (~/Downloads/).
Run AFTER slack_to_odoo_v2.py + timestamp SQL fix.
"""
import base64
import json
import os
import re
import sys
import time
import urllib.request
import xmlrpc.client
from datetime import datetime, timedelta, timezone

# ── CONFIG ──
SLACK_EXPORT = os.path.expanduser("~/Downloads/slack_export.json")
SLACK_TOKEN = "SLACK_TOKEN_HERE"

# STAGING
URL = "https://intrix-staging.bpconsulting.my"
DB = "intrix-staging"
USER = "intrix@bpconsulting.com.my"
PASS = "REPLACE_ME"  # ← paste admin password

DAYS_BACK = 14
DOWNLOAD_DIR = os.path.expanduser("~/Downloads/slack_files")


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


def download_slack_file(url, dest_path):
    """Download a file from Slack — custom opener preserves auth header on redirect."""
    class AuthRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            new_req = urllib.request.Request(newurl, headers={"Authorization": f"Bearer {SLACK_TOKEN}"})
            return new_req

    opener = urllib.request.build_opener(AuthRedirectHandler)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {SLACK_TOKEN}"})
    try:
        with opener.open(req) as resp:
            data = resp.read()
            with open(dest_path, 'wb') as f:
                f.write(data)
            return len(data)
    except Exception as e:
        print(f"    Download error: {e}")
        return 0


def main():
    print(f"Loading {SLACK_EXPORT}...")
    with open(SLACK_EXPORT) as f:
        data = json.load(f)

    cutoff = (datetime.now() - timedelta(days=DAYS_BACK)).timestamp()

    # Collect messages with files in the last 14 days
    to_process = []
    for ch in data['channels']:
        for msg in ch['messages']:
            ts = float(msg.get('ts', '0'))
            if ts >= cutoff and 'files' in msg:
                to_process.append({
                    'channel': ch['name'],
                    'ts': ts,
                    'text': msg.get('text', ''),
                    'user_name': msg.get('user_name', '?'),
                    'files': msg['files'],
                })

    total_files = sum(len(m['files']) for m in to_process)
    print(f"Messages with files (last {DAYS_BACK} days): {len(to_process)}")
    print(f"Total files: {total_files}")

    # Create download directory
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Connect to Odoo
    uid_odoo, models = connect()

    # Build channel name → Odoo channel ID map
    odoo_channels = call(models, uid_odoo, 'discuss.channel', 'search_read',
                         [[('name', 'like', '[Slack]')]],
                         {'fields': ['name', 'id']})
    channel_map = {}
    for ch in odoo_channels:
        # Extract original name: "[Slack] intrixgroup-chitchat" → "intrixgroup-chitchat"
        orig = ch['name'].replace('[Slack] ', '')
        channel_map[orig] = ch['id']
    print(f"Odoo [Slack] channels found: {len(channel_map)}")

    # Process files
    print(f"\n{'='*60}")
    print(f"  DOWNLOADING + ATTACHING FILES")
    print(f"{'='*60}")

    attached = 0
    skipped = 0
    errors = 0
    attachment_links = []  # (message_id, attachment_id) for SQL linking

    for msg_info in sorted(to_process, key=lambda m: m['ts']):
        ch_name = msg_info['channel']
        channel_id = channel_map.get(ch_name)
        if not channel_id:
            skipped += len(msg_info['files'])
            continue

        # Find matching message in Odoo by channel + approximate date
        msg_date_utc = datetime.fromtimestamp(msg_info['ts'], tz=timezone.utc)
        date_str = msg_date_utc.strftime('%Y-%m-%d %H:%M:%S')
        # Search within 2-minute window
        date_from = (msg_date_utc - timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
        date_to = (msg_date_utc + timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')

        odoo_msgs = call(models, uid_odoo, 'mail.message', 'search',
                         [[('model', '=', 'discuss.channel'),
                           ('res_id', '=', channel_id),
                           ('date', '>=', date_from),
                           ('date', '<=', date_to)]],
                         {'limit': 1})
        msg_id = odoo_msgs[0] if odoo_msgs else None

        for file_info in msg_info['files']:
            fname = file_info.get('name', 'unknown')
            furl = file_info.get('url_private_download') or file_info.get('url_private', '')
            fsize = file_info.get('size', 0)
            mimetype = file_info.get('mimetype', 'application/octet-stream')

            if not furl:
                skipped += 1
                continue

            # Download
            safe_name = re.sub(r'[^\w\-. ]', '_', fname)
            dest = os.path.join(DOWNLOAD_DIR, f"{int(msg_info['ts'])}_{safe_name}")

            downloaded = download_slack_file(furl, dest)
            if not downloaded:
                errors += 1
                continue
            time.sleep(0.5)  # rate limit courtesy

            # Read file and base64-encode
            with open(dest, 'rb') as f:
                file_b64 = base64.b64encode(f.read()).decode('ascii')

            # Create ir.attachment in Odoo — always on discuss.channel
            att_vals = {
                'name': fname,
                'datas': file_b64,
                'mimetype': mimetype,
                'res_model': 'discuss.channel',
                'res_id': channel_id,
            }

            try:
                att_id = call(models, uid_odoo, 'ir.attachment', 'create', [att_vals])
                if isinstance(att_id, list):
                    att_id = att_id[0]
                if msg_id:
                    attachment_links.append((msg_id, att_id))
                attached += 1
            except Exception as e:
                print(f"    Attach error ({fname}): {e}")
                errors += 1
                continue

        dt = datetime.fromtimestamp(msg_info['ts']).strftime('%d %b %H:%M')
        n = len(msg_info['files'])
        matched = "✓" if msg_id else "~"
        print(f"  {matched} {dt}  #{ch_name:<35} {n} file(s)")

    print(f"\n{'='*60}")
    print(f"  DONE!")
    print(f"  Files attached:  {attached}")
    print(f"  Files skipped:   {skipped}")
    print(f"  Errors:          {errors}")
    print(f"  Downloaded to:   {DOWNLOAD_DIR}")
    print(f"{'='*60}")

    # Generate SQL to link attachments to messages
    if attachment_links:
        sql_file = os.path.expanduser("~/Downloads/slack_link_attachments.sql")
        with open(sql_file, 'w') as f:
            f.write("-- Link Slack file attachments to their Discuss messages\n")
            f.write("BEGIN;\n")
            for msg_id, att_id in attachment_links:
                f.write(f"INSERT INTO message_attachment_rel (message_id, attachment_id) "
                        f"VALUES ({msg_id}, {att_id}) ON CONFLICT DO NOTHING;\n")
            f.write("COMMIT;\n")
        print(f"\nAttachment linking SQL: {sql_file}")
        print(f"Copy to server and run:")
        print(f"  scp {sql_file} root@odoo19e:/tmp/")
        print(f"  sudo -u odoo psql -d intrix-staging -f /tmp/slack_link_attachments.sql")


if __name__ == '__main__':
    main()
