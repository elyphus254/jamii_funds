# apps/core/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django_tenants.utils import schema_context
from .models import Client, Domain
from django.db import connection
import re
from datetime import date

def signup(request):
    if request.method == "POST":
        name = request.POST['name'].strip()
        subdomain = request.POST['subdomain'].lower().strip()
        email = request.POST['email'].strip()
        phone = request.POST['phone'].strip()
        password = request.POST['password']

        # Validation
        if not re.match(r'^[a-z0-9-]+$', subdomain):
            messages.error(request, "Subdomain can only contain letters, numbers, and hyphens")
            return render(request, 'core/signup.html')

        if Client.objects.filter(subdomain=subdomain).exists():
            messages.error(request, "This subdomain is already taken!")
            return render(request, 'core/signup.html')

        # 1. Create the tenant
        tenant = Client(
            schema_name=subdomain.replace('-', '_'),
            name=name,
            subdomain=subdomain,
            on_trial=True,
            paid_until=date.today()
        )
        tenant.save()

        # 2. Create domain (for local dev)
        domain_name = f"{subdomain}.127.0.0.1:8000"
        Domain.objects.create(domain=domain_name, tenant=tenant, is_primary=True)

        # 3. Create schema
        tenant.create_schema()

        # 4. Create superuser inside the new tenant
        with schema_context(tenant.schema_name):
            User.objects.create_superuser(
                username=email.split('@')[0],
                email=email,
                password=password
            )

        messages.success(request, f"Success! Your chama is ready at http://{subdomain}.127.0.0.1:8000")
        return redirect('signup')

    return render(request, 'core/signup.html')