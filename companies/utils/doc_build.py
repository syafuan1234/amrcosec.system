# companies/utils/doc_build.py
import io
from docxtpl import DocxTemplate

def build_context(company):
    """Everything your .docx template needs (used by BOTH preview and email)."""
    ctx = {"company": company, "include_signature": True}

    # Example: arrange directors 2 per row for the signature table
    directors = list(company.director_set.order_by("id").values("full_name"))
    rows = []
    for i in range(0, len(directors), 2):
        left = directors[i]
        right = directors[i+1] if i+1 < len(directors) else None
        rows.append({"left": left, "right": right})
    ctx["director_rows"] = rows

    return ctx

def render_docx_bytes(doc_template_path: str, context: dict) -> bytes:
    """Render a DocxTemplate to bytes (no temp files)."""
    tpl = DocxTemplate(doc_template_path)
    tpl.render(context)
    buf = io.BytesIO()
    tpl.save(buf)
    return buf.getvalue()
