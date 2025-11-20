# apps/core/dev_middleware.py
from django_tenants.utils import get_tenant_model
from django.db import connection

class ForceKibeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Always force kibe schema for development
        try:
            TenantModel = get_tenant_model()
            kibe_tenant = TenantModel.objects.get(schema_name='kibe')
            connection.set_tenant(kibe_tenant)
            print(f"✓ ForceKibeMiddleware: Set schema to kibe")
        except Exception as e:
            print(f"ForceKibeMiddleware warning: {e}")
        
        response = self.get_response(request)
        return response