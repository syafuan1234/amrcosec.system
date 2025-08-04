import django
import os
from django.core.management import call_command

def load():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secretary.settings')
    django.setup()

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if not User.objects.exists():  # Only load if no users exist
            call_command('loaddata', 'initial_superuser.json')
            print("✅ Superuser loaded successfully.")
        else:
            print("ℹ️ Superuser already exists. Skipping.")
    except Exception as e:
        print(f"❌ Error loading superuser: {e}")
