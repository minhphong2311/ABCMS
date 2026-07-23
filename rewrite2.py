import os

file_path = os.path.join('d:\\', 'Projects', 'test04', 'templates', 'site_detail.html')
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the old filtering logic with new tree and filtering logic
old_js_start = "let currentFolderFilter = 'all';"
end_js = "</script>"

new_js = """
// --- SPLIT VIEW LOGIC ---
const siteMenus = {{ site.menus | tojson | safe }} || [];
let currentTreeFilterIds = null; // null means show all, otherwise array of leaf node ids to show

document.addEventListener('DOMContentLoaded', () => {
    renderMenuTree();
    
    // Restore View Preference
    const savedView = localStorage.getItem('siteDetailViewMode') || 'list';
    toggleView(savedView);
});

function renderMenuTree() {
    const container = document.getElementById('site-menu-tree-container');
    if (siteMenus.length === 0) {
        container.innerHTML = '<div class="text-center p-3 text-muted">No menus found.</div>';
        return;
    }
    
    const treeHTML = buildTreeHTML(siteMenus, null);
    container.innerHTML = `
        <div class="px-3 py-2 border-bottom bg-light cursor-pointer" onclick="clearTreeFilter()" style="cursor: pointer;">
           <i class="fas fa-home text-primary mr-2"></i> <strong>Show All Pages</strong>
        </div>
        <div class="p-2">${treeHTML}</div>
    `;
}

function buildTreeHTML(menus, parentId) {
    const children = menus.filter(m => (m.parent_id || null) === (parentId || null));
    if (children.length === 0) return '';
    
    let html = '<ul class="list-unstyled pl-3 mb-0" style="margin-left: ' + (parentId ? '10px' : '0') + '">';
    children.sort((a, b) => (a.order || 0) - (b.order || 0)).forEach(node => {
        const hasChildren = menus.some(m => m.parent_id === node.id);
        
        if (hasChildren) {
            html += `
                <li class="py-1">
                  <div class="d-flex align-items-center tree-node cursor-pointer p-1 rounded" onclick="toggleAndFilterTreeNode('${node.id}')" id="tree-node-ui-${node.id}" style="cursor: pointer;">
                    <i class="fas fa-chevron-right fa-xs fa-fw text-muted mr-1" id="tree-caret-${node.id}"></i>
                    <i class="fas fa-folder text-warning mr-2"></i> 
                    <span class="font-weight-bold text-dark">${node.name}</span>
                  </div>
                  <div class="tree-children border-left" id="tree-children-${node.id}" style="display: none;">
                    ${buildTreeHTML(menus, node.id)}
                  </div>
                </li>
            `;
        } else {
            html += `
                <li class="py-1">
                  <div class="d-flex align-items-center tree-leaf cursor-pointer p-1 rounded" onclick="filterByLeafNode('${node.id}')" id="tree-node-ui-${node.id}" style="cursor: pointer; padding-left: 1.5rem !important;">
                    <i class="far fa-file-code text-secondary mr-2"></i>
                    <span class="text-dark">${node.name}</span>
                  </div>
                </li>
            `;
        }
    });
    html += '</ul>';
    return html;
}

function clearTreeFilter() {
    currentTreeFilterIds = null;
    highlightTreeNode(null);
    applyFilters();
}

function toggleAndFilterTreeNode(nodeId) {
    // Toggle expand/collapse
    const childrenDiv = document.getElementById(`tree-children-${nodeId}`);
    const caret = document.getElementById(`tree-caret-${nodeId}`);
    
    if (childrenDiv.style.display === 'none') {
        childrenDiv.style.display = 'block';
        caret.classList.replace('fa-chevron-right', 'fa-chevron-down');
    } else {
        childrenDiv.style.display = 'none';
        caret.classList.replace('fa-chevron-down', 'fa-chevron-right');
    }
    
    // Filter to show all descendants of this folder
    const descendantIds = getAllDescendantLeafIds(nodeId);
    currentTreeFilterIds = descendantIds;
    highlightTreeNode(nodeId);
    applyFilters();
}

function filterByLeafNode(nodeId) {
    currentTreeFilterIds = [nodeId];
    highlightTreeNode(nodeId);
    applyFilters();
}

function highlightTreeNode(nodeId) {
    document.querySelectorAll('[id^="tree-node-ui-"]').forEach(el => el.classList.remove('bg-info', 'text-white'));
    if (nodeId) {
        const el = document.getElementById(`tree-node-ui-${nodeId}`);
        if (el) el.classList.add('bg-info', 'text-white');
    }
}

function getAllDescendantLeafIds(parentId) {
    let leaves = [];
    const children = siteMenus.filter(m => m.parent_id === parentId);
    children.forEach(c => {
        const hasSub = siteMenus.some(m => m.parent_id === c.id);
        if (hasSub) {
            leaves = leaves.concat(getAllDescendantLeafIds(c.id));
        } else {
            leaves.push(c.id);
        }
    });
    return leaves;
}

function toggleView(viewType) {
    localStorage.setItem('siteDetailViewMode', viewType);
    const listView = document.getElementById('list-view-container');
    const gridView = document.getElementById('grid-view-container');
    const btnList = document.getElementById('btn-list-view');
    const btnGrid = document.getElementById('btn-grid-view');
    
    if (viewType === 'list') {
        listView.style.display = 'block';
        gridView.style.display = 'none';
        btnList.classList.replace('btn-outline-secondary', 'btn-secondary');
        btnGrid.classList.replace('btn-secondary', 'btn-outline-secondary');
    } else {
        listView.style.display = 'none';
        gridView.style.display = 'flex';
        btnList.classList.replace('btn-secondary', 'btn-outline-secondary');
        btnGrid.classList.replace('btn-outline-secondary', 'btn-secondary');
    }
}

function filterPages() {
    applyFilters();
}

function applyFilters() {
    const query = document.getElementById('pageSearchInput').value.toLowerCase().trim();
    // Support both grid and list items
    const items = document.querySelectorAll('.page-card-wrapper');
    const noResults = document.getElementById('noPageSearchResults');
    let visibleCount = 0;
    
    items.forEach(item => {
        // We can find the node ID if we need to, or match by folder/slug.
        // Actually, we need a way to map the card to the menu.id.
        // Let's add data-id attribute to the tr/div, but since we didn't, we can find the menu by slug and folder.
        const folder = item.getAttribute('data-folder');
        const slug = item.getAttribute('data-slug');
        const menu = siteMenus.find(m => (m.folder || '') === folder && m.slug === slug);
        const menuId = menu ? menu.id : null;
        
        let titleText = '';
        if(item.tagName === 'TR') {
           const titleEl = item.querySelector('.font-weight-bold');
           titleText = titleEl ? titleEl.textContent.toLowerCase() : '';
        } else {
           const titleEl = item.querySelector('.card-title');
           titleText = titleEl ? titleEl.textContent.toLowerCase() : '';
        }
        
        const slugText = slug.toLowerCase();
        const matchesQuery = titleText.includes(query) || slugText.includes(query);
        
        let matchesTree = true;
        if (currentTreeFilterIds !== null && menuId) {
            matchesTree = currentTreeFilterIds.includes(menuId);
        }
        
        if (matchesQuery && matchesTree) {
            if(item.tagName === 'TR') {
                item.style.setProperty('display', 'table-row', 'important');
            } else {
                item.style.setProperty('display', 'block', 'important');
            }
            visibleCount++;
        } else {
            item.style.setProperty('display', 'none', 'important');
        }
    });
    
    if (noResults) {
        if (visibleCount > 0 || items.length === 0) {
            noResults.style.display = 'none';
        } else {
            noResults.style.display = 'block';
        }
    }
}
"""

if old_js_start in content:
    parts = content.split(old_js_start)
    new_content = parts[0] + new_js + end_js + "\n{% endblock %}\n"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("JS logic injected successfully")
else:
    print("Could not find the hook for replacing JS")
