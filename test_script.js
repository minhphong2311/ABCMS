
  // Initialize Page Filters on Load
  document.addEventListener('DOMContentLoaded', function() {
      // filters initialization
      checkDeployStatus();
      setInterval(checkDeployStatus, 3000);
  });
  
let knownTasks = {}; // To track what we've already alerted

function checkDeployStatus() {
    $.ajax({
        url: '/api/deploy_status',
        type: 'GET',
        success: function(data) {
            // data is DEPLOY_TASKS from server
            for (let [taskId, info] of Object.entries(data)) {
                if (knownTasks[taskId] === info.status) continue; // no state change
                
                // Parse taskId (site_id--folder--slug)
                let parts = taskId.split('--');
                if (parts[0] !== '{{ site.id }}') continue; // Not this site
                
                let folder = parts[1];
                let slug = parts[2] || parts[1];
                if(parts.length === 2) {
                    folder = "";
                    slug = parts[1];
                }
                
                let paramKey = (folder ? folder + '--' : '--') + slug;
                let btn = document.getElementById(`deploy-form-${paramKey}`);
                let statusInfo = document.getElementById(`build-status-info-${paramKey}`);
                
                if (info.status === 'running') {
                    if (btn && !btn.disabled) {
                        btn.dataset.original = btn.innerHTML;
                        btn.disabled = true;
                        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                    }
                    if (statusInfo) {
                        statusInfo.innerHTML = '<span class="text-info"><i class="fas fa-circle-notch fa-spin mr-1"></i> Deploying in background...</span>';
                    }
                } else if (info.status === 'success') {
                    if (btn) {
                        btn.disabled = false;
                        btn.innerHTML = btn.dataset.original || '<i class="fas fa-cloud-upload-alt"></i>';
                    }
                    if (statusInfo) {
                        statusInfo.innerHTML = '<span class="text-success"><i class="fas fa-check-circle mr-1"></i>Successfully deployed to CMS!</span>';
                    }
                    if (knownTasks[taskId] === 'running') {
                        // Only alert if we saw it running before
                        Swal.fire({
                            toast: true, position: 'top-end', showConfirmButton: false, timer: 4000,
                            icon: 'success', title: 'Deploy successful!', text: `Page ${slug} has been updated.`
                        });
                    }
                } else if (info.status === 'error') {
                    if (btn) {
                        btn.disabled = false;
                        btn.innerHTML = btn.dataset.original || '<i class="fas fa-cloud-upload-alt"></i>';
                    }
                    if (statusInfo) {
                        statusInfo.innerHTML = '<span class="text-danger"><i class="fas fa-exclamation-triangle mr-1"></i>Error Deploy: ' + info.message + '</span>';
                    }
                    if (knownTasks[taskId] === 'running') {
                        Swal.fire({
                            icon: 'error', title: 'Error Deploy', text: info.message
                        });
                    }
                }
                
                knownTasks[taskId] = info.status;
            }
        }
    });
}

let generatePollingIntervals = {};

