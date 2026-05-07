import os
import subprocess
from glob import glob
import zipfile
import concurrent.futures
import config

if not os.path.isdir(config.unzip_path):
    os.makedirs(config.unzip_path)

out_dir = os.path.expanduser(config.unzip_path)
src_dirs = config.download_path

files = glob(f'{src_dirs}/*.zip')

def detect_format(path):
    with open(path, 'rb') as f:
        header = f.read(8)
    if header[:4] == b'Rar!':
        return 'rar'
    if header[:6] == b'7z\xbc\xaf\x27\x1c':
        return '7z'
    if header[:4] == b'PK\x03\x04' or header[:4] == b'PK\x05\x06':
        return 'zip'
    return 'unknown'

def unzip_to_path(zip_path):
    fmt = detect_format(zip_path)
    if fmt == 'zip':
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(out_dir)
        except zipfile.BadZipFile:
            print(f'Could not unzip: {zip_path}')
    elif fmt in ('7z', 'rar'):
        tool = 'unrar' if fmt == 'rar' else '7z'
        cmd = ['unrar', 'x', '-o+', zip_path, out_dir] if fmt == 'rar' else ['7z', 'x', f'-o{out_dir}', '-y', zip_path]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            print(f'Could not extract ({fmt}): {zip_path}')
            print(result.stderr.decode(errors='replace')[:200])
    else:
        print(f'Unknown format, skipping: {zip_path}')

print(f'Will attempt to unzip {len(files)} files')
with concurrent.futures.ThreadPoolExecutor(8) as executor:
    res = [
        executor.submit(unzip_to_path, f)
        for f in files
    ]
    concurrent.futures.wait(res)

print('Done.')
