import markdown
from weasyprint import HTML


CSS = """
body {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 12pt;
    line-height: 1.6;
    color: #222;
    max-width: 800px;
    margin: 0 auto;
    padding: 40px;
}
h1 { font-size: 22pt; margin-top: 1em; }
h2 { font-size: 18pt; margin-top: 0.8em; }
h3 { font-size: 14pt; margin-top: 0.6em; }
hr { border: none; border-top: 1px solid #ccc; margin: 1.5em 0; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; }
th { background: #f5f5f5; }
code { background: #f4f4f4; padding: 2px 4px; font-size: 0.9em; }
pre { background: #f4f4f4; padding: 12px; overflow-x: auto; }
"""


def markdown_to_pdf(md_content: str) -> bytes:
    """Convert a markdown string to PDF bytes."""
    html_body = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code"],
    )
    html_doc = (
        f"<!DOCTYPE html><html><head>"
        f"<meta charset='utf-8'>"
        f"<style>{CSS}</style>"
        f"</head><body>{html_body}</body></html>"
    )
    return HTML(string=html_doc).write_pdf()
