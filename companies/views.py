import os
import tempfile
import requests
from datetime import date
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import DirectorForm
from .models import Company, DocumentTemplate  # ✅ Needed for document generation
from docxtpl import DocxTemplate  # ✅ New import for document auto generator

import io
import zipfile
from itertools import zip_longest
from django.utils.text import slugify



# === Existing Functions ===

def import_directors(request):
    if request.method == 'POST':
        # Later we'll handle file upload here
        pass
    else:
        download_url = reverse('download_director_template')
        return render(request, 'mysecretarysystem/import_directors.html', {
            'download_url': download_url
        })


def download_director_template(request):
    file_path = os.path.join(
        settings.BASE_DIR,
        'mysecretarysystem',
        'static',
        'mysecretarysystem',
        'director_import_template.xlsx'
    )
    
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='director_import_template.xlsx')
    else:
        return render(request, 'mysecretarysystem/error.html', {
            'message': 'Template file not found.'
        })


def add_director(request):
    if request.method == 'POST':
        form = DirectorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('success')  # ✅ Make sure 'success' is a valid URL name
    else:
        form = DirectorForm()

    return render(request, 'director_form.html', {'form': form})


# === New Function for Document Auto Generation ===

def choose_template(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    templates = DocumentTemplate.objects.all().order_by('-created_at')

    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        if template_id:
            return redirect('generate_company_doc', company_id=company.id, template_id=int(template_id))
    # GET: show form
    return render(request, 'companies/choose_template.html', {
        'company': company,
        'templates': templates,
    })


def generate_company_doc(request, company_id, template_id):
    company = get_object_or_404(Company, id=company_id)
    doc_template = get_object_or_404(DocumentTemplate, id=template_id)

    # Keep your existing mapping (unchanged)

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

        # helper: group into pairs using zip_longest
        pairs = list(zip_longest(*(iter(director_list),) * 2, fillvalue=None))

        director_rows = []
        for left, right in pairs:
            left_dict = {'name': left.full_name, 'ic': getattr(left, 'ic_passport', '')} if left else None
            right_dict = {'name': right.full_name, 'ic': getattr(right, 'ic_passport', '')} if right else None
            director_rows.append({'left': left_dict, 'right': right_dict})


        base_context = {
            "company_name": company.company_name or '',
            "ssm_number": company.ssm_number or '',
            "incorporation_date": safe_date(company.incorporation_date),
            "amr_cosec_branch": getattr(company, 'amr_cosec_branch', ''),
            "generated_date": date.today().strftime("%d %B %Y"),
            # For templates using loops (docxtpl Jinja):
            "directors": [{"name": d.full_name, "ic": getattr(d, 'ic_passport', '')} for d in directors_qs],
            "shareholders": [{"name": s.full_name, "ic": getattr(s, 'ic_passport', '')} for s in shareholders_qs],
        }
        
        base_context["director_rows"] = director_rows

        # ---- Per-director mode: create one file per director and return a ZIP ----
        if getattr(doc_template, "per_director", False):
            directors = list(directors_qs)
            if not directors:
                return HttpResponse("No directors found for this company.", status=400)

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for director in directors:
                    # Copy base context and add director-specific keys
                    ctx = dict(base_context)  # shallow copy
                    ctx.update({
                        "director_name": director.full_name or '',
                        "director_ic": getattr(director, 'ic_passport', '') or '',
                        "director_address": getattr(director, 'residential_address', '') or '',
                        "director_email": getattr(director, 'email', '') or '',
                        # add any other director fields you use in templates
                    })

                    # Load fresh DocxTemplate from the temp file for each director
                    doc = DocxTemplate(tmp_path)
                    doc.render(ctx)

                    # Save the rendered doc into a BytesIO
                    doc_io = io.BytesIO()
                    doc.save(doc_io)
                    doc_io.seek(0)

                    # safe filename
                    safe_director = slugify(director.full_name) or "director"
                    safe_company = slugify(company.company_name) or "company"
                    file_name = f"{safe_company}_{safe_director}_{doc_template.name}.docx"

                    # write into the zip
                    zip_file.writestr(file_name, doc_io.read())

            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
            response['Content-Disposition'] = f'attachment; filename="{slugify(company.company_name or "company")}_directors.zip"'
            return response

        # ---- Normal single-document generation (unchanged behaviour) ----
        # Build the full context (keeps loop-based placeholders working too)
        context = dict(base_context)

        # Also keep individual director/shareholder placeholders in case the template uses them:
        # Fill director_1_name...director_N_name for backwards compatibility (optional)
        for i, d in enumerate(directors_qs, start=1):
            context[f"director_{i}_name"] = d.full_name or ''
            context[f"director_{i}_ic"] = getattr(d, 'ic_passport', '') or ''

        for i in range(len(directors_qs) + 1, 6):  # keep up to 5 slots for backwards compatibility
            context[f"director_{i}_name"] = ''
            context[f"director_{i}_ic"] = ''

        for i, s in enumerate(shareholders_qs, start=1):
            context[f"shareholder_{i}_name"] = s.full_name or ''

        for i in range(len(shareholders_qs) + 1, 6):
            context[f"shareholder_{i}_name"] = ''

        # Render single document
        doc = DocxTemplate(tmp_path)
        doc.render(context)

        filename = f"{company.company_name or 'company'}_{doc_template.name}.docx"
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        doc.save(response)
        return response

    finally:
        # cleanup temp file
        try:
            os.remove(tmp_path)
        except Exception:
            pass


