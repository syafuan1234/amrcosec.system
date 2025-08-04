from django.core.management.base import BaseCommand
from companies.models import Company
from django.core.mail import send_mail
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Check for companies with upcoming anniversaries'

    def handle(self, *args, **kwargs):
        today = date.today()
        upcoming = today + timedelta(days=7)

        companies_today = Company.objects.filter(
            incorporation_date__day=today.day,
            incorporation_date__month=today.month
        )

        companies_soon = Company.objects.filter(
            incorporation_date__day=upcoming.day,
            incorporation_date__month=upcoming.month
        )

        messages = []

        for c in companies_today:
            messages.append(f"🎯 TODAY: {c.company_name} (SSM: {c.ssm_number}) - Anniversary today!")

        for c in companies_soon:
            messages.append(f"🕒 UPCOMING: {c.company_name} (SSM: {c.ssm_number}) - Anniversary in 7 days!")

        if messages:
            send_mail(
                subject='[Reminder] Company Anniversary Alerts',
                message='\n'.join(messages),
                from_email='your_email@example.com',
                recipient_list=['yourteam@example.com'],  # Can be multiple emails
            )
            self.stdout.write(self.style.SUCCESS("Email sent with upcoming anniversaries."))
        else:
            self.stdout.write("No companies with upcoming anniversaries.")
