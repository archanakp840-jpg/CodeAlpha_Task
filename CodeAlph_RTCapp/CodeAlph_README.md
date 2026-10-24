# Connectify

Connectify is a learning and portfolio project for small, browser-based team meetings. It combines Django account and meeting management with Django Channels WebSockets, peer-to-peer WebRTC media, room chat, private file downloads, and a shared canvas.

## Included

- Django registration, login by username/email, logout, protected dashboard and hashed passwords.
- Random 12-character room codes, host/member records, meeting join/leave/end actions.
- Scheduled meetings and a profile page for display name and preferred device IDs.
- Authenticated Channels signaling and room events. WebRTC uses a small-room full mesh and Google STUN.
- Microphone and camera controls, screen capture, chat, shared drawing canvas and PNG download.
- Authorized file upload/download. Allowed extensions are restricted and max size is configurable.
- SQLite models for meetings, participants, files, chat and whiteboard state.

## Setup (Windows PowerShell)

```powershell
cd path\to\connectify
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py makemigrations meetings
python manage.py migrate
python manage.py createsuperuser
daphne -b 127.0.0.1 -p 8000 connectify_project.asgi:application
```

Open http://127.0.0.1:8000. Create an account, start a meeting, then open a second browser profile and join using the room code. Camera/microphone and screen capture are available on localhost (secure context). Run automated backend tests with `python manage.py test`. Daphne serves the ASGI app and Channels WebSockets; Django's WSGI development server does not serve the socket route.

## Configuration

Copy `.env.example` to `.env` and set a long random `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, and `MAX_UPLOAD_MB` for a deployment. Settings load this file automatically; deployment environment variables take precedence. Never commit secrets.

## Architecture and data

Django serves HTML pages and authenticated endpoints. Django Channels handles room WebSockets; the local development channel layer is in-memory and suitable only for a single process. SQLite is used locally. Models include Meeting, MeetingParticipant, SharedFile, ChatMessage and WhiteboardSession; Django's standard User model stores password hashes.

Each participant forms a direct WebRTC connection with every other participant. Bandwidth and CPU use grow quickly with room size; this prototype is for small rooms. Move larger rooms to an SFU such as LiveKit or mediasoup. For multi-process production Channels, configure Redis and an ASGI server/deployment that supports WebSockets. Configure HTTPS and WSS, trusted TURN service credentials, allowed hosts, secure cookies, storage policies and backups. `RTC_ICE_SERVERS` accepts a JSON array of ICE server objects; use TURN credentials from a trusted provider for networks that block direct connectivity. Never commit long-lived TURN credentials.

## Security and limitations

Django authentication, CSRF middleware, permission checks and randomized server filenames are used. Downloads require current meeting membership. Upload file extension and size are checked; browser MIME metadata is not treated as proof of content, so production should add content inspection/scanning. Files and SQLite data are not encrypted at rest by this application. WebRTC uses browser DTLS-SRTP transport encryption; this is not a claim of application-level end-to-end encryption across every shared content type. Configure storage encryption separately if needed. WebSocket chat and bounded whiteboard state are stored in the database. Host controls include ending the room and clearing the board. TURN credentials are not bundled; some networks will require a configured TURN server.

This is a demonstrable development project, not a production-ready conferencing service. Scheduling, profile/device preferences, recording, moderation, robust reconnection, rate limiting, Redis, PostgreSQL and SFU support are future work.

## Tests

The Django test suite covers registration/login/logout, protected dashboard access, joining, private-room denial, host-only end behavior, allowed/prohibited upload types, authorized downloads, scheduling and profile preferences. Browser tests for media permissions, cross-browser WebRTC, screen sharing, mobile layouts and multi-device network conditions require manual testing.

## Screenshots

Add local screenshots here when captured.

## Contributions

Issues and pull requests are welcome. Please describe the environment and reproduction steps for bugs.