function generateFiles(siteId, menuSlug, btnElement) {
    const originalContent = '<i class="fas fa-cogs mr-1"></i> Generate Page';
    btnElement.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Initializing...';
    btnElement.disabled = true;

    const statusInfo = document.getElementById(`build-status-info-${menuSlug}`);
    if (statusInfo) {
        statusInfo.innerHTML = '<span class="text-primary"><i class="fas fa-circle-notch fa-spin mr-1"></i> Starting...</span>';
    }

    $.ajax({
        url: `/site/${siteId}/generate/${menuSlug}`,
        type: 'POST',
        success: function(response) {
            if (response.success && response.task_id) {
                btnElement.disabled = false;
                btnElement.classList.remove('btn-primary');
                btnElement.classList.add('btn-danger');
                btnElement.innerHTML = '<i class="fas fa-times-circle mr-1"></i> Stop Generation';
                btnElement.onclick = function() { cancelGenerate(response.task_id, btnElement, menuSlug, siteId); };
                
                pollGenerateTask(response.task_id, menuSlug, btnElement, siteId);
            } else {
                btnElement.disabled = false;
                btnElement.innerHTML = originalContent;
                if (statusInfo) statusInfo.innerHTML = `<span class="text-danger"><i class="fas fa-exclamation-triangle mr-1"></i> ${response.message}</span>`;
                Swal.fire({ toast: true, position: 'top-end', showConfirmButton: false, timer: 3000, icon: 'error', title: 'Error', text: response.message });
            }
        },
        error: function(xhr) {
            btnElement.disabled = false;
            btnElement.innerHTML = originalContent;
            if (statusInfo) statusInfo.innerHTML = '<span class="text-danger"><i class="fas fa-exclamation-triangle mr-1"></i> Server connection error</span>';
            Swal.fire({ toast: true, position: 'top-end', showConfirmButton: false, timer: 3000, icon: 'error', title: 'Connection Error', text: 'Please try again.' });
        }
    });
}

function cancelGenerate(taskId, btnElement, menuSlug, siteId) {
    btnElement.disabled = true;
    btnElement.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Stopping...';
    $.ajax({
        url: `/api/generate_cancel/${taskId}`,
        type: 'POST',
        success: function() {
            // Polling will handle the status update to cancelled
        }
    });
}

function pollGenerateTask(taskId, menuSlug, btnElement, siteId) {
    if (generatePollingIntervals[taskId]) clearInterval(generatePollingIntervals[taskId]);
    const statusInfo = document.getElementById(`build-status-info-${menuSlug}`);
    
    generatePollingIntervals[taskId] = setInterval(() => {
        $.ajax({
            url: '/api/generate_status',
            type: 'GET',
            success: function(data) {
                const task = data[taskId];
                if (!task) return;
                
                if (task.status === 'running') {
                    if (statusInfo) statusInfo.innerHTML = `<span class="text-primary"><i class="fas fa-circle-notch fa-spin mr-1"></i> ${task.message || 'Generating...'}</span>`;
                } else {
                    clearInterval(generatePollingIntervals[taskId]);
                    
                    btnElement.classList.remove('btn-danger');
                    btnElement.classList.add('btn-primary');
                    btnElement.onclick = function() { generateFiles(siteId, menuSlug, btnElement); };
                    btnElement.innerHTML = '<i class="fas fa-cogs mr-1"></i> Generate Page';
                    btnElement.disabled = false;
                    
                    if (task.status === 'success') {
                        const badgeContainer = document.getElementById(`status-badge-container-${menuSlug}`);
                        if (badgeContainer) badgeContainer.innerHTML = '<span class="badge badge-success px-2 py-1"><i class="fas fa-check-circle mr-1"></i>Page Generated</span>';
                        
                        const badgeListContainer = document.getElementById(`status-badge-list-${menuSlug}`);
                        if (badgeListContainer) badgeListContainer.innerHTML = '<span class="badge badge-success px-2 py-1"><i class="fas fa-check-circle mr-1"></i>Page Generated</span>';
                        
                        if (statusInfo) statusInfo.innerHTML = `<span class="text-success"><i class="fas fa-check-circle mr-1"></i> ${task.message}</span>`;
                        
                        // Update Grid View Buttons
                        if(document.getElementById(`preview-btn-${menuSlug}`)) document.getElementById(`preview-btn-${menuSlug}`).style.display = 'inline-block';
                        if(document.getElementById(`preview-disabled-${menuSlug}`)) document.getElementById(`preview-disabled-${menuSlug}`).style.display = 'none';
                        if(document.getElementById(`deploy-form-${menuSlug}`)) document.getElementById(`deploy-form-${menuSlug}`).style.display = 'inline-block';
                        if(document.getElementById(`deploy-disabled-${menuSlug}`)) document.getElementById(`deploy-disabled-${menuSlug}`).style.display = 'none';
                        
                        // Update List View Buttons
                        if(document.getElementById(`preview-list-btn-${menuSlug}`)) document.getElementById(`preview-list-btn-${menuSlug}`).style.display = 'inline-block';
                        if(document.getElementById(`preview-list-disabled-${menuSlug}`)) document.getElementById(`preview-list-disabled-${menuSlug}`).style.display = 'none';
                        if(document.getElementById(`deploy-list-form-${menuSlug}`)) document.getElementById(`deploy-list-form-${menuSlug}`).style.display = 'inline-block';
                        if(document.getElementById(`deploy-list-disabled-${menuSlug}`)) document.getElementById(`deploy-list-disabled-${menuSlug}`).style.display = 'none';
                        
                        const card = btnElement.closest('.card');
                        card.classList.remove('card-secondary');
                        card.classList.add('card-success');
                        
                        Swal.fire({ toast: true, position: 'top-end', showConfirmButton: false, timer: 3000, icon: 'success', title: 'Success!', text: task.message });
                    } else if (task.status === 'error' || task.status === 'cancelled') {
                        if (statusInfo) statusInfo.innerHTML = `<span class="text-danger"><i class="fas fa-exclamation-triangle mr-1"></i> ${task.message}</span>`;
                        Swal.fire({ toast: true, position: 'top-end', showConfirmButton: false, timer: 3000, icon: task.status === 'cancelled' ? 'info' : 'error', title: task.status === 'cancelled' ? 'Cancelled' : 'Error', text: task.message });
                    }
                }
            }
        });
    }, 1000);
}

