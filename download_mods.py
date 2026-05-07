import os
import subprocess
import requests
import json
import concurrent.futures
import config

output_dir = config.download_path
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

with open('collection.json') as f:
    collection = json.load(f)

mods = collection['mods']
game_domain = collection['info']['domainName']
game_id = config.game_id
print(f'Game: {game_domain} (id={game_id})')

def download_from_url(url, save_path):
    if os.path.isfile(save_path):
        print(f'Already downloaded: {save_path}')
        return
    r = requests.get(url, allow_redirects=True)
    if r.status_code != 200:
        return r
    with open(save_path, 'wb') as f:
        f.write(r.content)

def get_dl_url(mod_id, file_id):
    result = subprocess.run(
        [
            'curl', '-s',
            'https://www.nexusmods.com/Core/Libs/Common/Managers/Downloads?GenerateDownloadUrl',
            '-H', 'accept: */*',
            '-H', 'accept-language: en-US,en;q=0.9,de;q=0.8',
            '-H', 'content-type: application/x-www-form-urlencoded',
            '-b', config.COOKIES,
            '-H', 'origin: https://www.nexusmods.com',
            '-H', f'referer: https://www.nexusmods.com/{game_domain}/mods/{mod_id}?tab=files&file_id={file_id}',
            '-H', 'sec-ch-ua: "Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            '-H', 'sec-ch-ua-mobile: ?0',
            '-H', 'sec-ch-ua-platform: "Linux"',
            '-H', 'sec-fetch-dest: empty',
            '-H', 'sec-fetch-mode: cors',
            '-H', 'sec-fetch-site: same-origin',
            '-H', 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
            '--data-raw', f'game_id={game_id}&fid={file_id}&collection_id=0',
        ],
        capture_output=True, text=True,
    )
    try:
        return json.loads(result.stdout)['url']
    except Exception:
        raise Exception(f'Bad response: {result.stdout[:200]}')

def download_mod(mod_info):
    src = mod_info['source']
    mod_name = mod_info['name']
    save_path = f'{output_dir}/' + mod_name + '.zip'
    if 'url' in src:
        url = src['url']
    else:
        url = get_dl_url(src['modId'], src['fileId'])
    print('Attempting to download:', mod_name)
    r = download_from_url(url, save_path)
    if r is not None:
        print(f'Failed to download {mod_name}. Code={r.status_code}; Reason={r.reason}')


with concurrent.futures.ThreadPoolExecutor(8) as executor:
    res = [
        executor.submit(download_mod, mod_info)
        for mod_info in mods
    ]
    concurrent.futures.wait(res)
