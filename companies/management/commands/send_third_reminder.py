from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

from companies.models import Company, Director, ContactPerson


class Command(BaseCommand):
    help = 'Send 1st reminder 30 days before anniversary date'

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
            reminder_date = anniversary + timedelta(days=23)

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
            subject = f"[FIRST REMINDER] UPCOMING ANNUAL RETURN SUBMISSION FOR {company.company_name}"
            message = f"""
Dear Sir/Madam,

This is an urgent reminder that your company’s Annual Return must be submitted to the Companies Commission of Malaysia (SSM) within the next 7 days to avoid penalties.

Here are your company details:
  • Company Name: {company.company_name}
  • SSM Number: {company.ssm_number}
  • Incorporation Date: {company.incorporation_date.strftime('%d-%m-%Y')}
  • Anniversary Date: {anniversary.strftime('%d-%m-%Y')}
  • Due Date for Annual Return Submission: {due_date.strftime('%d-%m-%Y')}

Failure to submit on time will result in:
  • Late filing fee of up to RM200.00; and
  • Compound of up to RM50,000.00.

To protect your company from these penalties and maintain good standing with SSM, please review the draft Annual Return and arrange payment immediately so we can proceed with submission without delay.


[Please IGNORE this email if your Annual Return has already been SUBMITTED]

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
