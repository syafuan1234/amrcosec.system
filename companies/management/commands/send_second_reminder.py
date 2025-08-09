from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

from companies.models import Company, Director, ContactPerson


class Command(BaseCommand):
    help = 'Send 2nd reminder on the anniversary date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Send reminder regardless of date (for testing purposes)'
        )

    def handle(self, *args, **kwargs):
        today = timezone.localtime(timezone.now()).date()
        test_mode = kwargs['test']

        companies = Company.objects.all()

        for company in companies:
            if not company.incorporation_date:
                self.stdout.write(self.style.WARNING(
                    f"❌ Skipped {company.company_name}: No incorporation date"
                ))
                continue

            # Calculate anniversary and due date
            anniversary = company.incorporation_date.replace(year=today.year)
            if anniversary < today:
                anniversary = anniversary.replace(year=today.year + 1)

            due_date = anniversary + timedelta(days=30)
            reminder_date = anniversary

            # Date check
            if not test_mode:
                if today != reminder_date:
                    self.stdout.write(
                        f"⏭ Skipped {company.company_name}: Today ({today}) is not reminder date ({reminder_date})"
                    )
                    continue
            else:
                self.stdout.write(self.style.WARNING(
                    f"⚠ TEST MODE: Sending for {company.company_name} even though today ({today}) != reminder date ({reminder_date})"
                ))

            # Collect recipients
            recipients = []

            # Directors
            directors = Director.objects.filter(company=company)
            for director in directors:
                if director.email and director.email not in recipients:
                    recipients.append(director.email)

            # Contact person
            try:
                contact = ContactPerson.objects.get(company=company)
                if contact.email and contact.email not in recipients:
                    recipients.append(contact.email)
            except ContactPerson.DoesNotExist:
                pass

            if not recipients:
                self.stdout.write(self.style.WARNING(
                    f"⚠ No email found for {company.company_name}"
                ))
                continue

            # Email content
            subject = f"[SECOND REMINDER] ANNUAL RETURN SUBMISSION DUE FOR {company.company_name}"
            message = f"""
Dear Sir/Madam,

This is a reminder that today is your company’s anniversary date, and your Annual Return must be submitted to the Companies Commission of Malaysia (SSM) within 30 days from today.

Here are your company details:
  • Company Name: {company.company_name}
  • SSM Number: {company.ssm_number}
  • Incorporation Date: {company.incorporation_date.strftime('%d-%m-%Y')}
  • Anniversary Date: {anniversary.strftime('%d-%m-%Y')}
  • Due Date for Annual Return Submission: {due_date.strftime('%d-%m-%Y')}

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
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Email sent to {company.company_name}: {', '.join(recipients)}"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"❌ Failed to send for {company.company_name}: {str(e)}"
                ))
