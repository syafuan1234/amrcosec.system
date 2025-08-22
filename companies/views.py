import os
import tempfile
import requests
import io
import zipfile
import subprocess

from datetime import date
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import DirectorForm
from .models import Company, DocumentTemplate, Director, EmailTemplate  # ✅ Needed for document generation
from docxtpl import DocxTemplate  # ✅ New import for document auto generator
from django.utils.text import slugify
from collections import defaultdict
from django.core.mail import EmailMessage
from .utils.word_to_pdf import convert_docx_to_pdf
from django.contrib import messages
from docx import Document

# === New Function for Document Auto Generation ===

# companies/views.py
def choose_email_template(request, company_id, template_id):
    company = get_object_or_404(Company, id=company_id)
    doc_template = get_object_or_404(DocumentTemplate, id=template_id)
    templates = EmailTemplate.objects.all()

    # Collect recipient emails
    director_emails = list(
        company.director_set.exclude(email="").values_list("email", flat=True)
    )

    # Handle one-to-one ContactPerson safely
    contact_person_emails = []
    if hasattr(company, "contactperson") and company.contactperson.email:
        contact_person_emails.append(company.contactperson.email)

    # Merge directors + contact person, remove duplicates
    recipients = ", ".join(set(director_emails + contact_person_emails))

    if request.method == "POST":
        recipient = request.POST.get("recipient")
        subject = request.POST.get("subject")
        body = request.POST.get("body")

        # --- Generate DOCX (same as in generate_company_doc) ---
        r = requests.get(doc_template.github_url)
        if r.status_code != 200:
            messages.error(request, "Failed to fetch document template.")
            return redirect("choose_template", company_id=company.id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(r.content)
            tmp_path = tmp.name

        try:
            doc = DocxTemplate(tmp_path)

            # Basic context (you can expand if needed)
            context = {
                "company_name": company.company_name or '',
                "ssm_number": company.ssm_number or '',
                "generated_date": date.today().strftime("%d %B %Y"),
            }
            doc.render(context)

            buf = io.BytesIO()
            doc.save(buf)
            buf.seek(0)

            pdf_bytes = convert_docx_to_pdf_bytes(buf.getvalue())

            # --- Send email ---
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[r.strip() for r in recipient.split(",") if r.strip()],
            )
            email.attach(f"{company.company_name}_document.pdf", pdf_bytes, "application/pdf")
            email.send()

            messages.success(request, "✅ Email sent successfully!")
            return redirect("admin:companies_company_changelist")

        finally:
            os.remove(tmp_path)

    return render(request, "companies/choose_email_template.html", {
        "company": company,
        "email_templates": templates,
        "recipients": recipients,
    })


