# companies/utils/word_to_pdf.py
import os
import shutil
import subprocess
import tempfile
import uuid

class LibreOfficeError(RuntimeError):
    pass

def convert_docx_to_pdf(docx_bytes: bytes) -> bytes:
    """
    Convert DOCX bytes to PDF bytes using LibreOffice (soffice) in headless mode.
    Works inside your Docker image where LibreOffice is installed.
    """
    # Find the binary (Render/Debian images expose it as 'soffice')
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise LibreOfficeError("LibreOffice/soffice binary not found in PATH.")

    with tempfile.TemporaryDirectory() as tmpdir:
        base = f"input-{uuid.uuid4().hex}"
        in_path = os.path.join(tmpdir, f"{base}.docx")
        out_pdf = os.path.join(tmpdir, f"{base}.pdf")

        # Write incoming DOCX bytes
        with open(in_path, "wb") as f:
            f.write(docx_bytes)

        # Run LibreOffice conversion
        # Note: writer_pdf_Export gives good fidelity for Word-like docs
        cmd = [
            soffice,
            "--headless",
            "--nologo",
            "--nolockcheck",
            "--nodefault",
            "--invisible",
            "--convert-to", "pdf:writer_pdf_Export",
            "--outdir", tmpdir,
            in_path,
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120
        )

        # LibreOffice sometimes returns 0 even if it fails; check for output file
        if not os.path.exists(out_pdf):
            output = result.stdout.decode(errors="ignore")
            raise LibreOfficeError(f"LibreOffice failed to convert DOCX → PDF.\nCommand: {' '.join(cmd)}\nOutput:\n{output}")

        with open(out_pdf, "rb") as f:
            return f.read()
