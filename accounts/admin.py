from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "phone", "is_staff", "date_joined")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email", "phone")
    fieldsets = UserAdmin.fieldsets + (("Rental profile", {"fields": ("role", "phone", "bio", "profile_image")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Rental profile", {"fields": ("email", "role", "phone")}),)
