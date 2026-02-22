"""
Generate PDF from the architecture document.
Converts markdown → styled HTML → PDF (via Edge/Chrome headless).
"""

import markdown
import subprocess
import os
import shutil
import sys

MD_PATH = os.path.join(os.path.dirname(__file__), "project_architecture_document.md")
HTML_PATH = os.path.join(os.path.dirname(__file__), "project_architecture_document.html")
PDF_PATH = os.path.join(os.path.dirname(__file__), "project_architecture_document.pdf")

CSS = """
@page {
    size: A4;
    margin: 2cm 2.2cm 2cm 2.2cm;
}

@media print {
    body { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
    pre, table, .section { page-break-inside: avoid; }
    h2 { page-break-before: always; }
    h2:first-of-type { page-break-before: avoid; }
}

* { box-sizing: border-box; }

body {
    font-family: 'Segoe UI', 'David', 'Arial', sans-serif;
    direction: rtl;
    text-align: right;
    line-height: 1.75;
    color: #1a1a2e;
    background: #ffffff;
    max-width: 210mm;
    margin: 0 auto;
    padding: 1cm;
    font-size: 11pt;
}

/* Title */
h1 {
    text-align: center;
    font-size: 26pt;
    color: #1e3a5f;
    border-bottom: 4px solid #3B82F6;
    padding-bottom: 15px;
    margin-bottom: 5px;
    letter-spacing: 1px;
}

h1 + h2 {
    text-align: center;
    color: #64748b;
    font-size: 14pt;
    font-weight: 400;
    border: none;
    margin-top: 0;
    padding: 0;
    page-break-before: avoid !important;
}

/* Section headers */
h2 {
    color: #1e3a5f;
    font-size: 18pt;
    border-bottom: 3px solid #3B82F6;
    padding-bottom: 8px;
    margin-top: 35px;
}

h3 {
    color: #2563EB;
    font-size: 14pt;
    margin-top: 25px;
    border-right: 4px solid #3B82F6;
    padding-right: 12px;
}

h4 {
    color: #475569;
    font-size: 12pt;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 10pt;
    direction: rtl;
}

th {
    background: linear-gradient(135deg, #1e3a5f, #2563EB);
    color: white;
    padding: 10px 12px;
    text-align: right;
    font-weight: 600;
}

td {
    padding: 8px 12px;
    border-bottom: 1px solid #e2e8f0;
    text-align: right;
    vertical-align: top;
}

tr:nth-child(even) {
    background-color: #f8fafc;
}

tr:hover {
    background-color: #eff6ff;
}

/* Code blocks */
pre {
    background: #0f172a;
    color: #e2e8f0;
    padding: 16px 20px;
    border-radius: 10px;
    overflow-x: auto;
    font-size: 9pt;
    line-height: 1.5;
    direction: ltr;
    text-align: left;
    border-left: 4px solid #3B82F6;
    margin: 15px 0;
}

code {
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 9.5pt;
}

/* Inline code */
p code, li code, td code {
    background: #eff6ff;
    color: #1e40af;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 9.5pt;
    direction: ltr;
    unicode-bidi: embed;
}

/* Lists */
ul, ol {
    padding-right: 25px;
    padding-left: 0;
}

li {
    margin-bottom: 4px;
}

/* Horizontal rule */
hr {
    border: none;
    height: 2px;
    background: linear-gradient(to left, transparent, #3B82F6, transparent);
    margin: 30px 0;
}

/* Strong / Bold */
strong {
    color: #1e3a5f;
}

/* Blockquote */
blockquote {
    border-right: 4px solid #3B82F6;
    border-left: none;
    margin: 15px 0;
    padding: 10px 20px;
    background: #eff6ff;
    border-radius: 0 8px 8px 0;
    color: #1e40af;
}

/* Star highlight sections */
h3:has(+ p > strong) {
    color: #d97706;
}

/* Emoji rendering */
td:first-child {
    font-size: 11pt;
}

/* Links */
a {
    color: #2563EB;
    text-decoration: none;
}

/* Print-specific */
@media print {
    body {
        padding: 0;
        font-size: 10.5pt;
    }
    pre {
        font-size: 8.5pt;
        padding: 10px 14px;
    }
    table { font-size: 9.5pt; }
    h2 { font-size: 16pt; }
    h3 { font-size: 12pt; }
}
"""


def find_browser():
    """Find Edge or Chrome executable."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    # Try shutil.which
    for name in ["msedge", "chrome", "google-chrome"]:
        found = shutil.which(name)
        if found:
            return found
    return None


def md_to_html(md_path: str) -> str:
    """Convert markdown file to styled HTML."""
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_body = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
    )

    html_doc = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Travel Agent — מסמך ארכיטקטורה</title>
    <style>{CSS}</style>
</head>
<body>
{html_body}
</body>
</html>"""
    return html_doc


def main():
    print("[1/3] Converting Markdown to HTML...")
    html_content = md_to_html(MD_PATH)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"      HTML saved: {HTML_PATH}")

    print("[2/3] Looking for browser (Edge/Chrome)...")
    browser = find_browser()
    if not browser:
        print("      ERROR: Could not find Edge or Chrome!")
        print(f"      You can open the HTML file manually and print to PDF:")
        print(f"      {HTML_PATH}")
        return

    browser_name = "Edge" if "edge" in browser.lower() else "Chrome"
    print(f"      Found {browser_name}: {browser}")

    print("[3/3] Converting HTML to PDF (headless)...")
    abs_html = os.path.abspath(HTML_PATH)
    abs_pdf = os.path.abspath(PDF_PATH)

    result = subprocess.run(
        [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--print-to-pdf={abs_pdf}",
            "--print-to-pdf-no-header",
            f"file:///{abs_html.replace(os.sep, '/')}",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if os.path.isfile(abs_pdf) and os.path.getsize(abs_pdf) > 1000:
        size_kb = os.path.getsize(abs_pdf) / 1024
        print(f"\n      PDF created successfully! ({size_kb:.0f} KB)")
        print(f"      {abs_pdf}")
    else:
        print(f"\n      PDF generation may have failed.")
        if result.stderr:
            print(f"      stderr: {result.stderr[:300]}")
        print(f"\n      Alternative: Open the HTML in a browser and print to PDF:")
        print(f"      {abs_html}")


if __name__ == "__main__":
    main()
