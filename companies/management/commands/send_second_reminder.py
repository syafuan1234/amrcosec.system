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

            reminder_date = anniversary
            due_date = anniversary + timedelta(days=30)

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
            subject = f"[SECOND REMINDER] ANNUAL RETURN SUBMISSION DUE FOR {company.company_name}"
            message = f"""
Dear Sir/Madam,

This is a reminder that today is your company’s anniversary date, and your Annual Return must be submitted to the Companies Commission of Malaysia (SSM) within 30 days from today.

Here are your company details:
  • Company Name: {company.company_name}
  • SSM Number: {company.ssm_number}
  • Incorporation Date: {company.incorporation_date.strftime('%Y-%m-%d')}
  • Anniversary Date: {anniversary.strftime('%Y-%m-%d')}
  • Due Date for Annual Return Submission: {due_date.strftime('%Y-%m-%d')}

Under Section 68 of the Companies Act 2016, failure to submit within the stipulated period may result in:
  • Late filing fee of up to RM200.00; and
  • Compound of up to RM50,000.00.

Completing this early will help ensure your company stays in good standing with SSM and avoids unnecessary penalties. 
If you have not yet done so, please review the draft Annual Return and arrange payment so we can proceed with the submission.

Thank you.

Best regards,  
AMR Secretarial Services Sdn. Bhd. and its related companies
            """

            try:
                send_mail(subject, message, None, recipients)
                self.stdout.write(self.style.SUCCESS(f"✅ Email sent to {company.company_name}: {', '.join(recipients)}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed to send for {company.company_name}: {str(e)}"))
