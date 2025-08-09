from django.db import models
from django.core.validators import RegexValidator

# Only digits and exactly 5 digits
postcode_validator = RegexValidator(regex=r'^\d{5}$', message='Postcode must be exactly 5 digits.')

# Dropdown choices for AMR branch
BRANCH_CHOICES = [
    ('HQ', 'HQ'),
    ('CHERAS', 'Cheras'),
    ('SHAH ALAM', 'Shah Alam'),
    ('SKUDAI', 'Skudai'),
    ('KUANTAN', 'Kuantan'),
]

# Company Model
class Company(models.Model):
    company_name = models.CharField(max_length=255, blank=True, null=True)
    ssm_number = models.CharField(max_length=50, unique = True)
    incorporation_date = models.DateField(blank=True, null=True)
    amr_cosec_branch = models.CharField(
        max_length=50,
        blank=True, null=True,
        choices=BRANCH_CHOICES,
        default='HQ'
    )

    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    address_line3 = models.CharField(max_length=255, blank=True)
    postcode = models.CharField(max_length=5, blank=True, null=True, validators=[postcode_validator])
    town = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)

    nature_of_business_1 = models.CharField(max_length=255)
    nature_of_business_2 = models.CharField(max_length=255, blank=True)
    nature_of_business_3 = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if self.company_name:
            self.company_name = self.company_name.upper()
        if self.ssm_number:
            self.ssm_number = self.ssm_number.upper()
        if self.address_line1:
            self.address_line1 = self.address_line1.upper()
        if self.address_line2:
            self.address_line2 = self.address_line2.upper()
        if self.address_line3:
            self.address_line3 = self.address_line3.upper()
        if self.postcode:
            self.postcode = self.postcode.upper()
        if self.town:
            self.town = self.town.upper()
        if self.state:
            self.state = self.state.upper()
        if self.nature_of_business_1:
            self.nature_of_business_1 = self.nature_of_business_1.upper()
        if self.nature_of_business_2:
            self.nature_of_business_2 = self.nature_of_business_2.upper()
        if self.nature_of_business_3:
            self.nature_of_business_3 = self.nature_of_business_3.upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.company_name or "Unnamed Company"


# Director Model
class Director(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=255)
    ic_passport = models.CharField(max_length=50, blank=True, null=True)
    
    # Professional address format
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    address_line3 = models.CharField(max_length=255, blank=True)
    postcode = models.CharField(max_length=5, blank=True, null=True, validators=[postcode_validator])
    town = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)

    phone_number = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)

    appointment_date = models.DateField()
    resignation_date = models.DateField(blank=True, null=True)
    is_shareholder = models.BooleanField(default=False)
    is_contact_person = models.BooleanField(default=False)  # ✅ NEW FIELD

    def __str__(self):
        return self.full_name


# Shareholder Model
class Shareholder(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=255)
    ic_passport = models.CharField(max_length=50, blank=True, null=True)

    # Professional address format
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    address_line3 = models.CharField(max_length=255, blank=True)
    postcode = models.CharField(max_length=5, blank=True, null=True, validators=[postcode_validator])
    town = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)

    phone_number = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    is_contact_person = models.BooleanField(default=False)  # ✅ NEW FIELD

    shareholding = models.PositiveIntegerField()
    shareholder_type = models.CharField(
        max_length=50,
        choices=[
            ('ordinary', 'Ordinary Shareholder'),
            ('preference', 'Preference Shareholder'),
            ('other', 'Other'),
        ],
        default='ordinary'
    )

    def __str__(self):
        return self.full_name

# Contact Person Model
class ContactPerson(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='contactperson')
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    position = models.CharField(max_length=100)

    def __str__(self):
        return self.name

from django.db import models

class ComplianceInformation(models.Model):
    company = models.OneToOneField('Company', on_delete=models.CASCADE, related_name='compliance_info')

    # Auditor
    auditor_name = models.CharField(max_length=255, blank=True, null=True)
    license_number = models.CharField(max_length=100, blank=True, null=True)
    aud_address_line1 = models.CharField(max_length=255, blank=True, null=True)
    aud_address_line2 = models.CharField(max_length=255, blank=True)
    aud_address_line3 = models.CharField(max_length=255, blank=True)
    aud_postcode = models.CharField(max_length=5, blank=True, null=True, validators=[postcode_validator])
    aud_town = models.CharField(max_length=100, blank=True, null=True)
    aud_state = models.CharField(max_length=100, blank=True, null=True)

    # Tax Agent
    tax_agent_name = models.CharField(max_length=255, blank=True, null=True)
    ssm_number = models.CharField(max_length=100, blank=True, null=True)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    address_line3 = models.CharField(max_length=255, blank=True)
    postcode = models.CharField(max_length=5, blank=True, null=True, validators=[postcode_validator])
    town = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)

    # FYE
    financial_year_end = models.CharField(
        max_length=20,
        help_text="Format: e.g. 31 December or 30 September",
        blank=True,
        null=True
    )

    # Statutory filings
    latest_annual_return_filed = models.DateField(blank=True, null=True)
    latest_financial_statement_filed = models.DateField(blank=True, null=True)

    # Beneficial Owner Declaration
    beneficial_owner_declaration = models.CharField(
        max_length=10,
        choices=[('Declared', 'Declared'), ('Pending', 'Pending')],
        default='Pending'
    )

    def __str__(self):
        return f"Compliance Info - {self.company.company_name}"

