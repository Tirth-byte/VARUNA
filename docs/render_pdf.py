import os
import re
import subprocess
from pathlib import Path

def md_to_html(md_text: str) -> str:
    lines = md_text.splitlines()
    html_lines = []
    in_table = False
    in_code = False
    table_header_done = False
    
    for line in lines:
        stripped = line.strip()
        
        # Code blocks
        if stripped.startswith("```"):
            if in_code:
                html_lines.append("</pre>")
                in_code = False
            else:
                lang = stripped[3:].strip()
                html_lines.append(f'<pre class="code-block {lang}">')
                in_code = True
            continue
        if in_code:
            html_lines.append(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            continue
            
        # Tables
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(set(c).issubset({"-", ":", " "}) for c in cells):
                # separator
                table_header_done = True
                continue
            if not in_table:
                html_lines.append('<div class="table-container"><table>')
                in_table = True
                table_header_done = False
                html_lines.append("<thead><tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr></thead><tbody>")
            else:
                html_lines.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
            continue
        else:
            if in_table:
                html_lines.append("</tbody></table></div>")
                in_table = False
                table_header_done = False
                
        # Headings
        if stripped.startswith("# "):
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("### "):
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("#### "):
            html_lines.append(f"<h4>{stripped[5:]}</h4>")
        elif stripped.startswith("---"):
            html_lines.append("<hr/>")
        elif stripped.startswith("> "):
            html_lines.append(f"<blockquote>{stripped[2:]}</blockquote>")
        elif stripped.startswith("* ") or stripped.startswith("- "):
            html_lines.append(f"<li>{stripped[2:]}</li>")
        elif stripped.startswith("1. ") or stripped.startswith("2. ") or stripped.startswith("3. ") or stripped.startswith("4. ") or stripped.startswith("5. "):
            html_lines.append(f'<li class="ordered">{stripped[3:]}</li>')
        elif stripped:
            html_lines.append(f"<p>{stripped}</p>")
            
    if in_table:
        html_lines.append("</tbody></table></div>")
    if in_code:
        html_lines.append("</pre>")
        
    raw_html = "\n".join(html_lines)
    
    # Inline formatting: bold, italic, links, mathjax-style formatting
    raw_html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", raw_html)
    raw_html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", raw_html)
    raw_html = re.sub(r"`([^`]+?)`", r"<code>\1</code>", raw_html)
    raw_html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', raw_html)
    
    # Wrap lists
    raw_html = re.sub(r"(<li>.*?</li>\n?)+", r"<ul>\g<0></ul>", raw_html)
    raw_html = re.sub(r'(<li class="ordered">.*?</li>\n?)+', r"<ol>\g<0></ol>", raw_html)
    
    return raw_html

def build_pdf():
    md_path = Path("docs/RESEARCH_REPORT_TRISHULI_FLOOD_2026.md")
    md_content = md_path.read_text(encoding="utf-8")
    
    body_html = md_to_html(md_content)
    
    # High-quality printable CSS
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>VARUNA: Evidence-Grounded Flood and Accessibility Mapping from Satellite Imagery</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 12mm 14mm 12mm 14mm;
    @bottom-right {{
      content: "Page " counter(page) " of " counter(pages);
      font-size: 8pt;
      color: #666;
    }}
  }}
  *, *::before, *::after {{
    box-sizing: border-box;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 8.5pt;
    line-height: 1.35;
    color: #1a202c;
    background: #fff;
    margin: 0;
    padding: 0;
  }}
  h1 {{
    font-size: 15pt;
    line-height: 1.2;
    margin: 0 0 4px 0;
    color: #0f172a;
    font-weight: 800;
  }}
  h2 {{
    font-size: 11pt;
    line-height: 1.25;
    margin: 12px 0 4px 0;
    color: #1e3a8a;
    border-bottom: 1.5px solid #cbd5e1;
    padding-bottom: 2px;
    font-weight: 700;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 9.5pt;
    line-height: 1.3;
    margin: 8px 0 3px 0;
    color: #1e293b;
    font-weight: 600;
    page-break-after: avoid;
  }}
  h4 {{
    font-size: 8.5pt;
    margin: 6px 0 2px 0;
    color: #334155;
    font-weight: 600;
  }}
  p {{
    margin: 0 0 5px 0;
    text-align: justify;
  }}
  hr {{
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 6px 0;
  }}
  blockquote {{
    margin: 4px 0;
    padding: 4px 8px;
    background: #f8fafc;
    border-left: 3px solid #3b82f6;
    font-size: 8pt;
    color: #334155;
  }}
  ul, ol {{
    margin: 2px 0 6px 16px;
    padding: 0;
  }}
  li {{
    margin-bottom: 2px;
  }}
  code {{
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
    font-size: 7.5pt;
    background: #f1f5f9;
    padding: 1px 3px;
    border-radius: 2px;
    color: #0f172a;
  }}
  pre.code-block {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 6px;
    font-size: 7.5pt;
    line-height: 1.25;
    overflow-x: hidden;
    white-space: pre-wrap;
    margin: 4px 0 6px 0;
    page-break-inside: avoid;
  }}
  .table-container {{
    margin: 6px 0;
    page-break-inside: avoid;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 7.5pt;
    line-height: 1.25;
  }}
  th, td {{
    border: 1px solid #cbd5e1;
    padding: 3px 5px;
    text-align: left;
  }}
  th {{
    background: #f1f5f9;
    color: #0f172a;
    font-weight: 600;
  }}
  tr:nth-child(even) td {{
    background: #f8fafc;
  }}
  .figure-grid {{
    display: flex;
    gap: 8px;
    margin: 6px 0;
    page-break-inside: avoid;
  }}
  .figure-box {{
    flex: 1;
    border: 1px solid #cbd5e1;
    padding: 4px;
    background: #fafafa;
    border-radius: 4px;
    text-align: center;
  }}
  .figure-box img {{
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
    max-height: 140px;
  }}
  .figure-caption {{
    font-size: 7pt;
    color: #475569;
    margin-top: 3px;
    font-weight: 500;
  }}
