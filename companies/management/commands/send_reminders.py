from django.core.management.base import BaseCommand
from companies.models import Company
from django.utils import timezone
from datetime import timedelta, date
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Send anniversary compliance reminder emails'

    def handle(self, *args, **options):
        today = timezone.now().date()
        # FOR TESTING — you can simulate any date like this:
        today = date(2025, 8, 6)

        companies = Company.objects.all()

        for company in companies:
            incorporation_date = company.incorporation_date
            if not incorporation_date:
                continue

            # Create anniversary date for this year
            try:
                anniversary_this_year = incorporation_date.replace(year=today.year)
            except ValueError:
                anniversary_this_year = incorporation_date.replace(year=today.year, day=28)

            # Calculate the 3 reminder trigger dates
            first_reminder_date = anniversary_this_year - timedelta(days=30 * 5)  # approx 5 months before
            second_reminder_date = anniversary_this_year
            third_reminder_date = anniversary_this_year + timedelta(days=14)

            # Only send if today matches any of the 3 dates
            if today in [first_reminder_date, second_reminder_date, third_reminder_date]:
                recipients = list(company.director_set.exclude(email='').values_list('email', flat=True))

                # If contact person exists and has email
                if hasattr(company, 'contactperson') and company.contactperson.email:
                    recipients.append(company.contactperson.email)

                if recipients:
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
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️ No email found for {company.company_name}"))
            else:
                self.stdout.write(f"⏩ Skipped {company.company_name} — not a reminder day")
