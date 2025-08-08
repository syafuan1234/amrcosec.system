from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

from companies.models import Company, Director, ContactPerson

class Command(BaseCommand):
    help = 'Send 1st reminder 30 days before anniversary date'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        companies = Company.objects.all()

        for company in companies:
            if not company.incorporation_date:
                self.stdout.write(self.style.WARNING(f"❌ Skipped {company.company_name}: No incorporation date"))
                continue

            anniversary = company.incorporation_date.replace(year=today.year)

            # Handle edge case: anniversary already passed this year
            if anniversary < today:
                anniversary = anniversary.replace(year=today.year + 1)

            reminder_date = anniversary - timedelta(days=30)

            if today != reminder_date:
                continue  # Not the reminder day yet

            # Collect recipients
            recipients = []

            # Add all director emails
            directors = Director.objects.filter(company=company)
            for director in directors:
                if director.email and director.email not in recipients:
                    recipients.append(director.email)

            # Add contact person email if not in director list
            try:
                contact = ContactPerson.objects.get(company=company)
                if contact.email and contact.email not in recipients:
                    recipients.append(contact.email)
            except ContactPerson.DoesNotExist:
                pass  # No contact person

            if not recipients:
                self.stdout.write(self.style.WARNING(f"⚠️ No email found for {company.company_name}"))
                continue

            # Email content for 1st reminder
            subject = f"[First Reminder] Upcoming Annual Return Submission for {company.company_name}"
            message = f"""
Dear Sir/Madam,

We wish to inform you that your company’s anniversary date is approaching, and your Annual Return will soon be due for submission to the Companies Commission of Malaysia (SSM).

You are receiving this email 30 days in advance of your company's anniversary date.

Here are your company details:
  • Company Name: {company.company_name}
  • SSM Number: {company.registration_number}
  • Incorporation Date: {company.incorporation_date.strftime('%Y-%m-%d')}
  • Anniversary Date: {anniversary.strftime('%Y-%m-%d')}

To ensure timely submission, please be ready to:
  1. Review the draft Annual Return (to be provided by us); and
  2. Arrange payment for our service fees of RM450 (excluding SST, if applicable) before the submission is made.

Completing this early will give you peace of mind knowing your company remains fully compliant with SSM.

Thank you.

Best regards,  
AMR Secretarial Services Sdn. Bhd. and its related companies
            """

            try:
                send_mail(subject, message, None, recipients)
                self.stdout.write(self.style.SUCCESS(f"✅ Email sent to {company.company_name}: {', '.join(recipients)}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed to send for {company.company_name}: {str(e)}"))
