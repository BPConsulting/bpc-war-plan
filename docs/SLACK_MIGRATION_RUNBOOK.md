# INTRIX Slack → Odoo Discuss Migration — Runbook

**Created:** 22 April 2026
**Author:** BPC (Fernando + Claude)
**Status:** Staging tested, production pending
**Scripts location:** `~/Downloads/` on FCS-StudioBerry

---

## Prerequisites

### Slack App (already created)
- App name: "BPC Migration" at `https://api.slack.com/apps`
- Workspace: intrixgroup.slack.com
- User Token Scopes: `channels:history`, `channels:read`, `groups:history`, `groups:read`, `users:read`, `files:read`
- Token: `SLACK_TOKEN_HERE`
- If token expires: go to the app → OAuth & Permissions → Reinstall to Workspace → copy new token

### Odoo credentials
- Staging: `https://intrix-staging.bpconsulting.my` / DB: `intrix-staging`
- Production: `https://intrix.bpconsulting.my` / DB: `intrix`
- User: `intrix@bpconsulting.com.my`
- Password: (your admin password — edit PASS in each script)

### Scripts (4 files, all in `~/Downloads/`)
1. `slack_export.py` — exports Slack data to JSON
2. `slack_to_odoo_v2.py` — creates Discuss channels + posts messages
3. `slack_attachments.py` — downloads files from Slack + attaches to Odoo
4. Generated SQL files (created automatically by scripts 2 and 3)

---

## STEP 1 — Export Slack Data

**Runs on:** Mac
**Time:** ~2 minutes
**Output:** `~/Downloads/slack_export.json`

```bash
cd ~/Downloads
python3 slack_export.py
```

**What it does:**
- Pulls all channels (public + private) you have access to
- Pulls last 90 days of messages per channel (configurable: `DAYS_BACK`)
- Resolves user IDs to real names
- Saves everything to `slack_export.json`

**Config to change for production run:**
- `DAYS_BACK = 90` — increase if you want more history (e.g., 365 for a full year)
- Token — update if expired

**Expected output:** ~115 channels, ~1,681 messages, ~374 users

---

## STEP 2 — Import Channels + Messages to Odoo

**Runs on:** Mac (XML-RPC to Odoo)
**Time:** ~5 minutes for ~1,500 messages
**Output:** Discuss channels created + `~/Downloads/slack_fix_timestamps.sql`

### 2a. If re-running (channels already exist), clean up first

**Run on server:**
```bash
sudo -u odoo psql -d DATABASE -c "
DELETE FROM mail_message WHERE res_id IN (
  SELECT id FROM discuss_channel WHERE name LIKE '[Slack]%'
) AND model = 'discuss.channel';
DELETE FROM discuss_channel WHERE name LIKE '[Slack]%';
"
```
Replace `DATABASE` with `intrix-staging` or `intrix`.

### 2b. Run the import

Edit `PASS` in `slack_to_odoo_v2.py`, then:

```bash
cd ~/Downloads
python3 slack_to_odoo_v2.py
```

**For production:** also change `URL`, `DB` in the script:
```python
URL = "https://intrix.bpconsulting.my"
DB = "intrix"
```

**What it does:**
- Creates `[Slack] channel-name` channels in Odoo Discuss
- Maps Slack users → Odoo employees by name (~80 matched out of 374)
- Posts messages with correct `author_id` (unmatched → Administrator)
- Cleans Slack markup: `<@U123>` → `@RealName`, URLs, emoji codes
- Skips system messages (joins, leaves)
- Generates `slack_fix_timestamps.sql` at the end

**Known gotcha:** `message_post` returns a list `[12345]` not int — script extracts `[0]`

### 2c. Fix message timestamps

The import stamps all messages as "now". The generated SQL fixes them to original Slack dates.

**Copy SQL to server and run:**
```bash
scp ~/Downloads/slack_fix_timestamps.sql root@odoo19e:/tmp/
sudo -u odoo psql -d DATABASE -f /tmp/slack_fix_timestamps.sql
```

**Restart Odoo** (Cloudpepper restart) after this step.

---

## STEP 3 — Import File Attachments

**Runs on:** Mac
**Time:** ~5-10 minutes for ~100 files (depends on file sizes)
**Output:** Files in `~/Downloads/slack_files/` + `~/Downloads/slack_link_attachments.sql`

### 3a. Clean previous attachment attempt (if re-running)

**Run on server:**
```bash
sudo -u odoo psql -d DATABASE -c "
DELETE FROM message_attachment_rel WHERE attachment_id IN (
  SELECT id FROM ir_attachment WHERE create_date >= 'YYYY-MM-DD'
  AND res_model = 'discuss.channel'
);
DELETE FROM ir_attachment WHERE create_date >= 'YYYY-MM-DD'
AND res_model = 'discuss.channel';
"
```
Replace `YYYY-MM-DD` with the date of the import run.

