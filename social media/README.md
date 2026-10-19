# iworld

iworld is an original social network built with Django, Django templates, vanilla JavaScript, and SQLite for local development. The original Express application remains in this folder as server.js and can still be started separately with npm.

## Django setup (recommended)

Requires Python 3.10 or newer. From PowerShell:

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

Open http://127.0.0.1:8000. Create accounts at /register/, sign in at /login/, and manage the database at /admin/. If PowerShell blocks activation, run Set-ExecutionPolicy -Scope Process Bypass in that terminal first.

Password reset uses Django’s console email backend in development: request a reset link and copy it from the terminal running runserver. Configure a real email backend before deployment.

## Working features

- Django registration with unique usernames, email and phone number; login by username, email, or phone; logout; password reset by email.
- Editable profiles with profile pictures, bios, phone numbers, and private-account settings.
- Image, video, and text posts with captions, visibility choices, file validation, and upload previews.
- Following, private follow requests with confirm/decline, follower/following lists, and contact matching from an uploaded vCard (.vcf).
- Follow-based feed, public explore, search, likes, comments, post editing/deletion, notifications, and Django Admin.
- CSRF-protected forms, ownership checks, server-side privacy enforcement, responsive layout, and dark iworld styling.

Uploads are stored under media/; post media is served through an authenticated view that checks visibility. SQLite is the default. To use PostgreSQL, set DB_ENGINE=postgresql and PGDATABASE, PGUSER, PGPASSWORD, PGHOST, and PGPORT environment variables.

The Express version is independent: use npm install and npm start to launch it on port 3000. Use python manage.py runserver for the Django version on port 8000.
