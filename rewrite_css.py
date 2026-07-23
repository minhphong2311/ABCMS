import os

file_path = os.path.join('d:\\', 'Projects', 'test04', 'templates', 'site_detail.html')
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

style_block = """
{% block style %}
<style>
.tree-node:hover, .tree-leaf:hover {
    background-color: rgba(0,0,0,0.05);
}
.tree-node.bg-info, .tree-leaf.bg-info {
    color: #fff !important;
}
.tree-node.bg-info .text-muted, .tree-leaf.bg-info .text-muted, .tree-leaf.bg-info .text-secondary {
    color: #f8f9fa !important;
}
body.dark-mode .tree-node:hover, body.dark-mode .tree-leaf:hover {
    background-color: rgba(255,255,255,0.1);
}
body.dark-mode .tree-node.bg-info, body.dark-mode .tree-leaf.bg-info {
    background-color: #3f6791 !important;
}
body.dark-mode .table-responsive.bg-white {
    background-color: #343a40 !important;
    border-color: #4b545c !important;
}
body.dark-mode .table th, body.dark-mode .table td {
    border-color: #4b545c;
}
body.dark-mode .table thead.bg-light {
    background-color: #454d55 !important;
}
body.dark-mode .table thead.bg-light th {
    color: #ced4da !important;
}
body.dark-mode .font-weight-bold.text-dark {
    color: #fff !important;
}
body.dark-mode .card-header.bg-light {
    background-color: #454d55 !important;
}
body.dark-mode #site-menu-tree-container {
    background-color: #343a40 !important;
}
</style>
{% endblock %}
"""

if '{% block title %}Site Details - {{ site.name }}{% endblock %}' in content:
    new_content = content.replace('{% block title %}Site Details - {{ site.name }}{% endblock %}', '{% block title %}Site Details - {{ site.name }}{% endblock %}\n' + style_block)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("CSS block injected successfully")
else:
    print("Could not find the hook for CSS")
