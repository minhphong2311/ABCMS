# ABCMS - Jiniworks CMS Page Deployer & Builder

**ABCMS** is a web application and automation tool specifically designed to support and streamline the deployment of frontend code (HTML, CSS, JS) directly into the **Jiniworks CMS**.

It helps developers preview designs and automatically push source code from their local environment to the target Jiniworks CMS, eliminating the need for manual copy-pasting through complex CMS admin interfaces.

---

## 🚀 Key Features

1. **CMS Site Management**:
   - Add, edit, and delete target website configurations (Site ID, Name, URL, Credentials).
   - Support for custom CSS guidelines (`css_guide`) per site.

2. **Visual Builder & Page Management**:
   - Intuitively drag-and-drop interface for managing nested menus, pages, and directory structures.
   - Configure individual HTML, CSS, and JavaScript settings for each page or layout.

3. **AI-Powered Automation & 100% Design Quality Matching**:
   - **Figma → HTML Quality Checklist (100% Precision)**: Iterative AI visual reflection loop enforcing a strict 7-step quality checklist (Layout, Typography, HTML & Class rules like `.con-box → h4`, `.con-box02 → h5`, `.con-box03 → h6`, Image export, Responsive layout, Interactive components, and Figma visual comparison).
   - **Gemini 3.6 Flash Engine**: Powered by Google's `gemini-3.6-flash` model with automatic model fallback retries for fast and reliable visual analysis.
   - **Smart Slug Generation**: Integrates with Google's Gemini API to automatically translate and summarize Korean menu titles into short, SEO-friendly English URL slugs (e.g., `부동산AI융합학과` -> `real-estate-ai`).
   - **Batch Excel Import**: Upload Excel files of site structures, and the AI will batch translate hundreds of missing slugs in just a few seconds.
   - **Auto-Deduplication & Folder Assignment**: Ensures globally unique URLs and intelligently derives folder structures.

4. **Playwright Automation (Auto Deploy & Image Sync)**:
   - **Playwright UI Mode Toggle**: Easily toggle Playwright between visible browser window (`headless=False`) and background mode (`headless=True`) directly in **System Settings**.
   - **Automated CMS Image Upload**: Scans local generated page images (`.jpg`, `.png`, etc.) and automatically uploads them into the CMS `content` resource folder (`#!/res-img`) via batch uploading.
   - **Automatic Image Path Replacement**: Automatically transforms local image paths in HTML (`<img src="...">`) and CSS (`background-image: url(...)`) to exact CMS resource URLs (`/_res/{res_org}/{site_id}/img/content/{filename}`).
   - **Page & Tree Manager Automation**: Automated login, folder creation, page existence check, template layout selection, and HTML/CSS/JS editor injection.

5. **UI & UX Standardizations**:
   - **Standardized Toast Notifications**: SweetAlert2 top-end toast notifications with timer progress bars and full Dark Mode support across all pages.
   - **Perfected Action Button Alignment**: Table rows are precision-centered vertically, ensuring all action buttons (Generate, Preview, Deploy, Edit, Delete) align perfectly for a cleaner and more polished UI.

---

## 📂 Project Structure

```text
├── app.py                # Main Flask server running the web builder dashboard
├── automation.py         # Playwright automation task engine for CMS deployment
├── deployer/             # Core deployment modules (site, menu, folder, upload, page)
├── routes/               # Flask blueprints for API routes (menu, site, deploy, generate)
├── assets/               # System resources (ai_prompts, layout templates, placeholder images)
├── data/                 # Local JSON database and configs (sites, config, cache)
├── static/               # Flask static files (CSS, JS) for the Web UI
├── templates/            # Flask Jinja2 HTML templates for the Web UI
└── scratch/              # Temporary folder for tests, DOM dumps, and debugging
```

---

## 🛠️ Installation & Setup

### Option 1: Automatic Setup via Antigravity AI (Recommended for Non-Developers)
If you don't have coding experience or want to save time, you can let the AI set everything up for you:
1. Clone or download this repository to your local machine.
2. Open the project folder in the **Antigravity IDE** (or Gemini IDE).
3. In the chat window, simply type: *"Please set up the environment and run this project for me"*.
4. The AI Agent will automatically read the project rules, install all dependencies (Python, Flask, Playwright, etc.), download the required browsers, and launch the web dashboard for you automatically!

### Option 2: Manual Setup (For Developers)

#### 1. Prerequisites
- Python 3.8+

#### 2. Install Dependencies
Open your terminal and run:
```bash
pip install flask playwright asyncio google-genai openpyxl requests pillow
playwright install chromium
```

### 3. Launch the Web Dashboard
Start the local Flask server:
```bash
python app.py
```
Then navigate to [http://localhost:5000](http://localhost:5000) in your web browser.

### 4. Configuration
Ensure you have set up your API keys and Playwright UI display mode in the dashboard's **System Settings** panel ([http://localhost:5000/settings](http://localhost:5000/settings)) to enable AI and automation features.

---

## 💻 Tech Stack
- **Backend**: Python, Flask (Dashboard UI and API)
- **AI Integration**: Google GenAI SDK (`gemini-3.6-flash` model)
- **Automation**: Playwright (Headless/Headed browser control)
- **Database**: Flat JSON files in the `data/` directory for lightweight, portable data persistence.

---

## 🌟 Recent Improvements
- **Figma → HTML Quality Checklist**: Auto-corrects compiled code against 7 strict design and project structure rules.
- **Automated CMS Image Upload & Path Sync**: Local page images are automatically uploaded into the CMS `content` folder and HTML/CSS paths are dynamically rewritten to `/_res/{res_org}/{site_id}/img/content/{filename}`.
- **Configurable Playwright UI Mode**: Toggle between `headless=False` and `headless=True` directly in System Settings.
- **Dark Mode Toasts & Table Alignment**: Unified top-end SweetAlert2 toasts and vertical-align centering for action buttons.
