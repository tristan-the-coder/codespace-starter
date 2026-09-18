import json
import re
from datetime import datetime
from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'albums' / 'taylor_swift_albums.json'
out_dir = root / 'album-pages'
out_dir.mkdir(exist_ok=True)
for existing in out_dir.glob('*.qmd'):
    existing.unlink()

with src.open() as f:
    payload = json.load(f)

records = []
seen = set()
for item in payload.get('results', []):
    if item.get('artistName') != 'Taylor Swift':
        continue
    if item.get('wrapperType') != 'collection':
        continue
    if item.get('collectionType') != 'Album':
        continue
    name = (item.get('collectionName') or '').strip()
    if not name:
        continue
    lower_name = name.lower()
    skip_tokens = (
        'single', 'remix', 'karaoke', 'instrumentals',
        'live from', 'live ', 'world tour', 'piano covers',
        'cover', 'toy story', 'soundtrack', 'from the motion picture',
        'featured in', 'performance', 'cma awards', 'studio sessions',
        'from the disney+ special', 'from "'
    )
    if any(token in lower_name for token in skip_tokens):
        continue
    if lower_name in seen:
        continue
    seen.add(lower_name)
    records.append(item)

records.sort(key=lambda x: x.get('releaseDate') or '2000-01-01T00:00:00Z')


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    value = value.strip('-')
    return value[:80] or 'album'


def format_date(value: str) -> str:
    if not value:
        return 'Unknown date'
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).strftime('%Y-%m-%d')
    except ValueError:
        return value[:10]

for i, item in enumerate(records, start=1):
    title = item.get('collectionName', 'Taylor Swift Album')
    slug = slugify(title)
    page_path = out_dir / f'{i:02d}-{slug}.qmd'
    release_date = format_date(item.get('releaseDate'))
    image = item.get('artworkUrl100') or 'https://placehold.co/600x600?text=Taylor+Swift'
    price = item.get('collectionPrice')
    genre = item.get('primaryGenreName', 'Unknown')
    track_count = item.get('trackCount', 'Unknown')
    country = item.get('country', 'USA')
    view_url = item.get('collectionViewUrl', '#')

    title_yaml = json.dumps(title)
    release_yaml = json.dumps(release_date)
    image_yaml = json.dumps(image)
    page_text = f'''---
title: {title_yaml}
date: {release_yaml}
image: {image_yaml}
---

![{title}]({image})

## Album details

- Artist: Taylor Swift
- Release date: {release_date}
- Genre: {genre}
- Tracks: {track_count}
- Country: {country}
- Price: ${price} USD

[Open on Apple Music]({view_url})

[Back to all albums](../index.qmd)
'''
    page_path.write_text(page_text)

index_text = '''---
title: "Taylor Swift Albums"
listing:
  - id: album-gallery
    contents: album-pages
    type: grid
    sort: "date desc"
    fields: [image, title, date]
    image-height: 220px
    page-size: 24
    filter-ui: false
    sort-ui: false
format:
  html:
    theme: cosmo
    toc: true
---

# Taylor Swift album collection

This site organizes Taylor Swift’s released albums into separate Quarto pages.

'''
(root / 'index.qmd').write_text(index_text)

print(f'Generated {len(records)} album pages in {out_dir}')
