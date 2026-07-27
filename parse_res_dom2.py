with open('res_img_dom_logged_in2.html', 'r', encoding='utf-8') as f:
    dom = f.read()
import re
print('Has _anchor?', '_anchor' in dom)
print('Has content folder?', 'content_anchor' in dom)
print('Buttons with upload:', set(re.findall(r'<button[^>]*upload[^>]*>.*?</button>', dom, re.IGNORECASE)))
print('Angular inputs for file:', set(re.findall(r'<input[^>]*type=[\"\']file[\"\'][^>]*>', dom, re.IGNORECASE)))
