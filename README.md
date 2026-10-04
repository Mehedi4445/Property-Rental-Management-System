# Property Rental & Management System

A Django app where **property owners** list properties and **tenants** search, send rental requests, and leave reviews.

## Features
- Auth: register (choose Owner/Tenant), login, logout, profile update (custom `User` with `role`)
- Owners: property CRUD (own properties only), dashboard with stats, accept/reject requests
- Tenants: browse/search/filter, send requests, dashboard, request details, cancel pending requests
- Search by location, type, min/max rent; pagination (bonus)
- Reviews (1-5) only after an accepted request, one per tenant per property
- Email notification to the owner on new requests (console backend by default) (bonus)
- Custom middleware (`accounts.middleware.RoleAccessMiddleware`) guarding `/owner/` and `/tenant/` URLs
- Organized Django Admin for Users, Properties, Rental Requests, Reviews

## Business rules and where they are enforced
| Rule | Enforcement |
|---|---|
| Only logged-in users can request | `@login_required` on `send_request` |
| Tenant cannot request own property | view check + `RentalRequest.clean()` |
| No duplicate pending requests | view check + DB `UniqueConstraint(condition=status="pending")` |
| Only the owner accepts/rejects | ownership check in `respond_to_request` (403 otherwise) |
| Cannot edit/delete another owner's property | `_own_property_or_403` (403) |
| One review per tenant per property | view check + `UniqueConstraint` |
| Review only after acceptance | check in `add_review` |

## Setup
```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # optional; export the variables or rely on dev defaults
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Open http://127.0.0.1:8000/ for the landing page (admin at `/admin/`). Visitors see the landing page; signed-in users are sent to their dashboard. Set `CURRENCY_SYMBOL` (default `$`) to change the currency shown on rents. Uploaded images go to `media/` (served in DEBUG).

## Tests
```bash
python manage.py test
```

## Production notes
Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, and an SMTP `DJANGO_EMAIL_BACKEND`. Never commit `.env`.
