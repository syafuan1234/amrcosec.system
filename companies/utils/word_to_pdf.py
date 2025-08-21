import os
import subprocess
from django.conf import settings

def convert_docx_to_pdf(input_path, output_dir=None):
    """
    Convert a Word .docx file to PDF using LibreOffice.
    """
    if output_dir is None:
        output_dir = os.path.dirname(input_path)

    try:
        subprocess.run([
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            input_path,
            "--outdir", output_dir
        ], check=True)
        
        output_path = os.path.join(
            output_dir,
            os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
        )
        return output_path

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Conversion failed: {e}")
