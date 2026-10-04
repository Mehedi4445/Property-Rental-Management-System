from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "owner", "Property Owner"
        TENANT = "tenant", "Tenant"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.TENANT)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_tenant(self):
        return self.role == self.Role.TENANT
