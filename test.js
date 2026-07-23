
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
                        if (statusInfo) statusInfo.innerHTML = `<span class="text-success"><i class="fas fa-check-circle mr-1"></i> ${task.message}</span>`;
                        
                        document.getElementById(`preview-btn-${menuSlug}`).style.display = 'inline-block';
                        document.getElementById(`preview-disabled-${menuSlug}`).style.display = 'none';
                        document.getElementById(`deploy-form-${menuSlug}`).style.display = 'inline-block';
                        document.getElementById(`deploy-disabled-${menuSlug}`).style.display = 'none';
                        
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

    document.getElementById('edit_menu_name').value = name;
    document.getElementById('edit_folder').value = folder;
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

let currentFolderFilter = 'all';

function filterByFolder(folder, btnElement) {
    currentFolderFilter = folder;
    
    // Update active class on filter buttons
    document.querySelectorAll('.folder-filter-btn').forEach(btn => {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-outline-primary');
    });
    btnElement.classList.remove('btn-outline-primary');
    btnElement.classList.add('btn-primary');
    
    // Apply filters
    applyFilters();
}

function filterPages() {
    applyFilters();
}

function applyFilters() {
    const query = document.getElementById('pageSearchInput').value.toLowerCase().trim();
    const cards = document.querySelectorAll('.page-card-wrapper');
    const noResults = document.getElementById('noPageSearchResults');
    let visibleCount = 0;
    
    cards.forEach(card => {
        // Extract folder and slug from composite ID: page-card-folder--slug
        const cardId = card.id.replace('page-card-', '');
        const parts = cardId.split('--');
        const folderPart = parts[0];
        const slugPart = parts[1] || cardId;
        
        const titleElement = card.querySelector('.card-title');
        const titleText = titleElement ? titleElement.textContent.toLowerCase() : '';
        const slugText = slugPart.toLowerCase();
        
        // Match query
        const matchesQuery = titleText.includes(query) || slugText.includes(query);
        
        // Match folder
        let matchesFolder = false;
        if (currentFolderFilter === 'all') {
            matchesFolder = true;
        } else if (currentFolderFilter === 'root') {
            matchesFolder = (folderPart === '');
        } else {
            matchesFolder = (folderPart === currentFolderFilter);
        }
        
        if (matchesQuery && matchesFolder) {
            card.style.setProperty('display', 'block', 'important');
            visibleCount++;
        } else {
            card.style.setProperty('display', 'none', 'important');
        }
    });
    
    if (noResults) {
        if (visibleCount > 0 || cards.length === 0) {
            noResults.style.display = 'none';
        } else {
            noResults.style.display = 'block';
        }
    }
}
