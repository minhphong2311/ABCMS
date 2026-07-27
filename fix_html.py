import re

with open('templates/site_detail.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove the bad placement
text = re.sub(r'(\s*<script>\s*function deployMenus.*?<\/script>\s*)', '', text, flags=re.DOTALL)

script = '''
<script>
function deployMenus(siteId) {
  if (!confirm("Are you sure you want to deploy the menu tree to the CMS? This will run in the background.")) return;
  
  fetch('/api/deploy_menus', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ site_id: siteId })
  })
  .then(r => r.json())
  .then(data => {
    if(data.success) {
      showToast('Deploy Menus Started', data.message, 'success');
    } else {
      showToast('Error', data.message, 'danger');
    }
  })
  .catch(err => {
    console.error(err);
    showToast('Error', 'An unexpected error occurred.', 'danger');
  });
}
</script>
'''

if 'function deployMenus' not in text:
    text = text.replace('{% endblock %}', script + '\n{% endblock %}')
    with open('templates/site_detail.html', 'w', encoding='utf-8') as f:
        f.write(text)
