import os
import django
from datetime import date

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.auth_app.models import Client, Domain

# Create tenant
try:
    # Check if tenant already exists
    if Client.objects.filter(schema_name='kibe').exists():
        print("! Tenant 'kibe' already exists")
        tenant = Client.objects.get(schema_name='kibe')
    else:
        tenant = Client.objects.create(
            schema_name='kibe',
            name='Kibe Organization',
            paid_until=date(2025, 12, 31),
            on_trial=False
        )
        print(f"✓ Tenant created successfully!")
    
    # Check if domain already exists
    if Domain.objects.filter(domain='kibe.localhost').exists():
        print("! Domain 'kibe.localhost' already exists")
        domain = Domain.objects.get(domain='kibe.localhost')
    else:
        domain = Domain.objects.create(
            domain='kibe.localhost',
            tenant=tenant,
            is_primary=True
        )
        print(f"✓ Domain created successfully!")
    
    print(f"\nTenant Details:")
    print(f"  Schema: {tenant.schema_name}")
    print(f"  Name: {tenant.name}")
    print(f"  Domain: {domain.domain}")
    print(f"  Primary: {domain.is_primary}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()