function deployFiles(siteId, menuSlug, folder, paramKey, btnElement) {
    // UI Loading state
    btnElement.dataset.original = btnElement.innerHTML;
    btnElement.disabled = true;
    btnElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    // Status text block
    const statusInfo = document.getElementById(`build-status-info-${paramKey}`);
    if (statusInfo) {
        statusInfo.innerHTML = '<span class="text-info"><i class="fas fa-circle-notch fa-spin mr-1"></i> Initializing deploy process...</span>';
    }

    $.ajax({
        url: '/api/deploy',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            site_id: siteId,
            menu_slug: menuSlug,
            folder: folder
        }),
        success: function(response) {
            // Trigger polling immediately to update UI based on backend thread status
            checkDeployStatus();
            
            if (!response.success) {
                // If it failed to even start
                btnElement.disabled = false;
                btnElement.innerHTML = btnElement.dataset.original || '<i class="fas fa-cloud-upload-alt"></i>';
                if (statusInfo) statusInfo.innerHTML = '<span class="text-danger"><i class="fas fa-exclamation-triangle mr-1"></i>Error Deploy: ' + response.message + '</span>';
                Swal.fire({ icon: 'error', title: 'Error Deploy', text: response.message });
            }
        },
        error: function(xhr) {
            btnElement.disabled = false;
            btnElement.innerHTML = btnElement.dataset.original || '<i class="fas fa-cloud-upload-alt"></i>';
            if (statusInfo) statusInfo.innerHTML = '<span class="text-danger"><i class="fas fa-exclamation-triangle mr-1"></i>Connection error during Deploy</span>';
            Swal.fire({
                icon: 'error',
                title: 'Connection Error',
                text: 'Cannot call Deploy API. Please try again.'
            });
        }
    });
}

function openEditMenuModal(btnElement) {
    const name = btnElement.getAttribute('data-name') || '';
    const folder = btnElement.getAttribute('data-folder') || '';
    const slug = btnElement.getAttribute('data-slug') || '';
    const figmaLink = btnElement.getAttribute('data-figma') || '';
    const layout = btnElement.getAttribute('data-layout') || '';
    
    // Find menu to get parent_id
    const menu = siteMenus.find(m => (m.folder || '') === folder && m.slug === slug);
    const parentId = menu ? (menu.parent_id || '') : '';

    document.getElementById('edit_menu_name').value = name;
    document.getElementById('edit_folder').value = parentId;
    document.getElementById('edit_menu_slug').value = slug;
    document.getElementById('edit_figma_link').value = figmaLink;
    document.getElementById('edit_layout').value = layout;
    
    // Set form action dynamically with composite key
    const paramKey = (folder ? folder + '--' : '--') + slug;
    document.getElementById('editMenuForm').action = `/site/{{ site.id }}/edit-menu/${paramKey}`;
    
    // Show modal
    $('#editMenuModal').modal('show');
}

