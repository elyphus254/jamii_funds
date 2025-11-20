from django.http import HttpResponseForbidden
from datetime import date, datetime
from django_tenants.middleware import TenantMiddleware
from django_tenants.utils import get_tenant_model
from django.db import connection

class HeaderTenantMiddleware:
    """
    Custom middleware that reads tenant from X-Tenant header
    Runs AFTER TenantMainMiddleware
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # TenantMainMiddleware has already set the schema
        # Now we check if we should override it with header
        
        # Get tenant model
        model = get_tenant_model()
        
        # Try to get tenant from header
        tenant_header = request.META.get('HTTP_X_TENANT') or request.META.get('TENANT')
        
        if tenant_header:
            try:
                tenant = model.objects.get(schema_name=tenant_header)
                request.tenant = tenant
                connection.set_tenant(tenant)
                print(f"✓ HeaderTenantMiddleware: Override schema to {tenant.schema_name}")
            except model.DoesNotExist:
                print(f"HeaderTenantMiddleware: Tenant '{tenant_header}' not found")
        
        response = self.get_response(request)
        return response

class TrialMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Debug current tenant
        if hasattr(request, 'tenant'):
            print(f"TrialMiddleware - Current tenant: {getattr(request.tenant, 'schema_name', 'None')}")
        else:
            print("TrialMiddleware - No tenant set")
            
        TenantModel = get_tenant_model()
        
        if hasattr(request, 'tenant') and isinstance(request.tenant, TenantModel):
            tenant = request.tenant
            if hasattr(tenant, 'on_trial') and tenant.on_trial:
                if hasattr(tenant, 'created_on') and tenant.created_on:
                    created_date = tenant.created_on
                    if isinstance(created_date, datetime):
                        created_date = created_date.date()
                    
                    trial_days = (date.today() - created_date).days
                    if trial_days > 14:
                        return HttpResponseForbidden("Your 14-day trial has expired. Please subscribe.")
        return self.get_response(request)