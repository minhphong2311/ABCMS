# ABCMS - CMS Page Deployer & Builder

**ABCMS** is a web application and automation tool specifically designed to support and streamline the deployment of frontend code (HTML, CSS, JS) directly into the **Jiniworks CMS**.

It helps developers preview designs and automatically push source code from their local environment to the target Jiniworks CMS, eliminating the need for manual copy-pasting through complex CMS admin interfaces.

---

## 🚀 Key Features

1. **CMS Site Management**:
   - Add, edit, and delete target website configurations (Site ID, Name, URL, Credentials).
   - Support for custom CSS guidelines (`css_guide`) per site.

2. **Visual Builder & Page Management**:
   - Intuitive drag-and-drop interface for managing nested menus, pages, and directory structures.
   - Configure individual HTML, CSS, and JavaScript settings for each page or layout.

3. **AI-Powered Automation**:
   - **Smart Slug Generation**: Integrates with Google's Gemini API (`gemini-flash-latest`) to automatically translate and summarize Korean menu titles into short, SEO-friendly English URL slugs (e.g., `부동산AI융합학과` -> `real-estate-ai`).
   - **Batch Excel Import**: Upload Excel files of site structures, and the AI will batch translate hundreds of missing slugs in just a few seconds.
   - **Auto-Deduplication**: Ensures globally unique URLs by automatically appending numeric suffixes (e.g., `-2`, `-3`) to identically named pages.
   - **Auto-Folder Assignment**: Intelligently derives folder structures by cascading root slugs down to descendant nodes.

4. **Playwright Automation (Auto Deploy)**:
   - Automated headless/headed login to the CMS.
   - Direct navigation to the Page Manager.
   - Automated folder creation on the CMS tree.
   - Verifies if a page (JSP/HTML) exists:
     - **If new**: Creates the page, selects the template layout, and configures titles/files.
     - **If existing**: Selects the target page and opens the editor.
   - Injects HTML, CSS, and JS code into the CMS editors (e.g., Froala, CodeMirror).
   - Automatically saves and finalizes the deployment.

---

## 📂 Project Structure

```text
├── app.py                # Main Flask server running the web builder dashboard
├── automation.py         # Playwright script for CMS login and code deployment
├── check_cms.py          # Script to inspect CMS DOM structure and connectivity
├── check_folders.py      # Helper script for folder validation
├── inspect_*.py          # Debugging scripts for UI, pages, and Figma
├── test_deploy.py        # Sandbox script for testing deployment workflows
├── data/                 # Local JSON database and configurations
│   ├── sites.json        # Managed CMS site list
│   └── config.json       # Global system settings (including Gemini API keys)
├── templates/            # Flask Jinja2 HTML templates
└── .gitignore            # Git exclusion rules
```

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- Python 3.8+

### 2. Install Dependencies
Open your terminal and run:
```bash
pip install flask playwright asyncio google-genai openpyxl requests
playwright install chromium
```

### 3. Launch the Web Dashboard
Start the local Flask server:
```bash
python app.py
```
Then navigate to [http://localhost:5000](http://localhost:5000) in your web browser.

### 4. Configuration
Ensure you have set up your API keys in the dashboard's settings panel (e.g., Gemini API Key) to enable AI features.

### 5. Automated Deployment (CLI)
You can test the deployment workflow directly via the CLI:
```bash
python test_deploy.py
```

---

## 💻 Tech Stack
- **Backend**: Python, Flask (Dashboard UI and API)
- **AI Integration**: Google GenAI SDK (`gemini-flash-latest` model)
- **Automation**: Playwright (Headless browser control)
- **Database**: Flat JSON files in the `data/` directory for lightweight, portable data persistence.