function confirmDeleteMenu(event, formElement) {
    event.preventDefault(); // Stop form submission
    
    Swal.fire({
        title: 'Confirm Delete Page?',
        text: 'Are you sure you want to delete this child page? All corresponding generated code will also be completely deleted.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            formElement.submit(); // Submit form programmatically
        }
    });
}

function renameFolder(oldFolder) {
    Swal.fire({
        title: `Rename Folder /${oldFolder}`,
        input: 'text',
        inputLabel: 'New folder name:',
        inputValue: oldFolder,
        showCancelButton: true,
        confirmButtonText: 'Save changes',
        cancelButtonText: 'Cancel',
        inputValidator: (value) => {
            if (!value || !value.trim()) {
                return 'Folder Name cannot be empty!';
            }
            const cleaned = value.trim().replace(/[^a-zA-Z0-9-_]/g, '');
            if (cleaned !== value.trim()) {
                return 'Folder Name must be continuous without accents or special characters!';
            }
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const newName = result.value.trim();
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/site/{{ site.id }}/edit-folder/${oldFolder}`;
            
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'new_folder_name';
            input.value = newName;
            form.appendChild(input);
            
            document.body.appendChild(form);
            form.submit();
        }
    });
}

function deleteFolder(folder) {
    Swal.fire({
        title: `Confirm delete folder /${folder}?`,
        text: 'Child pages inside this folder will automatically be moved to the Root Folder and corresponding code files will be moved out.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/site/{{ site.id }}/delete-folder/${folder}`;
            document.body.appendChild(form);
            form.submit();
        }
    });
}


// --- SPLIT VIEW LOGIC ---
let siteMenus = {{ site.menus | tojson | safe }} || [];
let currentTreeFilterIds = null; // null means show all, otherwise array of leaf node ids to show

// Pagination State
let currentPage = 1;
let pageSize = 25;

document.addEventListener('DOMContentLoaded', () => {
    populateFolderSelects();
    renderMenuTree();
    
    // Restore View Preference
    const savedView = localStorage.getItem('siteDetailViewMode') || 'list';
    toggleView(savedView);
    
    // Apply initial pagination and filtering
    applyFilters();
});

function renderMenuTree() {
    const container = document.getElementById('site-menu-tree-container');
    if (siteMenus.length === 0) {
        container.innerHTML = '<div class="text-center p-3 text-muted">No menus found.</div>';
        return;
    }
    
    const treeHTML = buildTreeHTML(siteMenus, null);
    container.innerHTML = `
        <style>.tree-active, .tree-active span, .tree-active i { color: #fff !important; }</style>
        <div class="p-2">${treeHTML}</div>
    `;
}

