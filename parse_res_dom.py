with open('res_img_dom.html', 'r', encoding='utf-8') as f:
    dom = f.read()
import re
print('Has content folder?', 'content' in dom)
print('Buttons with addFolder:', set(re.findall(r'<button[^>]*addFolder[^>]*>.*?</button>', dom)))
print('Buttons with upload:', set(re.findall(r'<button[^>]*upload[^>]*>.*?</button>', dom, re.IGNORECASE)))
print('Buttons with create:', set(re.findall(r'<button[^>]*create[^>]*>.*?</button>', dom, re.IGNORECASE)))
print('Angular inputs for file:', set(re.findall(r'<input[^>]*type=[\"\']file[\"\'][^>]*>', dom, re.IGNORECASE)))
