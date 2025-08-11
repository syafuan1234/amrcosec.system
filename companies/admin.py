from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Company, Director, Shareholder, ContactPerson, ComplianceInformation
from import_export.admin import ExportMixin
from import_export import resources, fields
from django.forms.models import BaseInlineFormSet
from import_export.widgets import ForeignKeyWidget
from django.utils.html import format_html
from django.urls import reverse




# --- INLINE ADMIN CONFIGS ---

class DirectorInlineFormSet(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit)
        if form.cleaned_data.get('is_shareholder'):
            # Only create if not already a shareholder
            existing = Shareholder.objects.filter(
                company=obj.company,
                full_name=obj.full_name,
                ic_passport=obj.ic_passport
            ).exists()
            if not existing:
                Shareholder.objects.create(
                    company=obj.company,
                    full_name=obj.full_name,
                    ic_passport=obj.ic_passport,
                    address_line1=obj.address_line1,
                    address_line2=obj.address_line2,
                    address_line3=obj.address_line3,
                    postcode=obj.postcode,
                    town=obj.town,
                    state=obj.state,
                    phone_number=obj.phone_number,
                    email=obj.email,
                    shareholding=0,  # You can change default
                    shareholder_type='ordinary'
                )
        return obj
    
class DirectorInline(admin.StackedInline):
    model = Director
    formset = DirectorInlineFormSet
    extra = 1
    show_change_link = True
    fieldsets = [
        ('Basic Info', {
            'classes': ('collapse',),
            'fields': ('full_name', 'ic_passport', 'phone_number', 'email', 'is_shareholder', 'is_contact_person')
        }),
        ('Appointment Info', {
            'classes': ('collapse',),
            'fields': ('appointment_date', 'resignation_date')
        }),
        ('Address', {
            'classes': ('collapse', 'wide'),  # Collapse + custom style
            'fields': (
                ('address_line1', 'address_line2', 'address_line3'),
                ('postcode', 'town', 'state'),
            )
        }),
    ]

class ShareholderInline(admin.StackedInline):
    model = Shareholder
    extra = 0
    show_change_link = True
    fieldsets = [
        ('Basic Info', {
            'classes': ('collapse',),
            'fields': ('full_name', 'ic_passport', 'phone_number', 'email', 'is_contact_person')
        }),
        ('Shareholding Info', {
            'classes': ('collapse',),
            'fields': ('shareholding', 'shareholder_type')
        }),
        ('Address', {
            'classes': ('collapse', 'wide'),  # Collapse + custom style
            'fields': (
                ('address_line1', 'address_line2', 'address_line3'),
                ('postcode', 'town', 'state'),
            )
        }),
    ]

class ContactPersonInline(admin.StackedInline):
    model = ContactPerson
    extra = 0
    max_num = 1  # ✅ Allow only one contact person
    can_delete = True  # Optional: allow delete so a new one can be added later
    show_change_link = True

    fieldsets = [
        ('Contact Person Info', {
            'classes': ('collapse',),
            'fields': ('name', 'position', 'phone_number', 'email')
        }),
    ]

class ComplianceInformationInline(admin.StackedInline):
    model = ComplianceInformation
    extra = 0
    show_change_link = True
    fieldsets = [
        ('Auditor Info', {
            'classes': ('collapse', 'wide'),
            'fields': (
                ('auditor_name', 'license_number'), 
                ('aud_address_line1', 'aud_address_line2', 'aud_address_line3'),
                ('aud_postcode', 'aud_town', 'aud_state')
            )
        }),
        ('Tax Agent Info', {
            'classes': ('collapse', 'wide'),
            'fields': (
                ('tax_agent_name', 'ssm_number'), 
                ('address_line1', 'address_line2', 'address_line3'),
                ('postcode', 'town', 'state')
            )
        }),
        ('Statutory & Declaration', {
            'classes': ('collapse',),
            'fields': ('financial_year_end', 'latest_annual_return_filed', 'latest_financial_statement_filed', 'beneficial_owner_declaration')
        }),
    ]

