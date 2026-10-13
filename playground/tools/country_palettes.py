"""Build countries_palette.json: for every country, its flag's main colours
(area-weighted, from a small flag PNG), its capital's coordinates (Natural
Earth populated places, with the country centroid as fallback), and names."""
import json, colorsys
from collections import Counter
from PIL import Image

countries = json.load(open('mledoze.json', encoding='utf-8'))
ne = json.load(open('ne_places.geojson', encoding='utf-8'))['features']
cap_by_a3 = {}
for f in ne:
    p = f['properties']
    if p.get('adm0cap') == 1 and p.get('adm0_a3'):
        cap_by_a3.setdefault(p['adm0_a3'], (f['geometry']['coordinates'], p.get('name')))

def flag_colours(path):
    im = Image.open(path).convert('RGB')
    q = im.quantize(colors=8, method=2).convert('RGB')
    counts = Counter(q.getdata())
    total = sum(counts.values())
    clusters = []  # [rgb, count]
    for rgb, n in counts.most_common():
        for c in clusters:
            if sum((a - b) ** 2 for a, b in zip(c[0], rgb)) ** 0.5 < 60:
                c[1] += n; break
        else:
            clusters.append([rgb, n])
    out = [('#%02x%02x%02x' % tuple(rgb), round(n / total, 3)) for rgb, n in clusters if n / total >= 0.02]
    return out[:4]

result = []
for c in countries:
    code = c['cca2'].lower()
    cols = flag_colours(f'flags/{code}.png')
    cap = cap_by_a3.get(c['cca3'])
    if cap:
        lng, lat = cap[0]; zoom, capname = 13.8, cap[1]
    else:
        lat, lng = c['latlng']; zoom, capname = 5.5, (c.get('capital') or [None])[0]
    result.append({
        'code': code, 'name': c['name']['common'],
        'name_fr': c.get('translations', {}).get('fra', {}).get('common') or c['name']['common'],
        'region': c.get('region'), 'independent': bool(c.get('independent')),
        'capital': capname, 'center': [round(lng, 4), round(lat, 4)], 'zoom': zoom,
        'colours': cols,
    })
result.sort(key=lambda r: r['name'])
json.dump(result, open('countries_palette.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
with_cap = sum(1 for r in result if r['zoom'] > 10)
print(len(result), 'countries;', with_cap, 'with capital coordinates;', len(result) - with_cap, 'fall back to country centre')
for code in ('ma', 'fr', 'jp', 'br', 'za'):
    r = next(x for x in result if x['code'] == code); print(code, r['capital'], r['center'], r['colours'])
