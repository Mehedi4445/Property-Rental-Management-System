from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.urls import reverse


class Property(models.Model):
    class Type(models.TextChoices):
        APARTMENT = "apartment", "Apartment"
        HOUSE = "house", "House"
        ROOM = "room", "Room"
        OFFICE = "office", "Office"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="properties")
    title = models.CharField(max_length=200)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=Type.choices)
    location = models.CharField(max_length=255)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1)])
    bedrooms = models.PositiveSmallIntegerField(default=1)
    bathrooms = models.PositiveSmallIntegerField(default=1)
    image = models.ImageField(upload_to="properties/", blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "properties"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("rentals:property_detail", args=[self.pk])

    @property
    def average_rating(self):
        return self.reviews.aggregate(a=Avg("rating"))["a"]


class RentalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="requests")
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rental_requests")
    message = models.TextField()
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["-request_date"]
        constraints = [
            # DB-level guarantee: one pending request per tenant per property.
            models.UniqueConstraint(
                fields=["property", "tenant"],
                condition=models.Q(status="pending"),
                name="unique_pending_request_per_tenant_property",
            )
        ]

    def __str__(self):
        return f"{self.tenant} -> {self.property} ({self.status})"

    def clean(self):
        if self.property_id and self.tenant_id and self.property.owner_id == self.tenant_id:
            raise ValidationError("You cannot request your own property.")


class Review(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="reviews")
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["property", "tenant"], name="one_review_per_tenant_property")]

    def __str__(self):
        return f"{self.rating}/5 for {self.property} by {self.tenant}"
