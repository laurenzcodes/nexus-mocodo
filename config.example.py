# Copy this file to config.py and fill in your values.

# --- Paths ---
download_path = 'downloaded_mods'
unzip_path = 'unzipped_mods'

# --- Nexus Mods API key ---
# Required for fetch_collection.py. Free account is fine.
# Get yours at https://www.nexusmods.com/users/myaccount?tab=api
nexusmods_api_key = 'YOUR_API_KEY_HERE'

# --- Game ID ---
# The numeric game ID used by Nexus Mods. Find it by opening DevTools while on
# any mod page and looking at the GenerateDownloadUrl request body (game_id=...).
game_id = 0

# --- Browser session cookies ---
# You need to acquire these once per session (they expire periodically).
#   1. Open Chrome DevTools (F12) and go to the Network tab
#   2. Manually download any mod for your game on nexusmods.com
#   3. Filter requests by "Downloads?" to find the GenerateDownloadUrl request
#   4. Right-click it > Copy > Copy as cURL, then paste into https://curlconverter.com/
#   5. Copy the cookies string from the generated Python code and paste it below
# Note: this is also where you can confirm the correct game_id (see request payload).
COOKIES = (
    'nexusmods_session=YOUR_SESSION_COOKIE; '
    'cf_clearance=YOUR_CF_CLEARANCE_COOKIE'
)
