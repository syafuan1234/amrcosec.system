import os
from datetime import date
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import DirectorForm
from .models import Company, DocumentTemplate  # ✅ Needed for document generation
from docxtpl import DocxTemplate  # ✅ New import for document auto generator


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

    # file path on filesystem (works for local filesystem storage)
    template_path = doc_template.file.path

    # build context (safely convert dates)
    def safe_date(dt):
        return dt.strftime("%Y-%m-%d") if dt else ''

    context = {
        "company_name": company.company_name or '',
        "ssm_number": company.ssm_number or '',
        "incorporation_date": safe_date(company.incorporation_date),
        "amr_cosec_branch": getattr(company, 'amr_cosec_branch', ''),
        "generated_date": date.today().strftime("%d %B %Y"),
        # add more fields as needed
    }

    # render docx
    doc = DocxTemplate(template_path)
    doc.render(context)

    filename = f"{company.company_name or 'company'}_{doc_template.name}.docx"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    doc.save(response)
    return response