def choose_template(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    directors = company.director_set.all()  # ✅ always matches the related directors

    # ✅ Group templates by category
    templates = DocumentTemplate.objects.all().order_by("category", "name")
    templates_by_category = defaultdict(list)
    for t in templates:
        templates_by_category[t.category].append(t)

    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        director_id = request.POST.get('director_id')  # ✅ capture director choice

        template = get_object_or_404(DocumentTemplate, pk=template_id)

        # ✅ Fetch selected directors
        if director_id == "all":
            selected_directors = directors
        else:
            selected_directors = directors.filter(pk=director_id)

        if template_id:
            action = request.POST.get('action', 'generate')  # 👈 which button was clicked
            url = reverse(
                'generate_company_doc_with_director',
                kwargs={
                    'company_id': company.id,
                    'template_id': int(template_id),
                    'director_id': director_id or "all"
                }
            )
            # 👇 carry the action across the redirect so we don't lose it
            return redirect(f"{url}?action={action}")

    # GET: show form
    return render(request, 'companies/choose_template.html', {
        'company': company,
        'templates_by_category': templates_by_category.items(),  # ✅ now grouped
        "templates": templates, 
        'directors': directors,
    })


def generate_company_doc(request, company_id, template_id, director_id=None):
    company = get_object_or_404(Company, id=company_id)
    doc_template = get_object_or_404(DocumentTemplate, id=template_id)

    template_url = doc_template.github_url
    if not template_url:
        return HttpResponse("No GitHub URL set for this template.", status=400)

    # Download the file from GitHub
    r = requests.get(template_url)
    if r.status_code != 200:
        return HttpResponse("Error downloading template from GitHub.", status=500)

    # Save to a temporary file so DocxTemplate can load it
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(r.content)
        tmp_path = tmp.name

    try:
        # helper for dates
        def safe_date(dt):
            return dt.strftime("%Y-%m-%d") if dt else ''

        # Base context used for single-doc generation and as part of per-director generation
        directors_qs = company.director_set.all()
        shareholders_qs = company.shareholder_set.all()

        # create director_rows = [ {'left': {...} or None, 'right': {...} or None}, ... ]
        director_list = list(directors_qs)  # list of Director model instances

        from itertools import zip_longest
        pairs = list(zip_longest(*(iter(director_list),) * 2, fillvalue=None))

        director_rows = []
        for left, right in pairs:
            left_dict = {
                'name': left.full_name if left else '',
                'line': '___________________'
            } if left else None

            right_dict = {
                'name': right.full_name if right else '',
                'line': '___________________'
            } if right else None

            director_rows.append({
                'left': left_dict,
                'right': right_dict
            })

        base_context = {
            "company_name": company.company_name or '',
            "ssm_number": company.ssm_number or '',
            "incorporation_date": safe_date(company.incorporation_date),
            "amr_cosec_branch": getattr(company, 'amr_cosec_branch', ''),
            "generated_date": date.today().strftime("%d %B %Y"),
            "directors": [{"name": d.full_name, "ic": getattr(d, 'ic_passport', '')} for d in directors_qs],
            "shareholders": [{"name": s.full_name, "ic": getattr(s, 'ic_passport', '')} for s in shareholders_qs],
            "director_rows": director_rows
        }
        
        # ✅ Detect user action (Download, Preview, or Email)
        action = request.GET.get("action", "generate")

        # === New: handle specific director selection ===
        if director_id and director_id != "all":
            director = get_object_or_404(company.director_set, id=director_id)
            ctx = dict(base_context)
            ctx.update({
                "director_name": director.full_name or '',
                "director_ic": getattr(director, 'ic_passport', '') or '',
                "director_address": getattr(director, 'residential_address', '') or '',
                "director_email": getattr(director, 'email', '') or '',
            })
            doc = DocxTemplate(tmp_path)
            doc.render(ctx)
            filename = f"{slugify(company.company_name)}_{slugify(director.full_name)}_{doc_template.name}.docx"

            # Default: download Word
            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            doc.save(response)
            return response

        # ---- Per-director mode: create one file per director and return a ZIP ----
        if getattr(doc_template, "per_director", False):
            directors = list(directors_qs)
            if not directors:
                return HttpResponse("No directors found for this company.", status=400)

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for director in directors:
                    ctx = dict(base_context)
                    ctx.update({
                        "director_name": director.full_name or '',
                        "director_ic": getattr(director, 'ic_passport', '') or '',
                        "director_address": getattr(director, 'residential_address', '') or '',
                        "director_email": getattr(director, 'email', '') or '',
                    })

                    doc = DocxTemplate(tmp_path)
                    doc.render(ctx)

                    doc_io = io.BytesIO()
                    doc.save(doc_io)
                    doc_io.seek(0)

                    safe_director = slugify(director.full_name) or "director"
                    safe_company = slugify(company.company_name) or "company"
                    file_name = f"{safe_company}_{safe_director}_{doc_template.name}.docx"

                    zip_file.writestr(file_name, doc_io.read())

            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
            response['Content-Disposition'] = f'attachment; filename="{slugify(company.company_name or "company")}_directors.zip"'
            return response

        # ---- Normal single-document generation ----
        context = dict(base_context)

        for i, d in enumerate(directors_qs, start=1):
            context[f"director_{i}_name"] = d.full_name or ''
            context[f"director_{i}_ic"] = getattr(d, 'ic_passport', '') or ''

        for i in range(len(directors_qs) + 1, 6):
            context[f"director_{i}_name"] = ''
            context[f"director_{i}_ic"] = ''

        for i, s in enumerate(shareholders_qs, start=1):
            context[f"shareholder_{i}_name"] = s.full_name or ''

        for i in range(len(shareholders_qs) + 1, 6):
            context[f"shareholder_{i}_name"] = ''

        doc = DocxTemplate(tmp_path)
        doc.render(context)

        filename = f"{company.company_name or 'company'}_{doc_template.name}"

        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        # Save generated DOCX file first
        safe_company = slugify(company.company_name) or "company"
        output_path = os.path.join(settings.MEDIA_ROOT, f"{safe_company}_{int(date.today().strftime('%Y%m%d'))}.docx")
        doc.save(output_path)

        # Handle action: preview, email, or download Word
        if action == "preview":
            buf = io.BytesIO()
            doc.save(buf)
            buf.seek(0)
            pdf_bytes = convert_docx_to_pdf_bytes(buf.getvalue())  # ✅ use helper
            return HttpResponse(pdf_bytes, content_type="application/pdf")


        elif action == "email":
            # Instead of sending directly, redirect to choose_email_template page
            return redirect(
                "choose_email_template",
                company_id=company.id,
                template_id=doc_template.id,
            )

            # Read the generated DOCX back into memory
            with open(output_path, "rb") as f:
                docx_bytes = f.read()

            # Convert to PDF
            pdf_bytes = convert_docx_to_pdf_bytes(docx_bytes)

            # Clean up the temporary DOCX
            os.remove(output_path)

            # Send email with PDF attached
            email = EmailMessage(
                subject=f"Document for {company.company_name}",
                body="Dear Client,\n\nPlease find attached the requested document.\n\nBest regards,\nYour Company",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=["client@example.com"],  # TODO: replace with actual client email(s)
            )
            email.attach(f"{company.company_name}.pdf", pdf_bytes, "application/pdf")
            email.send()
            messages.success(request, "Email sent successfully.")
            return redirect("admin:companies_company_changelist")


        else:
            # Default: download Word
            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}.docx"'
            doc.save(response)
            return response


    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def convert_docx_to_pdf_bytes(docx_bytes):
    """Convert DOCX bytes into PDF bytes using LibreOffice."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        input_path = os.path.join(tmpdirname, "input.docx")
        output_dir = tmpdirname
        output_path = os.path.join(output_dir, "input.pdf")

        # Write DOCX to temp file
        with open(input_path, "wb") as f:
            f.write(docx_bytes)

        # Run LibreOffice headless conversion
        subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", output_dir, input_path],
            check=True,
        )

        # Read back PDF as bytes
        with open(output_path, "rb") as f:
            pdf_bytes = f.read()

    return pdf_bytes
