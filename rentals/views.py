from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import owner_required, tenant_required

from .forms import PropertyForm, PropertySearchForm, RentalRequestForm, ReviewForm
from .models import Property, RentalRequest, Review

Status = RentalRequest.Status


# ---------- public listing ----------
def property_list(request):
    form = PropertySearchForm(request.GET or None)
    qs = Property.objects.filter(is_available=True).select_related("owner")
    if form.is_valid():
        d = form.cleaned_data
        if d["q"]:
            qs = qs.filter(location__icontains=d["q"])
        if d["property_type"]:
            qs = qs.filter(property_type=d["property_type"])
        if d["min_rent"] is not None:
            qs = qs.filter(monthly_rent__gte=d["min_rent"])
        if d["max_rent"] is not None:
            qs = qs.filter(monthly_rent__lte=d["max_rent"])
    page = Paginator(qs, 6).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "rentals/property_list.html", {"form": form, "page": page, "query": params.urlencode()})


def property_detail(request, pk):
    prop = get_object_or_404(Property.objects.select_related("owner"), pk=pk)
    user = request.user
    can_request = can_review = has_pending = False
    if user.is_authenticated and user.is_tenant and prop.owner_id != user.id:
        has_pending = prop.requests.filter(tenant=user, status=Status.PENDING).exists()
        can_request = prop.is_available and not has_pending
        can_review = (
            prop.requests.filter(tenant=user, status=Status.ACCEPTED).exists()
            and not prop.reviews.filter(tenant=user).exists()
        )
    return render(request, "rentals/property_detail.html", {
        "property": prop,
        "reviews": prop.reviews.select_related("tenant"),
        "can_request": can_request,
        "can_review": can_review,
        "has_pending": has_pending,
    })


# ---------- owner: property CRUD ----------
def _own_property_or_403(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    if prop.owner_id != request.user.id:
        raise PermissionDenied("You can only manage your own properties.")
    return prop


@owner_required
def property_create(request):
    form = PropertyForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        prop = form.save(commit=False)
        prop.owner = request.user
        prop.save()
        messages.success(request, "Property listed.")
        return redirect(prop)
    return render(request, "rentals/property_form.html", {"form": form, "title": "Add property"})


@owner_required
def property_update(request, pk):
    prop = _own_property_or_403(request, pk)
    form = PropertyForm(request.POST or None, request.FILES or None, instance=prop)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Property updated.")
        return redirect(prop)
    return render(request, "rentals/property_form.html", {"form": form, "title": "Edit property"})


@owner_required
def property_delete(request, pk):
    prop = _own_property_or_403(request, pk)
    if request.method == "POST":
        prop.delete()
        messages.success(request, "Property deleted.")
        return redirect("rentals:owner_dashboard")
    return render(request, "rentals/property_confirm_delete.html", {"property": prop})


# ---------- owner dashboard & request handling ----------
@owner_required
def owner_dashboard(request):
    props = request.user.properties.all()
    reqs = RentalRequest.objects.filter(property__owner=request.user).select_related("property", "tenant")
    stats = {
        "total_properties": props.count(),
        "available_properties": props.filter(is_available=True).count(),
        "total_requests": reqs.count(),
        "pending": reqs.filter(status=Status.PENDING).count(),
        "accepted": reqs.filter(status=Status.ACCEPTED).count(),
    }
    return render(request, "rentals/owner_dashboard.html", {"stats": stats, "properties": props, "requests": reqs})


@owner_required
@require_POST
def respond_to_request(request, pk, action):
    rental = get_object_or_404(RentalRequest, pk=pk)
    if rental.property.owner_id != request.user.id:
        raise PermissionDenied
    if action not in ("accept", "reject"):
        raise PermissionDenied
    if rental.status != Status.PENDING:
        messages.error(request, "Only pending requests can be answered.")
    else:
        rental.status = Status.ACCEPTED if action == "accept" else Status.REJECTED
        rental.save(update_fields=["status"])
        messages.success(request, f"Request {rental.get_status_display().lower()}.")
    return redirect("rentals:owner_dashboard")


# ---------- tenant ----------
@login_required
def send_request(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    back = redirect(prop)
    if prop.owner_id == request.user.id:
        messages.error(request, "You cannot request your own property.")
        return back
    if not request.user.is_tenant:
        messages.error(request, "Only tenant accounts can send rental requests.")
        return back
    if not prop.is_available:
        messages.error(request, "This property is not available.")
        return back
    if prop.requests.filter(tenant=request.user, status=Status.PENDING).exists():
        messages.error(request, "You already have a pending request for this property.")
        return back

    form = RentalRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        rental = form.save(commit=False)
        rental.property, rental.tenant = prop, request.user
        rental.full_clean(exclude=["message"])
        rental.save()
        if prop.owner.email:
            send_mail(
                f"New rental request for {prop.title}",
                f"{request.user.username} sent a request:\n\n{rental.message}",
                None, [prop.owner.email], fail_silently=True,
            )
        messages.success(request, "Request sent to the owner.")
        return redirect("rentals:tenant_dashboard")
    return render(request, "rentals/request_form.html", {"form": form, "property": prop})


@tenant_required
def tenant_dashboard(request):
    reqs = request.user.rental_requests.select_related("property")
    reviewed = set(request.user.reviews.values_list("property_id", flat=True))
    stats = {
        "total": reqs.count(),
        "pending": reqs.filter(status=Status.PENDING).count(),
        "accepted": reqs.filter(status=Status.ACCEPTED).count(),
        "rejected": reqs.filter(status=Status.REJECTED).count(),
    }
    return render(request, "rentals/tenant_dashboard.html", {"stats": stats, "requests": reqs, "reviewed": reviewed})


@tenant_required
def request_detail(request, pk):
    rental = get_object_or_404(RentalRequest, pk=pk, tenant=request.user)
    return render(request, "rentals/request_detail.html", {"rental": rental})


@tenant_required
@require_POST
def cancel_request(request, pk):
    rental = get_object_or_404(RentalRequest, pk=pk, tenant=request.user)
    if rental.status != Status.PENDING:
        messages.error(request, "Only pending requests can be cancelled.")
    else:
        rental.status = Status.CANCELLED
        rental.save(update_fields=["status"])
        messages.success(request, "Request cancelled.")
    return redirect("rentals:tenant_dashboard")


# ---------- reviews ----------
@login_required
def add_review(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    user = request.user
    if not prop.requests.filter(tenant=user, status=Status.ACCEPTED).exists():
        messages.error(request, "You can review a property after your request is accepted.")
        return redirect(prop)
    if prop.reviews.filter(tenant=user).exists():
        messages.error(request, "You have already reviewed this property.")
        return redirect(prop)
    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)
        review.property, review.tenant = prop, user
        review.save()
        messages.success(request, "Thanks for your review.")
        return redirect(prop)
    return render(request, "rentals/review_form.html", {"form": form, "property": prop})


# ---------- landing page ----------
def home(request):
    """Landing page for visitors; signed-in users go straight to their dashboard."""
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    from django.contrib.auth import get_user_model
    available = Property.objects.filter(is_available=True)
    return render(request, "rentals/home.html", {
        "form": PropertySearchForm(),
        "featured": available.select_related("owner")[:3],
        "stats": {"homes": available.count(), "owners": get_user_model().objects.filter(role="owner").count()},
    })
