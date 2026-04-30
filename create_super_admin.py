import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.users.models import User

def create_super_admin():
    username = 'superadmincrud'
    password = 'crud123'
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username=username, password=password, role='SUPER_ADMIN')
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f"Super Admin '{username}' created successfully.")
    else:
        print(f"User '{username}' already exists.")

if __name__ == '__main__':
    create_super_admin()
