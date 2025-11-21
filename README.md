# FoodLink Final

A Flask-based portal for FoodLink Society with role-based dashboards (client, volunteer, admin), QR-based pickups, and address validation via Canada Post.

## Features
- Client registration with photo upload, password policy, and Canada Post address validation (stores original + standardized).
- Unique QR generation for verified clients; volunteers scan to confirm pickups at their assigned site only.
- Admin tools for clients/volunteers/sites, notifications, and no-show tracking.
- MySQL-backed persistence with connection pooling; static QR assets generated server-side.

## Tech Stack
- Python 3.11+, Flask 3, MySQL, Requests, Pillow, qrcode, pyzbar.
- Templates with Bootstrap 5; minimal JS enhancements for address search/validation.

## Setup
1) Clone repo and create a virtualenv.
2) Install deps: `pip install -r requirements.txt`
3) Provision MySQL DB and user. Load schema: `mysql -u <user> -p <db_name> < schema.sql`
4) Configure environment in `.env` (copy/edit as needed):
   - `SECRET_KEY`
   - `DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME`
   - `CANADA_POST_API_KEY` (AddressComplete key) — required for address dropdown/validation
   - `CANADA_POST_API_BASE` (optional override)
   - `ADDRESS_VALIDATION_ALLOW_FALLBACK=false` (keep strict; set true only if you accept non-verified fallback)
5) Run: `python run.py` (uses `app.run(debug=True)` for local dev).

## Address Validation
- `/address/search`: proxies AddressComplete suggestions (min 3 chars).
- `/address/validate`: validates and returns standardized components; registration/profile updates block on failed validation unless fallback is enabled.
- Client form enforces choosing from the dropdown; both original and standardized JSON are persisted in `clients`.

## Navigation & Roles
- Auth redirects to the correct dashboard per role (client/volunteer/admin).
- Navbar shows role-aware links: user dashboards, profile (client), scan/sign-in (volunteer), admin console. My Account menu includes change password and sign out.
- Notifications badge visible when logged in.

## QR + Pickups (overview)
- Verified clients see/download QR (tokenized, no PII) from dashboard.
- Volunteers log in, scan QR, and can only confirm pickups for their assigned site; responses include client photo and eligibility.

## Testing
- Placeholder `tests/` directory; add integration tests for auth, registration, and address endpoints before production.

## Notes
- Ensure HTTPS and secure cookies in production (`SESSION_COOKIE_SECURE=1`).
- Seed an admin user manually after loading schema (see commented insert in `schema.sql`), then login via `/auth/login?role=admin`.
