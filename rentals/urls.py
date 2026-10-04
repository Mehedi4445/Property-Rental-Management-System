from django.urls import path

from . import views

app_name = "rentals"
urlpatterns = [
    path("", views.home, name="home"),
    path("properties/", views.property_list, name="property_list"),
    path("properties/<int:pk>/", views.property_detail, name="property_detail"),
    path("properties/<int:pk>/request/", views.send_request, name="send_request"),
    path("properties/<int:pk>/review/", views.add_review, name="add_review"),
    # owner area (guarded by RoleAccessMiddleware + decorators)
    path("owner/dashboard/", views.owner_dashboard, name="owner_dashboard"),
    path("owner/properties/add/", views.property_create, name="property_create"),
    path("owner/properties/<int:pk>/edit/", views.property_update, name="property_update"),
    path("owner/properties/<int:pk>/delete/", views.property_delete, name="property_delete"),
    path("owner/requests/<int:pk>/<str:action>/", views.respond_to_request, name="respond_to_request"),
    # tenant area
    path("tenant/dashboard/", views.tenant_dashboard, name="tenant_dashboard"),
    path("tenant/requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("tenant/requests/<int:pk>/cancel/", views.cancel_request, name="cancel_request"),
]
