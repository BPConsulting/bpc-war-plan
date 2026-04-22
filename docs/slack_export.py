#!/usr/bin/env python3
"""
Slack Channel Export — INTRIX Migration
Run on your Mac: python3 slack_export.py

Exports all channels you have access to, with message history.
Output: slack_export.json (for Odoo import in next step)
"""
import urllib.request
import json
import time
import os
from datetime import datetime, timedelta

TOKEN = "SLACK_TOKEN_HERE"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# How many days of history to pull per channel
DAYS_BACK = 90

OUTPUT_FILE = os.path.expanduser("~/Downloads/slack_export.json")


def slack_get(url):
    """Make a GET request to Slack API with rate limit handling."""
    for attempt in range(3):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
                if data.get('error') == 'ratelimited':
                    retry = int(resp.headers.get('Retry-After', 5))
                    print(f"    Rate limited, waiting {retry}s...")
                    time.sleep(retry)
                    continue
                return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry = int(e.headers.get('Retry-After', 5))
                print(f"    Rate limited, waiting {retry}s...")
                time.sleep(retry)
                continue
            raise
    return {'ok': False, 'error': 'max_retries'}


def get_channels():
    """List all channels (public + private) the user has access to."""
    channels = []
    cursor = None
    for _ in range(20):
        url = "https://slack.com/api/conversations.list?types=public_channel,private_channel&limit=200"
        if cursor:
            url += f"&cursor={cursor}"
        data = slack_get(url)
        if not data.get('ok'):
            print(f"  ERROR listing channels: {data.get('error')}")
            break
        channels.extend(data.get('channels', []))
        cursor = data.get('response_metadata', {}).get('next_cursor')
        if not cursor:
            break
    return channels


def get_users():
    """Build user ID → display name map."""
    users = {}
    cursor = None
    for _ in range(20):
        url = "https://slack.com/api/users.list?limit=200"
        if cursor:
            url += f"&cursor={cursor}"
        data = slack_get(url)
        if not data.get('ok'):
            print(f"  ERROR listing users: {data.get('error')}")
            break
        for u in data.get('members', []):
            name = u.get('real_name') or u.get('profile', {}).get('real_name') or u.get('name', 'Unknown')
            users[u['id']] = name
        cursor = data.get('response_metadata', {}).get('next_cursor')
        if not cursor:
            break
    return users


def get_channel_messages(channel_id, channel_name, days_back):
    """Pull message history for a channel."""
    oldest = (datetime.now() - timedelta(days=days_back)).timestamp()
    messages = []
    cursor = None

    for page in range(100):  # safety limit
        url = f"https://slack.com/api/conversations.history?channel={channel_id}&oldest={oldest}&limit=200"
        if cursor:
            url += f"&cursor={cursor}"
        data = slack_get(url)
        if not data.get('ok'):
            print(f"    ERROR on #{channel_name}: {data.get('error')}")
            break
        batch = data.get('messages', [])
        messages.extend(batch)
        cursor = data.get('response_metadata', {}).get('next_cursor')
        if not cursor or not data.get('has_more'):
            break
        time.sleep(0.5)  # be nice to rate limits

    return messages


def main():
    print("=" * 60)
    print("  INTRIX Slack Export")
    print("=" * 60)

    # Step 1: Get users
    print("\n1. Fetching users...")
    users = get_users()
    print(f"   Found {len(users)} users")

    # Step 2: Get channels
    print("\n2. Fetching channels...")
    channels = get_channels()
    print(f"   Found {len(channels)} channels")

    for ch in sorted(channels, key=lambda c: c.get('name', '')):
        priv = "🔒" if ch.get('is_private') else "📢"
        members = ch.get('num_members', '?')
        name = ch.get('name', 'unnamed')
        print(f"   {priv} #{name:<35} {members:>3} members")

    # Step 3: Pull messages
    print(f"\n3. Pulling messages (last {DAYS_BACK} days)...")
    export = {
        'exported_at': datetime.now().isoformat(),
        'days_back': DAYS_BACK,
        'users': users,
        'channels': [],
    }

    total_messages = 0
    for ch in sorted(channels, key=lambda c: c.get('name', '')):
        name = ch.get('name', 'unnamed')
        channel_id = ch['id']

        messages = get_channel_messages(channel_id, name, DAYS_BACK)

        # Resolve user names in messages
        for msg in messages:
            uid = msg.get('user', '')
            msg['user_name'] = users.get(uid, uid)

        total_messages += len(messages)
        print(f"   #{name:<35} {len(messages):>5} messages")

        export['channels'].append({
            'id': channel_id,
            'name': name,
            'is_private': ch.get('is_private', False),
            'purpose': ch.get('purpose', {}).get('value', ''),
            'topic': ch.get('topic', {}).get('value', ''),
            'num_members': ch.get('num_members', 0),
            'messages': sorted(messages, key=lambda m: float(m.get('ts', '0'))),
        })

        time.sleep(0.3)  # breathing room between channels

    # Step 4: Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(export, f, ensure_ascii=False, indent=2)

    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"\n{'=' * 60}")
    print(f"  DONE!")
    print(f"  Channels: {len(export['channels'])}")
    print(f"  Messages: {total_messages}")
    print(f"  Users:    {len(users)}")
    print(f"  File:     {OUTPUT_FILE} ({size_mb:.1f} MB)")
    print(f"{'=' * 60}")
    print(f"\nUpload slack_export.json to Claude for the Odoo import step.")


if __name__ == '__main__':
    main()