Also clean local downloads:
```bash
rm -rf ~/Downloads/slack_files
```

### 3b. Run the attachment import

Edit `PASS` in `slack_attachments.py`, then:

```bash
cd ~/Downloads
python3 slack_attachments.py
```

**For production:** also change `URL`, `DB`, and consider changing `DAYS_BACK`:
```python
URL = "https://intrix.bpconsulting.my"
DB = "intrix"
DAYS_BACK = 90  # or however many days of files you want
```

**What it does:**
- Filters messages with files within `DAYS_BACK` window
- Downloads each file from Slack using auth header with redirect handling
- Base64-encodes and creates `ir.attachment` in Odoo (on `discuss.channel`)
- Generates `slack_link_attachments.sql` to link attachments to messages
- 0.5s sleep between downloads to avoid Slack rate limits (429)

**Known gotcha:** Python's `urllib` strips Authorization header on HTTP redirects. Script uses custom `AuthRedirectHandler` to preserve it. This was the root cause of empty/HTML files in the first attempt.

**Known gotcha:** Old files may return 404 (Slack retention policy). Script logs these and continues.

### 3c. Link attachments to messages

**Copy SQL to server and run:**
```bash
scp ~/Downloads/slack_link_attachments.sql root@odoo19e:/tmp/
sudo -u odoo psql -d DATABASE -f /tmp/slack_link_attachments.sql
```

**Restart Odoo** (Cloudpepper restart) after this step.

---

## STEP 4 — Verify

1. Open Odoo → Discuss
2. Check `[Slack]` channels appear in the left sidebar
3. Open a channel — messages should show:
   - Correct author names (from employee mapping)
   - Correct dates/times (from SQL timestamp fix)
   - Clean text (no HTML tags, no Slack markup)
   - Attachments visible inline (images render, PDFs downloadable)
4. Spot-check a few channels against Slack to confirm content matches

---

## Production Deployment Checklist

- [ ] Update `slack_export.py`: set `DAYS_BACK` to desired range
- [ ] Re-run `slack_export.py` to get fresh data (Slack conversations continue daily)
- [ ] Update `slack_to_odoo_v2.py`: change URL/DB to production, edit PASS
- [ ] Update `slack_attachments.py`: change URL/DB to production, edit PASS, set `DAYS_BACK`
- [ ] Run Step 2 (channels + messages)
- [ ] Run Step 2c (fix timestamps SQL)
- [ ] Run Step 3 (attachments)
- [ ] Run Step 3c (link attachments SQL)
- [ ] Cloudpepper restart production
- [ ] Verify in Odoo Discuss
- [ ] Check server disk space: `df -h /var/odoo`
- [ ] Inform INTRIX team: Slack channels are now in Odoo Discuss

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Authentication failed` | Wrong password | Edit `PASS` in script |
| Messages show as today's date | Timestamp SQL not run | Run Step 2c |
| Images show as grey placeholders | Attachments not linked to messages | Run Step 3c |
| All files ~54KB (HTML pages) | Auth header stripped on redirect | Use the `AuthRedirectHandler` version of `slack_attachments.py` |
| 429 Too Many Requests | Slack rate limit | Script auto-retries; increase `time.sleep()` if persistent |
| 404 on file download | File deleted from Slack (retention) | Normal for old files — script logs and continues |
| `Invalid field 'mobile'` | Odoo 19 doesn't have mobile on res.partner | Already fixed in v2 — use `phone` field |
| Channels exist but no messages | Script skips existing channels | Clean up first (Step 2a) then re-run |

---

## Data Volumes (22 Apr 2026 baseline)

- Channels: 115 total (64 with messages)
- Messages: 1,681 (933 regular + 508 bot + 240 system)
- Messages imported: 1,449 (system skipped)
- Users: 374 (80 mapped to Odoo employees)
- Files: 962 total (501 JPG, 255 PDF, 132 PNG, 44 HEIC, 14 MP4, 12 binary, 4 other)
- Last 14 days: 99 files / ~157 MB

---

## Slack App Scopes (for reference)

If you need to recreate the Slack App:
1. Go to `https://api.slack.com/apps` → Create New App → From Scratch
2. Name: "BPC Migration", Workspace: INTRIX Group
3. OAuth & Permissions → User Token Scopes:
   - `channels:history`
   - `channels:read`
   - `groups:history`
   - `groups:read`
   - `users:read`
   - `files:read`
4. Install to Workspace → Authorize
5. Copy User OAuth Token (starts with `xoxp-`)
