import re
import sys
import requests
import config

GRAPHQL_URL = 'https://api.nexusmods.com/v2/graphql'

QUERY = """
query CollectionRevision($slug: String!, $domainName: String!) {
  collectionRevision(slug: $slug, domainName: $domainName, viewAdultContent: true) {
    downloadLink
    revisionNumber
    fileSize
  }
}
"""

def parse_url(url):
    # Handles: https://www.nexusmods.com/games/witcher3/collections/ypinp7
    m = re.match(r'https?://(?:www\.)?nexusmods\.com/(?:games/)?([^/]+)/collections/([^/?&#]+)', url)
    if not m:
        sys.exit(f'Unrecognised URL: {url}')
    return m.group(1), m.group(2)

def main(url):
    domain, slug = parse_url(url)
    headers = {
        'apikey': config.nexusmods_api_key,
        'Content-Type': 'application/json',
    }

    print(f'Fetching collection {slug} ({domain})...')
    r = requests.post(GRAPHQL_URL, json={
        'query': QUERY,
        'variables': {'slug': slug, 'domainName': domain},
    }, headers=headers)
    r.raise_for_status()

    body = r.json()
    if 'errors' in body:
        sys.exit(f'GraphQL error: {body["errors"]}')

    revision = body['data']['collectionRevision']
    download_link = revision['downloadLink']
    revision_number = revision['revisionNumber']
    file_size = revision.get('fileSize', 0)

    print(f'Revision {revision_number} ({file_size:,} bytes), downloading...')
    r = requests.get(download_link, allow_redirects=True)
    r.raise_for_status()

    with open('collection.json', 'wb') as f:
        f.write(r.content)
    print(f'Saved collection.json')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python fetch_collection.py <collection_url>')
        print('Example: python fetch_collection.py https://www.nexusmods.com/games/witcher3/collections/ypinp7')
        sys.exit(1)
    main(sys.argv[1])
