#!/usr/bin/env python3
import importlib.util
import json
import os
import subprocess
import sys

import requests

CONFIG_PATH = 'config.py'
PLACEHOLDER_API_KEY = 'YOUR_API_KEY_HERE'
PLACEHOLDER_COOKIES = 'YOUR_SESSION_COOKIE'

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    spec = importlib.util.spec_from_file_location('_cfg', CONFIG_PATH)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return {}
    return {
        'download_path': getattr(mod, 'download_path', 'downloaded_mods'),
        'unzip_path':    getattr(mod, 'unzip_path', 'unzipped_mods'),
        'nexusmods_api_key': getattr(mod, 'nexusmods_api_key', ''),
        'game_id':       getattr(mod, 'game_id', 0),
        'COOKIES':       getattr(mod, 'COOKIES', ''),
        '_game_domain':  getattr(mod, '_game_domain', ''),
    }

def write_config(cfg):
    with open(CONFIG_PATH, 'w') as f:
        f.write(f"""\
# --- Paths ---
download_path = {cfg['download_path']!r}
unzip_path = {cfg['unzip_path']!r}

# --- Nexus Mods API key ---
# Required for fetch_collection.py. Free account is fine.
# Get yours at https://www.nexusmods.com/users/myaccount?tab=api
nexusmods_api_key = {cfg['nexusmods_api_key']!r}

# --- Game ID ---
# The numeric game ID used by Nexus Mods. Find it by opening DevTools while on
# any mod page and looking at the GenerateDownloadUrl request body (game_id=...).
# _game_domain tracks which game this ID belongs to — updated automatically.
game_id = {cfg['game_id']}
_game_domain = {cfg.get('_game_domain', '')!r}

# --- Browser session cookies ---
# You need to acquire these once per session (they expire periodically).
#   1. Open Chrome DevTools (F12) and go to the Network tab
#   2. Manually download any mod for your game on nexusmods.com
#   3. Filter requests by "Downloads?" to find the GenerateDownloadUrl request
#   4. Right-click it > Copy > Copy as cURL, then paste into https://curlconverter.com/
#   5. Copy the cookies string from the generated Python code and paste it below
# Note: this is also where you can confirm the correct game_id (see request payload).
COOKIES = {cfg['COOKIES']!r}
""")

