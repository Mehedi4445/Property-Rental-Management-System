from django.contrib import admin

from .models import Property, RentalRequest, Review


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "property_type", "location", "monthly_rent", "is_available", "created_at")
    list_filter = ("property_type", "is_available", "created_at")
    list_editable = ("is_available",)
    search_fields = ("title", "location", "owner__username")
    autocomplete_fields = ("owner",)
    date_hierarchy = "created_at"
    inlines = [ReviewInline]


@admin.register(RentalRequest)
class RentalRequestAdmin(admin.ModelAdmin):
    list_display = ("property", "tenant", "status", "request_date")
    list_filter = ("status", "request_date")
    search_fields = ("property__title", "tenant__username")
    list_select_related = ("property", "tenant")
    actions = ["mark_accepted", "mark_rejected"]

    @admin.action(description="Mark selected as accepted")
    def mark_accepted(self, request, qs):
        qs.filter(status="pending").update(status="accepted")

    @admin.action(description="Mark selected as rejected")
    def mark_rejected(self, request, qs):
        qs.filter(status="pending").update(status="rejected")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("property", "tenant", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("property__title", "tenant__username", "comment")