</style>
</head>
<body>
{body_html}

<div class="figure-grid">
  <div class="figure-box">
    <img src="../data/demo_evidence/map_1_trishuli_flood_hazard_overview.png" alt="Trishuli Flood Hazard Overview" />
    <div class="figure-caption"><strong>Figure 1:</strong> Trishuli River Valley Sentinel-1 SAR change classification map showing candidate inundation (cyan) and debris/roughening (orange).</div>
  </div>
  <div class="figure-box">
    <img src="../data/demo_evidence/map_2_bidur_infrastructure_exposure_detail.png" alt="Bidur Infrastructure Exposure" />
    <div class="figure-caption"><strong>Figure 2:</strong> High-resolution exposure detail at Bidur confluence showing surveyed buildings, roads, and EMSR927 optical truth.</div>
  </div>
</div>

</body>
</html>"""

    html_path = Path("docs/research_report_print.html")
    html_path.write_text(html_doc, encoding="utf-8")
    print(f"Wrote printable HTML to {html_path}")

    pdf_path = Path("docs/RESEARCH_REPORT_TRISHULI_FLOOD_2026.pdf")
    cmd = [
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={pdf_path.resolve()}",
        f"file://{html_path.resolve()}"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("Brave exit code:", res.returncode)
    
    if pdf_path.exists():
        pdf_bytes = pdf_path.read_bytes()
        # Count pages
        page_count = len(re.findall(rb"/Type\s*/Page\b", pdf_bytes))
        print(f"Generated PDF size: {len(pdf_bytes)} bytes, Page Count: {page_count}")
        if page_count <= 6:
            print(f"SUCCESS: Page count {page_count} is <= 6 pages!")
        else:
            print(f"WARNING: Page count {page_count} exceeds 6 pages!")

if __name__ == "__main__":
    build_pdf()