function buildTreeHTML(menus, parentId) {
    const children = menus.filter(m => (m.parent_id || null) === (parentId || null));
    if (children.length === 0) return '';
    
    let html = '<ul class="list-unstyled pl-0 mb-0" style="margin-left: ' + (parentId ? '12px' : '0') + '">';
    children.sort((a, b) => (a.order || 0) - (b.order || 0)).forEach(node => {
        const hasChildren = menus.some(m => m.parent_id === node.id);
        
        if (hasChildren) {
            html += `
                <li class="py-1">
                  <div class="d-flex align-items-center tree-node cursor-pointer p-1 rounded" onclick="toggleAndFilterTreeNode('${node.id}')" id="tree-node-ui-${node.id}" style="cursor: pointer;">
                    <i class="fas fa-chevron-right fa-xs fa-fw text-muted mr-1" id="tree-caret-${node.id}"></i>
                    <i class="fas fa-folder text-warning mr-2"></i> 
                    <span class="font-weight-bold">${node.name}</span>
                  </div>
                  <div class="tree-children" id="tree-children-${node.id}" style="display: none;">
                    ${buildTreeHTML(menus, node.id)}
                  </div>
                </li>
            `;
        } else {
            html += `
                <li class="py-1">
                  <div class="d-flex align-items-center tree-leaf cursor-pointer p-1 rounded" onclick="filterByLeafNode('${node.id}')" id="tree-node-ui-${node.id}" style="cursor: pointer; padding-left: 1.25rem !important;">
                    <i class="far fa-file-code text-secondary mr-2"></i>
                    <span>${node.name}</span>
                  </div>
                </li>
            `;
        }
    });
    html += '</ul>';
    return html;
}

function filterByLeafNode(nodeId) {
    currentTreeFilterIds = [nodeId];
    highlightTreeNode(nodeId);
    currentPage = 1;
    applyFilters();
}

function clearTreeFilter() {
    currentTreeFilterIds = null;
    highlightTreeNode(null);
    currentPage = 1;
    applyFilters();
}

function toggleAllChecks(checked) {
    const checkboxes = document.querySelectorAll('.menu-checkbox');
    checkboxes.forEach(cb => {
        // only check visible ones (to handle search filtering properly)
        const row = cb.closest('.page-card-wrapper');
        if (row && row.style.display !== 'none') {
            cb.checked = checked;
        }
    });
    const checkAllList = document.getElementById('check-all-list');
    const checkAllGlobal = document.getElementById('check-all-global');
    if (checkAllList) checkAllList.checked = checked;
    if (checkAllGlobal) checkAllGlobal.checked = checked;
    updateBulkActionsBtn();
}

function updateBulkActionsBtn() {
    const checkboxes = document.querySelectorAll('.menu-checkbox:checked');
    const visibleChecked = Array.from(checkboxes).filter(cb => {
        const row = cb.closest('.page-card-wrapper');
        return row && row.style.display !== 'none';
    });
    const values = new Set(visibleChecked.map(cb => cb.value));
    
    const count = values.size;
    const countSpan = document.getElementById('bulk-selected-count');
    countSpan.innerText = count;
}

function executeBulkAction(siteId) {
    const checkboxes = document.querySelectorAll('.menu-checkbox:checked');
    const visibleChecked = Array.from(checkboxes).filter(cb => {
        const row = cb.closest('.page-card-wrapper');
        return row && row.style.display !== 'none';
    });
    if (visibleChecked.length === 0) {
        Swal.fire('Info', 'Please check at least one page to apply the action.', 'info');
        return;
    }

    const action = document.getElementById('bulk-action-select').value;
    if (!action) {
        Swal.fire('Info', 'Please select an action from the dropdown first.', 'info');
        return;
    }
    
    if (action === 'generate') {
        bulkGenerateSelected(siteId);
    } else if (action === 'deploy') {
        bulkDeploySelected(siteId);
    } else if (action === 'delete') {
        bulkDeleteSelected(siteId);
    }
}

function bulkGenerateSelected(siteId) {
    const checkboxes = document.querySelectorAll('.menu-checkbox:checked');
    const values = Array.from(new Set(Array.from(checkboxes).map(cb => cb.value)));
    if (values.length === 0) return;
    
    const generateList = [];
    for (let val of values) {
        const sepIndex = val.indexOf('--');
        const folder = val.substring(0, sepIndex);
        const slug = val.substring(sepIndex + 2);
        
        const menu = siteMenus.find(m => (m.folder || '') === folder && m.slug === slug);
        if (menu && menu.figma_link) {
            generateList.push({ folder, slug, val });
        }
    }
    
    if (generateList.length === 0) {
        Swal.fire('Info', 'No selected pages have a Figma Link. Cannot generate.', 'info');
        return;
    }
    
    Swal.fire({
        title: `Generate ${generateList.length} pages?`,
        text: 'This will initiate generation for the selected pages in parallel.',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Yes, generate!',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            generateList.forEach(item => {
                let btn = document.getElementById(`generate-list-btn-${item.val}`);
                if (!btn || btn.closest('.page-card-wrapper').style.display === 'none') {
                    btn = document.getElementById(`generate-grid-btn-${item.val}`);
                }
                if (btn) {
                    generateFiles(siteId, item.val, btn);
                }
            });
        }
    });
}

