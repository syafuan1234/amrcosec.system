from django.core.management.base import BaseCommand
from companies.models import Company, Director, ContactPerson
from django.utils import timezone
from datetime import timedelta, date
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Send anniversary compliance reminder emails'

    def handle(self, *args, **options):
        # Use real date or simulated one for testing
        today = timezone.now().date()
        # Simulated test date
        today = date(2025, 8, 6)

        companies = Company.objects.all()

        for company in companies:
            incorporation_date = company.incorporation_date
            if not incorporation_date:
                continue

            # Handle leap year edge case
            try:
                anniversary_this_year = incorporation_date.replace(year=today.year)
            except ValueError:
                anniversary_this_year = incorporation_date.replace(year=today.year, day=28)

            first_reminder_date = anniversary_this_year - timedelta(days=30 * 5)
            second_reminder_date = anniversary_this_year
            third_reminder_date = anniversary_this_year + timedelta(days=14)

            print(f"\n🔍 Checking company: {company.company_name}")
            print(f"• Incorporation Date: {incorporation_date}")
            print(f"• Anniversary This Year: {anniversary_this_year}")
            print(f"• First Reminder: {first_reminder_date}")
            print(f"• Second Reminder: {second_reminder_date}")
            print(f"• Third Reminder: {third_reminder_date}")
            print(f"• Today (fake): {today}")

            if today not in [first_reminder_date, second_reminder_date, third_reminder_date]:
                print(f"⏩ Skipped {company.company_name} — not a reminder day")
                continue

            print(f"✅ Reminder triggered for {company.company_name}")

            # Prepare recipients list
            recipients = []

            # Add director emails
            directors = Director.objects.filter(company=company)
            for director in directors:
                if director.email:
                    recipients.append(director.email)

            # Add contact person if they exist and not already included
            if hasattr(company, 'contactperson'):
                contact = company.contactperson
                if contact.email and contact.email not in recipients:
                    recipients.append(contact.email)

            if not recipients:
                self.stdout.write(self.style.WARNING(f"⚠️ No email found for {company.company_name}"))
                continue

            subject = 'Compliance Reminder - Annual Return and Financial Statement'
            message = f"""
Dear Sir/Madam,

This is a friendly reminder to all our valued clients regarding compliance obligations with the Companies Commission of Malaysia (SSM), particularly in relation to the submission of the Annual Return and Financial Statement.

This reminder applies to your company as per the following details:

• Company Name: {company.company_name}
• SSM Number: {company.ssm_number}
• Incorporation Date: {company.incorporation_date}

Please ensure that the necessary documentation is submitted to SSM by the due date to avoid any penalties or compliance issues.

If you have already submitted the relevant documents, kindly disregard this notice.

If you have any questions or require assistance, please do not hesitate to contact us.

Thank you.
            """.strip()

            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipients,
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS(f"✅ Email sent to {company.company_name}: {', '.join(recipients)}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed to send email for {company.company_name}: {str(e)}"))
