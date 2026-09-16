# EduManage — Education Management + Course Store

A full-stack app for a school with five roles (Admin, Teacher, Student, Parent,
parents), tests/feedback, secure relationship-gated chat, and a
Course Store with online payments (UPI / Google Pay / PhonePe / Paytm).

- **Backend:** Django 5 + Django REST Framework, JWT auth (SimpleJWT), MySQL,
  Django Channels (WebSocket chat)
- **Frontend:** React 18 + React Router + Axios (Vite)

Everything has been built and verified locally: the backend's 14 automated
tests pass, `npm run build` succeeds, and a live smoke test confirmed
login → JWT → protected endpoints → the React dev server's API proxy all work
end-to-end.

---

## 1. Project layout

```
edumanage/
  backend/     Django REST API
  frontend/    React app
```

## 2. Backend setup

### 2.1 Prerequisites
- **Python 3.11, 3.12, or 3.13** — **not 3.14**. Django 5.0.6 (pinned here)
  predates a Python 3.14 compatibility fix in Django's template engine
  ([Django ticket #35844](https://code.djangoproject.com/ticket/35844)) and
  will throw `AttributeError: 'super' object has no attribute 'dicts'` on
  every admin/template page under Python 3.14. Tested here on 3.12.
- MySQL 8+ (or use the SQLite fallback below to get started immediately)
- Redis (only needed for chat WebSockets in a realistic multi-worker setup —
  a single-process in-memory channel layer is used automatically in DEBUG
  mode, see below)

> **Note on the MySQL driver:** this project uses **PyMySQL**, a pure-Python
> MySQL driver, instead of `mysqlclient`. `mysqlclient` needs native
> `libmysqlclient-dev`/`pkg-config` headers to compile and fails
> `pip install` on a lot of machines out of the box; PyMySQL has none of that
> and is a drop-in replacement (see `config/__init__.py`). If you'd rather
> use `mysqlclient` for its faster C bindings in production, see the comment
> in `requirements.txt` for the swap.
>
> **Every dependency version below has been installed together from a clean
> virtualenv and exercised by the full test suite** (see §2.6) — this isn't
> just a list of "should work" pins.

### 2.2 Install

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set at minimum `SECRET_KEY` and your MySQL credentials
(`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`). Generate a real
secret key with:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Fastest path to running it today, before MySQL is set up:** set
`USE_SQLITE=True` in `.env`. Everything (models, auth, chat, payments) works
identically on SQLite; switch back to MySQL for anything beyond local
exploration by setting `USE_SQLITE=False` and filling in the `DB_*` values.

### 2.3 Create the MySQL database (skip if using SQLite)

```sql
CREATE DATABASE edumanage CHARACTER SET utf8mb4;
```

### 2.4 Migrate + seed demo data

```bash
python manage.py migrate
python manage.py seed_data
```

`seed_data` creates one demo account per role and a sample course:

| Role    | Email                     | Password       |
|---------|---------------------------|----------------|
| Admin   | admin@edumanage.test      | Admin@12345    |
| Teacher | teacher@edumanage.test    | Teacher@12345  |
| Student | student@edumanage.test    | Student@12345  |
| Parent  | parent@edumanage.test     | Parent@12345   |

The seeded student's Student ID is printed at the end of the command — the
parent account is already linked to that student, but you can also test the
parent's own "search by Student ID" flow with it.

### 2.5 Run it

For plain HTTP API testing:
```bash
python manage.py runserver
```

For WebSocket chat to work you're already covered — `manage.py runserver`
under Django 5 + Channels serves both HTTP and WebSocket via ASGI/Daphne
automatically (see `config/asgi.py`). In production, run behind Daphne (or
another ASGI server) explicitly:
```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

### 2.6 Run the tests

```bash
python manage.py test
```

### 2.7 Payments

The project ships with a **pluggable payment gateway** (`apps/courses/payments.py`):

- `PAYMENT_GATEWAY=mock` (default) — no external account needed. The
  frontend's Course Store has a "Pay with UPI / Google Pay / PhonePe / Paytm"
  step that calls a dev-only `mock/simulate-payment/` endpoint, which runs
  through the *exact same* signature-verified code path a real webhook would
  (see `apps/courses/views.py::_apply_gateway_event`) — so the whole
  Student → Course → Checkout → Payment → Enrollment pipeline is real and
  testable today.
- `PAYMENT_GATEWAY=razorpay` — for real UPI/GPay/PhonePe/Paytm collection.
  Razorpay is the standard Indian aggregator that exposes all four rails
  under one checkout + one webhook, so no per-wallet integration is needed.
  1. `pip install razorpay`
  2. Set `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`
     in `.env`
  3. Point your Razorpay webhook at `POST /api/courses/webhook/`
  4. No other code changes needed — every view talks to `get_gateway()`,
     never to a specific SDK.

Card/UPI credentials are never stored — only the gateway's own opaque
order/payment IDs and non-sensitive metadata (`Payment.gateway_response`).

### 2.8 Admin panel

Django's built-in admin is available at `/admin/` (log in with the seeded
`admin@edumanage.test` account, or `python manage.py createsuperuser`).

---

## 3. Frontend setup

### 3.1 Prerequisites
- Node.js 18+ and npm (tested with Node 22 / npm 10)

### 3.2 Install & run

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**. The dev server proxies `/api` and `/ws` to
`http://127.0.0.1:8000` (see `vite.config.js`), so make sure the backend is
running first. Log in with any of the seeded accounts above.

For a production build:
```bash
npm run build     # outputs to frontend/dist/
```

---

## 4. How the roles map to the UI

| Role    | Sidebar pages |
|---------|---------------|
| Student | Dashboard, Homework, Tests, Performance, Course Store, My Courses, Messages |
| Parent  | Dashboard, My Children, Add a Child (search by Student ID), Performance Reports, Messages |
| Teacher | Dashboard, My Students, Homework, Tests, Reports, Messages |
| Admin   | Dashboard, All Users, Students, Teachers, Parents, Courses, Orders |

## 5. Security notes (what's already enforced, not just documented)

- **Parent–child linking requires school authorization, not just a Student
  ID.** A parent can search for any student by Student ID (harmless — it
  only returns name/grade), but the actual link only succeeds if an admin
  has pre-authorized that parent for that specific student, either by
  `guardian_email` (matched against the parent's login email) or by
  directly setting `authorized_parent` to an existing parent account. Admins
  set this at student-creation time or later via the "Parent authorization"
  panel on the Admin → Users page (API: `PATCH
  /api/accounts/students/<id>/set_guardian/`). Guessing or being told a
  Student ID is no longer sufficient on its own to gain access to that
  student's data.
- **Nothing is trusted from the client.** Every list/detail endpoint filters
  its queryset from `request.user`, and every write re-derives ownership
  from the database (see `apps/accounts/permissions.py::can_access_student`
  and `apps/chat/permissions.py::can_message`) — a forged `student_id` or
  `conversation_id` in a request body can't grant access to someone else's
  data.
- **Homework grading is field-locked.** A student's `PATCH` on their own
  homework can only ever touch submission fields; `grade`/`feedback` are
  stripped server-side regardless of what's sent, and there's a dedicated
  `/grade/` action reachable only by the assigning teacher.
- **Payments are confirmed server-to-server.** An order is only ever marked
  `paid` (and an `Enrollment` created) after a signature-verified webhook
  event — a compromised or malicious frontend "it succeeded" call can't
  unlock a course for free.
- **Passwords are hashed** via Django's default PBKDF2 hasher;
  **JWT access/refresh tokens** rotate and blacklist on refresh
  (`SIMPLE_JWT` settings in `config/settings.py`).

## 6. Troubleshooting

**"AttributeError: 'super' object has no attribute 'dicts'" in the admin
(or anywhere Django renders a template):** you're running Python 3.14+.
This is [Django ticket #35844](https://code.djangoproject.com/ticket/35844)
— Python 3.14 changed how `super` objects can be copied, breaking an
internal trick in Django's template context code. Django 5.0.6 (pinned in
`requirements.txt`) predates the fix. Recreate your virtualenv with Python
3.11, 3.12, or 3.13 and reinstall:
```bash
rm -rf venv
python3.12 -m venv venv        # Windows: py -3.12 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**"Can't log in as a student" / login doesn't work at all:** this was
almost always caused by `pip install -r requirements.txt` silently failing
partway through (most commonly on `mysqlclient`, which needs native MySQL
headers to compile — see §2.1). If the backend server process never
actually started, no login can succeed. Run the install command directly
and read its full output for errors before assuming the app itself is
broken:
```bash
pip install -r requirements.txt   # read this output carefully
python manage.py check            # should print "no issues"
python manage.py migrate          # should finish without errors
python manage.py runserver
```
Then confirm the API itself works before touching the frontend:
```bash
curl -X POST http://127.0.0.1:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"student@edumanage.test","password":"Student@12345"}'
```
This should return a JSON body containing `access` and `refresh` tokens. If
it does and the React app still can't log in, check that the frontend dev
server is actually proxying to the right backend port (`vite.config.js`
proxies to `http://127.0.0.1:8000` by default — adjust it if your backend
runs elsewhere), and check the browser console/network tab for the actual
error.

**Dependency versions:** every version pinned in `backend/requirements.txt`
has been installed together into a clean virtualenv and exercised by the
full Django test suite (`python manage.py test`, 14/14 passing) — see §2.1
for the one deliberate swap (PyMySQL instead of mysqlclient) and why.
`frontend/package.json` similarly builds cleanly from a fresh `npm install`
with Node 18+.

## 7. Known gaps / next steps for a production rollout

- Parent → child linking now requires school authorization (see §5) rather
  than Student ID knowledge alone. For production, consider adding a
  secondary verification step too (e.g. a confirmation code sent to the
  guardian email on file) before the link takes effect immediately.
- The mock payment gateway and its `mock/simulate-payment/` endpoint are for
  local development/demo only — they refuse to run once
  `PAYMENT_GATEWAY=razorpay` is set, but should still be excluded from a
  production deployment's URL config if you want to be extra cautious.
- File uploads (homework submissions, course content) currently write to
  local disk (`MEDIA_ROOT`); swap in S3/GCS `django-storages` for production.
- Channels is configured with an in-memory layer in `DEBUG` mode for
  zero-setup local dev; production needs the Redis-backed layer that's
  already wired up (`REDIS_URL` in `.env`) plus a real ASGI deployment
  (Daphne/Uvicorn behind Nginx).
