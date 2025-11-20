from django_tenants.models import TenantMixin, DomainMixin
from django.db import models
from django.utils.text import slugify


class Client(TenantMixin):               # ← THIS LINE IS THE KEY: inherit from TenantMixin
    name = models.CharField(max_length=100)
    paid_until = models.DateField()
    on_trial = models.BooleanField(default=False)
    created_on = models.DateField(auto_now_add=True)

    class Meta:
        app_label = 'core'

    


    # Optional but recommended: auto-generate schema_name
    def save(self, *args, **kwargs):
        if not self.schema_name:
            self.schema_name = slugify(self.name).replace('-', '_')[:50] or 'default'
            # Ensure uniqueness
            base = self.schema_name
            i = 1
            while Client.objects.filter(schema_name=self.schema_name).exists():
                self.schema_name = f"{base}_{i}"
                i += 1
        super().save(*args, **kwargs)


class Domain(DomainMixin):
    pass