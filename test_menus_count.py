import json
with open('data/sites.json', 'r', encoding='utf-8') as f:
    sites = json.load(f)
for s in sites:
    if s['id'] == 'test-phong':
        print(f"Total menus in sites.json: {len(s.get('menus', []))}")
        for m in s.get('menus', []):
            print(f"{m.get('name')} - parent_id: {m.get('parent_id')}")