function bulkDeploySelected(siteId) {
    const checkboxes = document.querySelectorAll('.menu-checkbox:checked');
    const values = Array.from(new Set(Array.from(checkboxes).map(cb => cb.value)));
    if (values.length === 0) return;
    
    const deployList = [];
    for (let val of values) {
        const sepIndex = val.indexOf('--');
        const folder = val.substring(0, sepIndex);
        const slug = val.substring(sepIndex + 2);
        
        // Ensure it is generated before allowing deploy
        const menu = siteMenus.find(m => (m.folder || '') === folder && m.slug === slug);
        if (menu && menu.generated) {
            deployList.push({ folder, slug, val });
        }
    }
    
    if (deployList.length === 0) {
        Swal.fire('Info', 'No generated pages selected to deploy. Please generate them first.', 'info');
        return;
    }
    
    Swal.fire({
        title: `Deploy ${deployList.length} pages?`,
        text: 'This will initiate deployment for the selected generated pages.',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Yes, deploy!',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            let startedCount = 0;
            deployList.forEach(item => {
                // Find button to show spinner
                const btn = document.getElementById(`deploy-list-form-${item.val}`) || document.getElementById(`deploy-grid-form-${item.val}`);
                if (btn) {
                    btn.dataset.original = btn.innerHTML;
                    btn.disabled = true;
                    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                }
                
                $.ajax({
                    url: '/api/deploy',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        site_id: siteId,
                        menu_slug: item.slug,
                        folder: item.folder
                    }),
                    success: function() {
                        startedCount++;
                        if (startedCount === deployList.length) {
                            checkDeployStatus();
                        }
                    }
                });
            });
            Swal.fire('Started', `Initiated deployment for ${deployList.length} pages. Watch the status on each item.`, 'success');
        }
    });
}

function bulkDeleteSelected(siteId) {
    const checkboxes = document.querySelectorAll('.menu-checkbox:checked');
    const items = [];
    const seen = new Set();
    checkboxes.forEach(cb => {
        const id = cb.id.replace('check-list-', '').replace('check-grid-', '');
        if (!seen.has(id)) {
            seen.add(id);
            items.push({ id: id, param: cb.value });
        }
    });
    if (items.length === 0) return;
    
    Swal.fire({
        title: `Delete ${items.length} items?`,
        text: 'Are you sure you want to delete these? All generated files will be removed permanently.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, delete!',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({ title: 'Deleting...', text: 'Please wait.', allowOutsideClick: false, didOpen: () => { Swal.showLoading(); }});
            $.ajax({
                url: `/site/${siteId}/bulk-delete-menus`,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ items: items }),
                success: function(response) {
                    if (response.success) {
                        items.forEach(item => {
                            const listCb = document.getElementById(`check-list-${item.id}`);
                            if (listCb) {
                                const tr = listCb.closest('tr');
                                if (tr) tr.remove();
                            }
                            const gridCb = document.getElementById(`check-grid-${item.id}`);
                            if (gridCb) {
                                const wrapper = gridCb.closest('.page-card-wrapper');
                                if (wrapper) wrapper.remove();
                            }
                            const treeNode = document.getElementById(`tree-node-ui-${item.id}`);
                            if (treeNode) {
                                const li = treeNode.closest('li');
                                if (li) li.remove();
                            }
                            siteMenus = siteMenus.filter(m => m.id !== item.id);
                        });
                        Swal.fire('Deleted!', `Successfully deleted ${response.deleted_count} items.`, 'success');
                        applyFilters();
                        updateBulkActionsBtn();
                    } else {
                        Swal.fire('Error', response.message || 'Could not delete items.', 'error');
                    }
                },
                error: function() {
                    Swal.fire('Error', 'Connection error.', 'error');
                }
            });
        }
    });
}