def validate_api_key(key):
    try:
        r = requests.get(
            'https://api.nexusmods.com/v1/users/validate.json',
            headers={'apikey': key},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json().get('name')
    except Exception:
        pass
    return None

def validate_cookies(cookies):
    """Returns True if the session cookies are still valid."""
    try:
        r = requests.get(
            'https://www.nexusmods.com/users/myaccount',
            headers={
                'Cookie': cookies,
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            },
            allow_redirects=False,
            timeout=10,
        )
        # Logged in → 200; expired/not logged in → 302 to login page
        return r.status_code == 200
    except Exception:
        return False

def yn(prompt, default='y'):
    hint = 'Y/n' if default == 'y' else 'y/N'
    val = input(f'{prompt} [{hint}]: ').strip().lower()
    return (val in ('y', 'yes')) if val else (default == 'y')

def ask(prompt):
    while True:
        val = input(f'{prompt}: ').strip()
        if val:
            return val

def section(title):
    print(f'\n── {title} {"─" * max(1, 52 - len(title))}')

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print('nexus-mocodo setup')
    print('=' * 18)

    cfg = load_config()
    cfg.setdefault('download_path', 'downloaded_mods')
    cfg.setdefault('unzip_path', 'unzipped_mods')
    cfg.setdefault('nexusmods_api_key', '')
    cfg.setdefault('game_id', 0)
    cfg.setdefault('COOKIES', '')
    cfg.setdefault('_game_domain', '')

    # ── API key ───────────────────────────────────────────────────────────────
    section('Nexus Mods API key')
    api_key = cfg['nexusmods_api_key']
    if api_key and PLACEHOLDER_API_KEY not in api_key:
        print('Validating...', end=' ', flush=True)
        username = validate_api_key(api_key)
        if username:
            print(f'✓ logged in as {username}')
        else:
            print('✗ invalid or unreachable')
            if yn('Re-enter API key?'):
                api_key = ask('API key')
    else:
        print('A free Nexus Mods API key is required for fetching collections.')
        print('Get yours at: https://www.nexusmods.com/users/myaccount?tab=api')
        api_key = ask('API key')
    cfg['nexusmods_api_key'] = api_key

    # ── Collection ────────────────────────────────────────────────────────────
    section('Collection')
    col = None
    if os.path.exists('collection.json'):
        try:
            with open('collection.json') as f:
                col = json.load(f)
            info = col.get('info', {})
            print(f'Current: "{info.get("name", "unknown")}" ({info.get("domainName", "unknown")})')
            if not yn('Use this collection?'):
                col = None
        except Exception:
            print('collection.json could not be read.')

    if col is None:
        print('Paste a Nexus Mods collection URL:')
        print('  e.g. https://www.nexusmods.com/games/witcher3/collections/ypinp7')
        url = ask('URL')
        write_config(cfg)  # ensure fetch_collection.py can read the API key
        result = subprocess.run([sys.executable, 'fetch_collection.py', url])
        if result.returncode != 0:
            print('Failed to fetch collection. Check your API key and the URL.')
            sys.exit(1)
        with open('collection.json') as f:
            col = json.load(f)
        print(f'✓ Saved as collection.json')

    game_domain = col.get('info', {}).get('domainName', '')

    # ── Game ID ───────────────────────────────────────────────────────────────
    section('Game ID')
    game_id = cfg['game_id']
    game_changed = game_domain and cfg['_game_domain'] and cfg['_game_domain'] != game_domain

    if game_id and not game_changed:
        print(f'✓ game_id={game_id} ({game_domain})')
    else:
        if game_changed:
            print(f'Game changed: {cfg["_game_domain"]} → {game_domain}')
        else:
            print(f'Game: {game_domain}')
        print('Find the numeric game_id in DevTools:')
        print('  Open a mod page, click manual download, find the GenerateDownloadUrl')
        print('  request in the Network tab → Payload → game_id.')
        while True:
            val = input('game_id: ').strip()
            if val.isdigit():
                game_id = int(val)
                break
            print('  Enter a number.')
    cfg['game_id'] = game_id
    cfg['_game_domain'] = game_domain

    # ── Cookies ───────────────────────────────────────────────────────────────
    section('Browser session cookies')
    cookies = cfg['COOKIES']
    cookies_ok = False
    if cookies and PLACEHOLDER_COOKIES not in cookies:
        print('Validating...', end=' ', flush=True)
        cookies_ok = validate_cookies(cookies)
        print('✓ valid' if cookies_ok else '✗ expired or invalid')

    if not cookies_ok:
        print('Steps to get fresh cookies:')
        print('  1. Open nexusmods.com and trigger a manual mod download')
        print('  2. In DevTools Network tab, filter by "Downloads?"')
        print('     and find the GenerateDownloadUrl request')
        print('  3. Right-click → Copy as cURL')
        print('     → paste into https://curlconverter.com/')
        print('  4. Copy the cookies string from the generated Python code')
        cookies = ask('Cookies')
    cfg['COOKIES'] = cookies

    # ── Save ──────────────────────────────────────────────────────────────────
    section('Saving config')
    write_config(cfg)
    print('✓ config.py saved')

    # ── Download ──────────────────────────────────────────────────────────────
    section('Download')
    col_name = col.get('info', {}).get('name', 'collection')
    if yn(f'Start downloading "{col_name}" now?'):
        subprocess.run([sys.executable, 'download_mods.py'])


if __name__ == '__main__':
    main()
