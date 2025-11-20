import os
import django
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

def init_database():
    print("=== Initializing Database ===")
    
    # Reset migration state
    print("1. Resetting migration state...")
    os.system('python manage.py migrate --fake')
    
    # Apply all migrations
    print("2. Applying migrations...")
    os.system('python manage.py migrate')
    
    print("3. Database initialization complete!")

if __name__ == "__main__":
    init_database()