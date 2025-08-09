import os
from datetime import date
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import DirectorForm
from .models import Company  # ✅ Needed for document generation
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

def generate_company_doc(request, company_id):
    # 1. Get company data
    company = get_object_or_404(Company, id=company_id)

    # 2. Load the Word template
    template_path = os.path.join(settings.BASE_DIR, 'templates', 'docs', 'template.docx')
    doc = DocxTemplate(template_path)

    # 3. Context for placeholders in template.docx
    context = {
        "company_name": company.company_name,
        "ssm_number": company.ssm_number,
        "incorporation_date": company.incorporation_date.strftime("%Y-%m-%d"),
        "today": date.today().strftime("%Y-%m-%d"),
    }

    # 4. Render the document with actual data
    doc.render(context)

    # 5. Prepare response for download
    filename = f"{company.company_name}_document.docx"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    doc.save(response)

    return response
