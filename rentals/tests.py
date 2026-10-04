from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Property, RentalRequest, Review


class RentalRulesTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", "o@x.com", "pw12345!", role="owner")
        self.other = User.objects.create_user("other", "x@x.com", "pw12345!", role="owner")
        self.tenant = User.objects.create_user("tenant", "t@x.com", "pw12345!", role="tenant")
        self.prop = Property.objects.create(owner=self.owner, title="Flat", description="d", property_type="apartment",
                                            location="Dhaka", monthly_rent=500)

    def test_other_owner_cannot_edit_or_delete(self):
        self.client.login(username="other", password="pw12345!")
        self.assertEqual(self.client.get(reverse("rentals:property_update", args=[self.prop.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("rentals:property_delete", args=[self.prop.pk])).status_code, 403)
        self.assertTrue(Property.objects.filter(pk=self.prop.pk).exists())

    def test_tenant_blocked_from_owner_area_by_middleware(self):
        self.client.login(username="tenant", password="pw12345!")
        r = self.client.get(reverse("rentals:property_create"))
        self.assertRedirects(r, reverse("rentals:property_list"))

    def test_no_duplicate_pending_and_owner_cannot_request(self):
        self.client.login(username="tenant", password="pw12345!")
        url = reverse("rentals:send_request", args=[self.prop.pk])
        self.client.post(url, {"message": "I would love to rent this."})
        self.client.post(url, {"message": "Sending again please."})
        self.assertEqual(RentalRequest.objects.count(), 1)
        self.client.login(username="owner", password="pw12345!")
        self.client.post(url, {"message": "My own property!!"})
        self.assertEqual(RentalRequest.objects.count(), 1)

    def test_only_owner_accepts_and_review_flow(self):
        req = RentalRequest.objects.create(property=self.prop, tenant=self.tenant, message="hello there")
        accept = reverse("rentals:respond_to_request", args=[req.pk, "accept"])
        self.client.login(username="other", password="pw12345!")
        self.assertEqual(self.client.post(accept).status_code, 403)
        review_url = reverse("rentals:add_review", args=[self.prop.pk])
        self.client.login(username="tenant", password="pw12345!")
        self.client.post(review_url, {"rating": 5, "comment": "nice"})
        self.assertEqual(Review.objects.count(), 0)  # not accepted yet
        self.client.login(username="owner", password="pw12345!")
        self.client.post(accept)
        req.refresh_from_db()
        self.assertEqual(req.status, "accepted")
        self.client.login(username="tenant", password="pw12345!")
        self.client.post(review_url, {"rating": 5, "comment": "nice"})
        self.client.post(review_url, {"rating": 1, "comment": "again"})
        self.assertEqual(Review.objects.count(), 1)

    def test_tenant_can_cancel_pending(self):
        req = RentalRequest.objects.create(property=self.prop, tenant=self.tenant, message="hello there")
        self.client.login(username="tenant", password="pw12345!")
        self.client.post(reverse("rentals:cancel_request", args=[req.pk]))
        req.refresh_from_db()
        self.assertEqual(req.status, "cancelled")

    def test_search_filters(self):
        r = self.client.get(reverse("rentals:property_list"), {"q": "dha", "property_type": "apartment", "min_rent": 100, "max_rent": 600})
        self.assertContains(r, "Flat")
        r = self.client.get(reverse("rentals:property_list"), {"max_rent": 100})
        self.assertNotContains(r, "Flat")


class PageSmokeTests(TestCase):
    """Every page should render for the right user."""

    def setUp(self):
        self.owner = User.objects.create_user("owner", "o@x.com", "pw12345!", role="owner")
        self.tenant = User.objects.create_user("tenant", "t@x.com", "pw12345!", role="tenant")
        self.prop = Property.objects.create(owner=self.owner, title="Flat", description="d", property_type="apartment",
                                            location="Dhaka", monthly_rent=500)
        self.req = RentalRequest.objects.create(property=self.prop, tenant=self.tenant, message="hello there",
                                                status="accepted")

    def test_home_is_landing_for_visitors(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Find a place that fits your month")

    def test_home_redirects_signed_in_users_to_dashboard(self):
        self.client.login(username="owner", password="pw12345!")
        self.assertRedirects(self.client.get("/"), reverse("accounts:dashboard"), fetch_redirect_response=False)

    def test_public_and_auth_pages(self):
        for name, args in [("rentals:property_list", []), ("rentals:property_detail", [self.prop.pk]),
                           ("accounts:login", []), ("accounts:register", [])]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, name)

    def test_owner_pages(self):
        self.client.login(username="owner", password="pw12345!")
        for name, args in [("rentals:owner_dashboard", []), ("rentals:property_create", []),
                           ("rentals:property_update", [self.prop.pk]), ("rentals:property_delete", [self.prop.pk]),
                           ("accounts:profile", []), ("rentals:property_detail", [self.prop.pk])]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, name)

    def test_tenant_pages(self):
        self.client.login(username="tenant", password="pw12345!")
        for name, args in [("rentals:tenant_dashboard", []), ("rentals:request_detail", [self.req.pk]),
                           ("rentals:add_review", [self.prop.pk]), ("rentals:property_detail", [self.prop.pk]),
                           ("accounts:profile", [])]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, name)

    def test_register_creates_user_and_logs_in(self):
        r = self.client.post(reverse("accounts:register"), {
            "username": "newbie", "email": "n@x.com", "role": "owner", "phone": "",
            "password1": "Str0ng-pass-99", "password2": "Str0ng-pass-99"})
        self.assertRedirects(r, reverse("accounts:dashboard"), fetch_redirect_response=False)
        self.assertEqual(User.objects.get(username="newbie").role, "owner")
