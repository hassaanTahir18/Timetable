import requests
from bs4 import BeautifulSoup
import time
import re
import json

def compile_cui_timetable():
    base_url = "https://sfs.cuilahore.edu.pk/schedule/public/timetable"

    # Helper to fetch dropdown options dynamically (Updated for new JS array format)
    def get_options(kind, dept=None):
        params = {"Kind": kind}
        if dept:
            params["Dept"] = dept

        res = requests.get(base_url, params=params)
        soup = BeautifulSoup(res.text, 'html.parser')

        if not dept:
            # Departments are still in a standard <select> tag
            select = soup.find('select', {'name': 'Dept'})
            if not select:
                return [], soup
            return [opt['value'] for opt in select.find_all('option') if opt.get('value')], soup
        else:
            # Classes and Faculty are now hidden inside a JS array: const all = [...];
            match = re.search(r'const all = (\[.*?\]);', res.text)
            if match:
                try:
                    # json.loads perfectly parses a JS string array into a Python list
                    items = json.loads(match.group(1))
                    return items, soup
                except json.JSONDecodeError:
                    print(f"Error parsing array for {dept}")
                    return [], soup
            return [], soup

    print("Fetching departments...")
    departments, initial_soup = get_options("class")

    classes_html, faculty_html = "", ""
    head_html = str(initial_soup.find('head'))

    for dept in departments:
        print(f"\n--- Processing Department: {dept} ---")

        # 1. Fetch Students/Classes
        classes, _ = get_options("class", dept)
        print(f"  -> Fetching {len(classes)} classes...")
        for cls in classes:
            res = requests.get(base_url, params={"Kind": "class", "Dept": dept, "Who": cls})
            soup = BeautifulSoup(res.text, 'html.parser')
            sheet = soup.find('div', class_='sheetwrap')
            if sheet:
                classes_html += str(sheet) + "<div class='page-break-divider'></div>"
            time.sleep(0.2)

        # 2. Fetch Faculty
        teachers, _ = get_options("teacher", dept)
        print(f"  -> Fetching {len(teachers)} faculty members...")
        for teacher in teachers:
            res = requests.get(base_url, params={"Kind": "teacher", "Dept": dept, "Who": teacher})
            soup = BeautifulSoup(res.text, 'html.parser')
            sheet = soup.find('div', class_='sheetwrap')
            if sheet:
                faculty_html += str(sheet) + "<div class='page-break-divider'></div>"
            time.sleep(0.2)

    # Master HTML payload with UI Tabs
   # Master HTML payload with UI Tabs
    master_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    {head_html}
    <style>
        /* UNIFIED HEADER CSS (Matches builder.html exactly, no sticky positioning) */
        body {{ font-family: system-ui, -apple-system, sans-serif; background: #f1f5f9; margin: 0; color: #0f172a; }}
        .custom-nav {{ display: flex; align-items: center; justify-content: space-between; padding: 16px 24px; background: #ffffff; border-bottom: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); }}
        .nav-left {{ flex: 1; display: flex; flex-direction: column; gap: 2px; }}
        .nav-left h1 {{ font-size: 1.15rem; font-weight: 700; margin: 0; letter-spacing: -0.02em; }}
        .nav-left p {{ font-size: 0.78rem; color: #64748b; margin: 0; font-style: italic; }}
        
        .nav-center {{ flex: 1; display: flex; justify-content: center; }}
        .tab-group {{ display: flex; background: #f1f5f9; padding: 4px; border-radius: 8px; gap: 4px; }}
        .tab-group a {{ text-decoration: none; padding: 8px 18px; font-size: 0.85rem; font-weight: 600; border-radius: 6px; color: inherit; }}
        .tab-group a.active {{ background: #ffffff; color: #0f172a; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); }}
        
        .nav-right {{ flex: 1; display: flex; justify-content: flex-end; }}
        .print-btn {{ padding: 8px 16px; background: #0f172a; color: white; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; transition: 0.2s; }}
        .print-btn:hover {{ background: #1e293b; }}

        /* LOCAL FILTER TABS (Classes vs Faculty) */
        .local-filters {{ display: flex; justify-content: center; padding: 12px; background: #fff; border-bottom: 1px solid #e2e8f0; gap: 10px; }}
        .filter-btn {{ padding: 6px 16px; border: 1px solid #cbd5e1; background: #f8fafc; border-radius: 20px; font-size: 0.85rem; font-weight: 600; cursor: pointer; color: #475569; transition: 0.2s; }}
        .filter-btn:hover {{ background: #e2e8f0; }}
        .filter-btn.active {{ background: #0f172a; color: white; border-color: #0f172a; }}

        /* MOBILE RESPONSIVENESS */
        @media (max-width: 768px) {{
            .custom-nav {{ flex-direction: column; align-items: flex-start; gap: 15px; padding: 16px; }}
            .nav-left, .nav-center, .nav-right {{ flex: none; width: 100%; }}
            .nav-center, .nav-right {{ justify-content: flex-start; }}
        }}

        @media print {{
            .noprint {{ display: none !important; }}
            body {{ background: #fff; }}
        }}
    </style>
    <body>
        <!-- GLOBAL APP NAV -->
        <div class="custom-nav noprint">
            <div class="nav-left">
                <h1>ComSucks Timetable Combined</h1>
                <p>For god sake give us a simple pdf file from next time! Don't fix which isn't broken.</p>
            </div>
            <div class="nav-center">
                <div class="tab-group">
                    <a href="index.html" class="active">Master Schedule</a>
                    <a href="builder.html">Custom Builder ⚡</a>
                </div>
            </div>
            <div class="nav-right">
                <button class="print-btn" onclick="window.print()">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16" style="vertical-align: -2px; margin-right: 4px;"><path d="M2.5 8a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/><path d="M5 1a2 2 0 0 0-2 2v2H2a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h1v1a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-1h1a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-1V3a2 2 0 0 0-2-2H5zM4 3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2H4V3zm1 5a2 2 0 0 0-2 2v1H2a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v-1a2 2 0 0 0-2-2H5zm7 2v3a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1z"/></svg>
                    Download PDF
                </button>
            </div>
        </div>

        <!-- LOCAL DATA FILTER -->
        <div class="local-filters noprint">
            <button class="filter-btn active" onclick="switchTab(event, 'classes')">Students View</button>
            <button class="filter-btn" onclick="switchTab(event, 'faculty')">Faculty View</button>
        </div>

        <div id="classes" class="tab-content" style="display: block;">
            {classes_html}
        </div>
        <div id="faculty" class="tab-content" style="display: none;">
            {faculty_html}
        </div>

        <script>
            function switchTab(evt, tabName) {{
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tab-content");
                for (i = 0; i < tabcontent.length; i++) {{
                    tabcontent[i].style.display = "none";
                }}
                
                // Update active state on the local filter buttons
                tablinks = document.getElementsByClassName("filter-btn");
                for (i = 0; i < tablinks.length; i++) {{
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                }}
                
                document.getElementById(tabName).style.display = "block";
                evt.currentTarget.className += " active";
            }}
        </script>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(master_html)
    print("Extraction complete! Output saved to index.html")

if __name__ == "__main__":
    compile_cui_timetable()