import json

data = open('d:/Projects/test04/data/figma_cache.json', encoding='utf-8').read()
d = json.loads(data)

for k, v in d.items():
    if not isinstance(v, dict):
        continue
    if 'nodes' not in v:
        continue
    for nid, node_data in v['nodes'].items():
        doc = node_data.get('document', {})
        def find_image_fills(node, depth=0):
            name = node.get('name', '')
            t = node.get('type', '')
            fills = node.get('fills', [])
            bb = node.get('absoluteBoundingBox', {})
            w = bb.get('width', 0)
            h = bb.get('height', 0)
            for f in fills:
                if f.get('type') == 'IMAGE':
                    ref = f.get('imageRef', '')
                    print(f"[IMG_FILL] id={node.get('id')} name={name!r} type={t} size={w}x{h} ref={ref}")
            for c in node.get('children', []):
                find_image_fills(c, depth+1)
        find_image_fills(doc)
