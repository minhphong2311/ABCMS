import os

file_path = os.path.join('d:\\', 'Projects', 'test04', 'templates', 'site_detail.html')
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Find the first {% block style %} block (the one I injected at the top)
pattern = r'\{% block title %\}Site Details - \{\{ site\.name \}\}\{% endblock %\}.*?\{% block style %\}(.*?)\{% endblock %\}'
match = re.search(pattern, content, re.DOTALL)

if match:
    # The CSS I injected
    injected_css = match.group(1).strip()
    
    # Remove it from the top
    content = content.replace('\n{% block style %}\n' + injected_css + '\n{% endblock %}', '')
    
    # Inject it into the existing block style at the bottom
    # The bottom block style is around line 528:
    # {% block style %}
    # <link rel="stylesheet"...>
    # <style>
    # ...
    content = content.replace('{% block style %}', '{% block style %}\n' + injected_css + '\n')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed Jinja block style conflict")
else:
    print("Could not find the injected block style")