function updateLayout(siteId, menuId, newLayout) {
    $.ajax({
        url: `/site/${siteId}/update-layout/${menuId}`,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ layout: newLayout }),
        success: function(response) {
            if (response.success) {
                Swal.fire({ toast: true, position: 'top-end', showConfirmButton: false, timer: 1500, icon: 'success', title: 'Layout saved' });
                
                const menu = siteMenus.find(m => m.id === menuId);
                if (menu) {
                    menu.layout = newLayout;
                    const editBtns = document.querySelectorAll(`button[data-folder="${menu.folder || ''}"][data-slug="${menu.slug || ''}"]`);
                    editBtns.forEach(btn => btn.setAttribute('data-layout', newLayout));
                }
            } else {
                Swal.fire({ toast: true, position: 'top-end', showConfirmButton: false, timer: 3000, icon: 'error', title: 'Error', text: response.message });
            }
        },
        error: function() {
            Swal.fire({ toast: true, position: 'top-end', showConfirmButton: false, timer: 3000, icon: 'error', title: 'Connection Error', text: 'Please try again.' });
        }
    });
}

function buildSelectOptionsHTML(menus, parentId, level) {
    let html = '';
    const children = menus.filter(m => (m.parent_id || null) === (parentId || null));
    children.sort((a, b) => (a.order || 0) - (b.order || 0)).forEach(node => {
        const prefix = '&nbsp;&nbsp;&nbsp;&nbsp;'.repeat(level) + (level > 0 ? '↳ ' : '');
        html += `<option value="${node.id}">${prefix}${node.name}</option>`;
        html += buildSelectOptionsHTML(menus, node.id, level + 1);
    });
    return html;
}

