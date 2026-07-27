import re

with open('menu_dom.html', 'r', encoding='utf-8') as f:
    text = f.read()
    
print("--- INPUTS ---")
inputs = re.findall(r'<input[^>]*>', text, re.IGNORECASE)
for i in inputs:
    if 'type="hidden"' not in i.lower():
        print(i)
        
print("--- BUTTONS ---")
buttons = re.findall(r'<button[^>]*>.*?</button>', text, re.IGNORECASE)
for b in buttons:
    if 'ng-click' in b:
        match = re.search(r'ng-click="([^"]+)"', b)
        text_content = re.sub(r'<[^>]+>', '', b).strip()
        print(f'Button ng-click: {match.group(1) if match else ""} -> Text: {text_content}')