class CompanyResource(resources.ModelResource):
    # Company fields
    company_name = fields.Field(attribute='company_name')
    ssm_number = fields.Field(attribute='ssm_number')
    incorporation_date = fields.Field(attribute='incorporation_date')
    amr_cosec_branch = fields.Field(attribute='amr_cosec_branch')

    # Compliance info
    fye = fields.Field(column_name='Financial Year End', attribute='compliance_info__financial_year_end')
    latest_ar = fields.Field(column_name='Latest Annual Return Filed', attribute='compliance_info__latest_annual_return_filed')
    latest_fs = fields.Field(column_name='Latest Financial Statement Filed', attribute='compliance_info__latest_financial_statement_filed')
    auditor = fields.Field(column_name='Auditor Name', attribute='compliance_info__auditor_name')
    tax_agent = fields.Field(column_name='Tax Agent Name', attribute='compliance_info__tax_agent_name')

    class Meta:
        model = Company
        import_id_fields = ['ssm_number']  # use this to check for existing records
        skip_unchanged = True
        report_skipped = True
        fields = (
            'id',
            'company_name',
            'ssm_number',
            'incorporation_date',
            'amr_cosec_branch',
            'fye',
            'latest_ar',
            'latest_fs',
            'auditor',
            'tax_agent',
        )
        

# --- MAIN ADMIN REGISTRATION ---

@admin.register(Company)
class CompanyAdmin(ImportExportModelAdmin, ExportMixin, admin.ModelAdmin):
    resource_class = CompanyResource

    list_display = ('company_name', 'ssm_number', 'incorporation_date', 'amr_cosec_branch', 'generate_doc_button')
    search_fields = ('company_name', 'ssm_number')
    inlines = [DirectorInline, ShareholderInline, ContactPersonInline, ComplianceInformationInline]

    def generate_doc_button(self, obj):
        url = reverse('choose_template', args=[obj.id])
        return format_html(
            '<a class="button" style="padding:3px 8px; background:#28a745; color:white; border-radius:3px; text-decoration:none;" href="{}">Generate Document</a>',
            url
        )
    generate_doc_button.short_description = "Document"
    

@admin.register(Director)
class DirectorAdmin(ImportExportModelAdmin):
    list_display = ('full_name', 'ic_passport', 'appointment_date', 'resignation_date', 'company')
    search_fields = ('full_name', 'ic_passport')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.is_shareholder:
            # Check if already exists to prevent duplication
            if not Shareholder.objects.filter(company=obj.company, full_name=obj.full_name).exists():
                Shareholder.objects.create(
                    company=obj.company,
                    full_name=obj.full_name,
                    ic_passport=obj.ic_passport,
                    address_line1=obj.address_line1,
                    address_line2=obj.address_line2,
                    address_line3=obj.address_line3,
                    postcode=obj.postcode,
                    town=obj.town,
                    state=obj.state,
                    phone_number=obj.phone_number,
                    email=obj.email,
                    shareholding=0,  # User needs to fill this later
                    shareholder_type='ordinary'
                )

@admin.register(Shareholder)
class ShareholderAdmin(ImportExportModelAdmin):
    list_display = ('full_name', 'ic_passport', 'shareholding', 'shareholder_type', 'company')
    search_fields = ('full_name', 'ic_passport')

@admin.register(ContactPerson)
class ContactPersonAdmin(ImportExportModelAdmin):
    list_display = ('name', 'position', 'phone_number', 'email', 'company')
    search_fields = ('name', 'email')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if not obj:  # Only restrict on Add form
            used_company_ids = ContactPerson.objects.values_list('company_id', flat=True)
            form.base_fields['company'].queryset = Company.objects.exclude(id__in=used_company_ids)

        return form

@admin.register(ComplianceInformation)
class ComplianceInformationAdmin(ImportExportModelAdmin):
    list_display = (
        'company',
        'auditor_name',
        'tax_agent_name',
        'financial_year_end',
        'latest_annual_return_filed',
        'latest_financial_statement_filed',
        'beneficial_owner_declaration',
    )
    search_fields = ('company__company_name', 'auditor_name', 'tax_agent_name')