function populateFolderSelects() {
    const optionsHTML = '<option value="">Root Folder (Root)</option>' + buildSelectOptionsHTML(siteMenus, null, 0);
    const addSelect = document.getElementById('folder');
    const editSelect = document.getElementById('edit_folder');
    if (addSelect) addSelect.innerHTML = optionsHTML;
    if (editSelect) editSelect.innerHTML = optionsHTML;
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

function highlightTreeNode(nodeId) {
    document.querySelectorAll('[id^="tree-node-ui-"]').forEach(el => el.classList.remove('bg-primary', 'text-white', 'tree-active'));
    if (nodeId) {
        const el = document.getElementById(`tree-node-ui-${nodeId}`);
        if (el) el.classList.add('bg-primary', 'text-white', 'tree-active');
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
        btnList.classList.replace('btn-outline-primary', 'btn-primary');
        btnGrid.classList.replace('btn-primary', 'btn-outline-primary');
    } else {
        listView.style.display = 'none';
        gridView.style.display = 'flex';
        btnList.classList.replace('btn-primary', 'btn-outline-primary');
        btnGrid.classList.replace('btn-outline-primary', 'btn-primary');
    }
}

function filterPages() {
    currentPage = 1;
    applyFilters();
}

function applyFilters() {
    const query = document.getElementById('pageSearchInput').value.toLowerCase().trim();
    const allItems = document.querySelectorAll('.page-card-wrapper');
    const noResults = document.getElementById('noPageSearchResults');
    
    // Separate into TRs and DIVs (they correspond 1:1 in order)
    const trs = [];
    const divs = [];
    allItems.forEach(el => {
        if(el.tagName === 'TR') trs.push(el);
        else divs.push(el);
    });
    
    const matchedIndices = [];
    
    for (let i = 0; i < trs.length; i++) {
        const item = trs[i];
        const folder = item.getAttribute('data-folder');
        const slug = item.getAttribute('data-slug');
        const menu = siteMenus.find(m => (m.folder || '') === folder && m.slug === slug);
        const menuId = menu ? menu.id : null;
        
        const titleEl = item.querySelector('.font-weight-bold');
        const titleText = titleEl ? titleEl.textContent.toLowerCase() : '';
        const slugText = slug.toLowerCase();
        const matchesQuery = titleText.includes(query) || slugText.includes(query);
        
        let matchesTree = true;
        if (currentTreeFilterIds !== null && menuId) {
            matchesTree = currentTreeFilterIds.includes(menuId);
        }
        
        if (matchesQuery && matchesTree) {
            matchedIndices.push(i);
        }
        
        // Hide all initially
        item.style.setProperty('display', 'none', 'important');
        if (divs[i]) divs[i].style.setProperty('display', 'none', 'important');
    }
    
    // Calculate Pagination
    const totalPages = Math.ceil(matchedIndices.length / pageSize);
    if (currentPage > totalPages && totalPages > 0) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;
    
    const startIdx = (currentPage - 1) * pageSize;
    const endIdx = Math.min(startIdx + pageSize, matchedIndices.length);
    
    // Show only the elements for the current page
    for (let j = startIdx; j < endIdx; j++) {
        const originalIdx = matchedIndices[j];
        trs[originalIdx].style.setProperty('display', 'table-row', 'important');
        if (divs[originalIdx]) divs[originalIdx].style.setProperty('display', 'block', 'important');
    }
    
    // No results message
    if (noResults) {
        if (matchedIndices.length === 0 && trs.length > 0) {
            noResults.style.display = 'block';
        } else {
            noResults.style.display = 'none';
        }
        
        const displayedCountEl = document.getElementById('displayed-pages-count');
        if (displayedCountEl) {
            displayedCountEl.innerText = matchedIndices.length;
        }
        
        updateBulkActionsBtn();
    }
    
    updatePaginationUI(totalPages);
}

function updatePaginationUI(totalPages) {
    const ul = document.getElementById('pagination-ul');
    if (!ul) return;
    ul.innerHTML = '';
    
    if (totalPages <= 1) {
        ul.innerHTML = `<li class="page-item active"><a class="page-link" href="javascript:void(0)">1</a></li>`;
        return;
    }
    
    // Prev
    const prevDisabled = currentPage === 1 ? 'disabled' : '';
    ul.innerHTML += `<li class="page-item ${prevDisabled}"><a class="page-link" href="javascript:void(0)" onclick="goToPage(${currentPage - 1})">«</a></li>`;
    
    // Pages
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        ul.innerHTML += `<li class="page-item"><a class="page-link" href="javascript:void(0)" onclick="goToPage(1)">1</a></li>`;
        if (startPage > 2) ul.innerHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
    }
    
    for (let p = startPage; p <= endPage; p++) {
        const active = p === currentPage ? 'active' : '';
        ul.innerHTML += `<li class="page-item ${active}"><a class="page-link" href="javascript:void(0)" onclick="goToPage(${p})">${p}</a></li>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) ul.innerHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        ul.innerHTML += `<li class="page-item"><a class="page-link" href="javascript:void(0)" onclick="goToPage(${totalPages})">${totalPages}</a></li>`;
    }
    
    // Next
    const nextDisabled = currentPage === totalPages ? 'disabled' : '';
    ul.innerHTML += `<li class="page-item ${nextDisabled}"><a class="page-link" href="javascript:void(0)" onclick="goToPage(${currentPage + 1})">»</a></li>`;
}

function goToPage(p) {
    currentPage = p;
    applyFilters();
}

function changePageSize() {
    pageSize = parseInt(document.getElementById('pageSizeSelect').value, 10);
    currentPage = 1;
    applyFilters();
}
