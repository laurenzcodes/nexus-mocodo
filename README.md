# Nexus Mod Collection Downloader

`mocodo` = **Mo**d **Co**llection **Do**wnloader.

Scripts to batch-download entire mod collections from [Nexus Mods](https://www.nexusmods.com) without a Vortex/premium membership. Works with any game on Nexus Mods — the game is detected automatically from your `collection.json`.

## Requirements

- Python 3.8+
- `requests` library (`pip install requests`)
- `curl` (usually pre-installed on Linux/macOS)
- `unrar` and/or `7z` if your mods come in RAR/7z archives (optional)

## Setup

### 1. Get your Nexus Mods API key

Required for `fetch_collection.py`. A free account is fine.

Go to [your Nexus Mods account API settings](https://www.nexusmods.com/users/myaccount?tab=api), generate a personal API key, and paste it into `config.py`.

### 2. Get your collection.json

**Option A — fetch it with the script (recommended):**

```bash
python fetch_collection.py https://www.nexusmods.com/games/witcher3/collections/ypinp7
```

This uses the Nexus API to download the collection bundle and saves it as `collection.json`.

**Option B — copy it from Vortex:**

When Vortex imports a collection via an `nxs://` link, it downloads the bundle to a local file. Copy that file here and rename it to `collection.json`.

### 3. Get your browser session cookies and game ID

Both are obtained in the same place. Cookies are required for download URL generation; the game ID is the numeric ID Nexus uses internally (e.g. `952` for Witcher 3).

1. Log in to nexusmods.com and open any mod page for your game
2. Open DevTools (`F12`) → **Network** tab
3. Click the mod's manual download button
4. Filter by `Downloads?` to find the `GenerateDownloadUrl` request
5. Right-click it → **Copy** → **Copy as cURL**, then paste into [curlconverter.com](https://curlconverter.com/) to extract the cookies
6. The request **Payload** also shows `game_id` — copy that too

> **Note:** Session cookies expire. If downloads fail with auth errors, repeat steps 3–5 to refresh them.

### 4. Configure config.py

```bash
cp config.example.py config.py
```

Then fill in your values:

```python
nexusmods_api_key = 'YOUR_KEY'   # for fetch_collection.py
game_id = 952                     # numeric game ID from DevTools
COOKIES = 'nexusmods_session=...; cf_clearance=...'
```

> `config.py` is gitignored so your credentials won't be accidentally committed.

## Usage

**Run the interactive setup (recommended — handles everything in order):**

```bash
python setup.py
```

On first run it walks through the full configuration. On subsequent runs it skips whatever is still valid (API key, game ID, unexpired cookies) and only prompts for what's changed or expired.

---

**Or use the scripts individually:**

**Fetch a collection from a Nexus Mods URL:**

```bash
python fetch_collection.py https://www.nexusmods.com/games/witcher3/collections/ypinp7
```

**Download all mods from your collection:**

```bash
python download_mods.py
```

Reads `collection.json`, detects the game automatically from the `domainName` field, then downloads all mods in parallel into `downloaded_mods/`. Already-downloaded files are skipped.

**Extract all downloaded archives:**

```bash
python unzip_mods.py
```

Supports `.zip`, `.rar`, and `.7z` archives. Requires `unrar` / `7z` to be installed for non-zip formats. Files that fail to extract are reported but won't stop the rest.

## Files

| File | Purpose |
|------|---------|
| `setup.py` | Interactive setup — configure and start downloading in one go |
| `fetch_collection.py` | Downloads `collection.json` from a Nexus Mods collection URL |
| `download_mods.py` | Downloads all mods listed in `collection.json` |
| `unzip_mods.py` | Extracts all archives in `downloaded_mods/` |
| `collection.json` | Collection bundle (fetched or copied from Vortex) |
| `config.py` | Your credentials and paths (gitignored) |
| `config.example.py` | Template — copy to `config.py` and fill in your values |
