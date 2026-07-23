import sys
import os

file_path = os.path.join('d:\\', 'Projects', 'test04', 'templates', 'site_detail.html')
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1
card_inner_html = ''

for i, line in enumerate(lines):
    if '<!-- List of Pages Search & Add Button -->' in line:
        start_idx = i
    if '<!-- Add Page Modal (Add Page) -->' in line:
        end_idx = i
        break

# Extracted from lines 102 to 213 (0-indexed -> 101 to 212)
card_inner_html = ''.join(lines[101:213])

new_content = """
<!-- Main Split Layout -->
<div class="row">
  <!-- Left Pane: Menu Tree -->
  <div class="col-md-4 col-lg-3">
    <div class="card card-outline card-primary h-100">
      <div class="card-header bg-light py-2">
        <h3 class="card-title font-weight-bold mb-0 text-dark" style="font-size: 1.1rem;"><i class="fas fa-sitemap mr-2"></i>{{ site.name }}</h3>
      </div>
      <div class="card-body p-0 bg-white" id="site-menu-tree-container" style="overflow-y: auto; max-height: 800px;">
        <div class="text-center p-4 text-muted"><i class="fas fa-spinner fa-spin"></i> Loading tree...</div>
      </div>
    </div>
  </div>

  <!-- Right Pane: List/Grid Views -->
  <div class="col-md-8 col-lg-9">
    <!-- List of Pages Search & Add Button -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <!-- Page Search Input -->
      <div class="input-group" style="max-width: 400px;">
        <div class="input-group-prepend">
          <span class="input-group-text bg-white border-right-0"><i class="fas fa-search text-muted"></i></span>
        </div>
        <input type="text" id="pageSearchInput" class="form-control border-left-0" placeholder="Search Page..." onkeyup="filterPages()">
      </div>
      
      <!-- Action Buttons & View Toggle -->
      <div>
        <div class="btn-group mr-3" role="group" aria-label="View Toggle">
          <button type="button" class="btn btn-secondary" id="btn-list-view" onclick="toggleView('list')"><i class="fas fa-list"></i></button>
          <button type="button" class="btn btn-outline-secondary" id="btn-grid-view" onclick="toggleView('grid')"><i class="fas fa-th-large"></i></button>
        </div>
        <button type="button" class="btn btn-outline-primary mr-2" data-toggle="modal" data-target="#addFolderModal">
          <i class="fas fa-folder mr-1"></i> Manage Folder
        </button>
        <button type="button" class="btn btn-primary" data-toggle="modal" data-target="#addMenuModal">
          <i class="fas fa-plus mr-1"></i> Add Page
        </button>
      </div>
    </div>

    <!-- Dynamic Page Search No Results message -->
    <div class="col-12" id="noPageSearchResults" style="display: none; width: 100%;">
      <div class="card py-5 text-center text-muted card-outline card-secondary">
        <i class="fas fa-search fa-3x mb-3 text-light"></i>
        <h5>No Pages match the search keyword.</h5>
      </div>
    </div>

    <!-- Views Container -->
    <div id="pages-view-container">

      {% set parent_ids = [] %}
      {% if site.menus %}
        {% for m in site.menus %}
          {% if m.parent_id %}
            {% set _ = parent_ids.append(m.parent_id) %}
          {% endif %}
        {% endfor %}
      {% endif %}

      {% set leaf_menus = [] %}
      {% if site.menus %}
        {% for m in site.menus %}
          {% if m.id not in parent_ids %}
            {% set _ = leaf_menus.append(m) %}
          {% endif %}
        {% endfor %}
      {% endif %}

      <!-- LIST VIEW -->
      <div id="list-view-container">
        {% if leaf_menus %}
        <div class="table-responsive bg-white rounded shadow-sm border mb-4">
          <table class="table table-hover mb-0 align-middle table-sm" style="min-width: 800px;">
            <thead class="bg-light text-muted">
              <tr>
                <th style="width: 250px;" class="border-top-0">Page Name</th>
                <th class="text-center border-top-0">Generated</th>
                <th class="text-center border-top-0">HTML</th>
                <th class="text-center border-top-0">Layout</th>
                <th class="text-center border-top-0">Tab</th>
                <th class="text-right border-top-0">Actions</th>
              </tr>
            </thead>
            <tbody>
              {% for menu in leaf_menus %}
              <tr class="page-card-wrapper" data-folder="{{ menu.folder or '' }}" data-slug="{{ menu.slug }}" data-parent-id="{{ menu.parent_id or '' }}">
                <td class="py-2">
                  <div class="d-flex align-items-center">
                    <i class="far fa-file-code text-secondary mr-2"></i>
                    <div>
                      <div class="font-weight-bold text-dark">{{ menu.name }}</div>
                      <div class="text-xs text-muted">{{ menu.slug }}.html</div>
                    </div>
                  </div>
                </td>
                <td class="text-center py-2">
                  {% if menu.generated %}<i class="fas fa-check-square text-success"></i>{% else %}<i class="far fa-square text-muted"></i>{% endif %}
                </td>
                <td class="text-center py-2">
                  <i class="fas fa-check-square text-success"></i>
                </td>
                <td class="text-center py-2">
                  {% if menu.layout and 'sub-template' in menu.layout %}<i class="fas fa-check-square text-success"></i>{% else %}<i class="far fa-square text-muted"></i>{% endif %}
                </td>
                <td class="text-center py-2">
                  {% if menu.layout == 'sub-template-tab' %}<i class="fas fa-check-square text-success"></i>{% else %}<i class="far fa-square text-muted"></i>{% endif %}
                </td>
                <td class="text-right py-2">
                  <div class="d-flex align-items-center justify-content-end">
                    <button type="button" class="btn btn-primary btn-sm page-action-btn mr-1" onclick="generateFiles('{{ site.id }}', '{{ menu.folder or '' }}--{{ menu.slug }}', this)" {% if not menu.figma_link %}disabled{% endif %} title="Generate"><i class="fas fa-cogs"></i></button>
                    <a href="/preview/{{ site.id }}/{{ menu.folder or '' }}--{{ menu.slug }}/" class="btn btn-success btn-sm page-action-btn mr-1" id="preview-list-btn-{{ menu.folder or '' }}--{{ menu.slug }}" onclick="this.href='/preview/{{ site.id }}/{{ menu.folder or '' }}--{{ menu.slug }}/?t=' + Date.now()" style="display: {% if menu.generated %}inline-block{% else %}none{% endif %};" title="Preview"><i class="fas fa-eye"></i></a>
                    <button class="btn btn-secondary btn-sm page-action-btn mr-1" disabled id="preview-list-disabled-{{ menu.folder or '' }}--{{ menu.slug }}" style="display: {% if menu.generated %}none{% else %}inline-block{% endif %};" title="Preview"><i class="fas fa-eye"></i></button>
                    
                    <button type="button" class="btn btn-info btn-sm page-action-btn mr-1" title="Deploy" onclick="deployFiles('{{ site.id }}', '{{ menu.slug }}', '{{ menu.folder or '' }}', '{{ menu.folder or '' }}--{{ menu.slug }}', this)" id="deploy-list-form-{{ menu.folder or '' }}--{{ menu.slug }}" style="display: {% if menu.generated %}inline-block{% else %}none{% endif %};"><i class="fas fa-cloud-upload-alt"></i></button>
                    <button class="btn btn-secondary btn-sm page-action-btn mr-1" disabled id="deploy-list-disabled-{{ menu.folder or '' }}--{{ menu.slug }}" style="display: {% if menu.generated %}none{% else %}inline-block{% endif %};" title="Deploy"><i class="fas fa-cloud-upload-alt"></i></button>
                    
                    <button type="button" class="btn btn-warning btn-sm text-white page-action-btn mr-1" title="Edit" data-name="{{ menu.name }}" data-folder="{{ menu.folder or '' }}" data-slug="{{ menu.slug }}" data-figma="{{ menu.figma_link }}" data-layout="{{ menu.layout }}" onclick="openEditMenuModal(this)"><i class="fas fa-edit"></i></button>
                  </div>
                </td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
        {% else %}
        <div class="col-12 px-0">
          <div class="card py-5 text-center text-muted card-outline card-secondary">
            <i class="fas fa-folder-open fa-3x mb-3 text-light"></i>
            <h5>No child pages have been set up. Click "Add New Page" to begin!</h5>
          </div>
        </div>
        {% endif %}
      </div>

      <!-- GRID VIEW -->
      <div class="row" id="grid-view-container" style="display: none;">
        {% if leaf_menus %}
          {% for menu in leaf_menus %}
""" + card_inner_html + """
          {% endfor %}
        {% endif %}
      </div>

    </div>
  </div>
</div>
"""

new_lines = lines[:start_idx] + [new_content] + lines[end_idx:]
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Updated HTML structure')
