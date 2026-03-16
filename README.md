# IoTDashV0 - Multipurpose IoT Dashboard Platform

> A secure, extensible IoT dashboard inspired by Adafruit IO, with user/admin roles, configurable subscription tiers, and monetization foundations.

## What this project includes
- Secure login/registration with hashed passwords, session auth, and role-based access.
- User dashboard supporting IoT-style widgets (chart/switch/map/gauge/text), Mosquitto MQTT connect/test/pub/sub workflows, sensor enrollment, and actuator commands.
- Admin backend for user management, subscription tier CRUD, pricing/usage limits, and site configuration.
- Learning Zone / Help section and an engaging splash page.
- Stripe-ready subscription checkout hook.
- Works locally on Windows/Linux/macOS/Raspberry Pi and is deployable to Render.

---

## Quick Start (Idiot-proof)

### 1) Clone and enter project
```bash
git clone <your-repo-url>
cd IoTDashV0
```

### 2) Create virtual environment

#### Linux/macOS/RPi
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

#### Windows PowerShell
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

### 3) Run app locally with selectable port

#### Linux/macOS/RPi
```bash
./scripts/run_dev.sh 8000
```

#### Windows PowerShell
```powershell
./scripts/run_dev.ps1 -Port 8000
```

Or run directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4) Open in browser
- `http://localhost:8000`
- Seeded admin login:
  - Email: `admin@iotdash.local`
  - Password: `ChangeMe123!`

> **IMPORTANT SECURITY STEP:** Change admin password immediately in production.

---

## Production deployment (Render example)
1. Push repo to GitHub.
2. Create a **Web Service** in Render.
3. Build command:
   ```bash
   pip install -r requirements.txt
   ```
4. Start command:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. Add environment variables from `.env.example`.
6. For production, set:
   - `DEBUG=false`
   - Strong `SECRET_KEY`
   - Real database URL (PostgreSQL recommended)
   - Stripe keys

### Production-grade server option
You can also run with Gunicorn + Uvicorn workers:
```bash
gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:$PORT --workers 2
```

---

## API examples for IoT devices
Publish a sensor value (recommended Bearer auth header):
```bash
curl -X POST http://localhost:8000/api/sensor/publish \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "topic=sensors/temp" \
  -F "value=24.8"
```

Alternative accepted auth formats:
- `X-API-Key: YOUR_API_KEY` header
- `api_key=YOUR_API_KEY` form field (legacy)

Your current setup template (as requested):
```bash
curl -X POST http://192.168.56.1:8001/api/sensor/publish \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "topic=sensors/temp" \
  -F "value=24.8"
```



## Mosquitto MQTT integration quick flow
1. Login to `/dashboard`.
2. Use **Mosquitto Connection Test** card to connect to your broker (`host`, `port`, optional auth, optional TLS).
3. Use **Publish MQTT Test Message** to verify publish path.
4. Use **Enroll New Sensor** to subscribe to each sensor topic.
5. Watch **Live Sensor Preview** and door/status widgets update as messages arrive.

Example test message from another terminal:
```bash
mosquitto_pub -h 127.0.0.1 -p 1883 -t sensors/door/front -m open
```

---

## Feature roadmap

### User-facing features
- [x] Splash page with clear getting-started CTA
- [x] Secure auth (register/login/logout)
- [x] Dashboard widget creation (door/chart/switch/map/gauge/text)
- [x] API key based sensor publishing
- [x] Actuator command UI
- [x] Learning Zone/FAQ page
- [x] Profile management with profile pic URL
- [x] Manage Subscription view
- [x] Door open/close status widget with on/off payload support
- [ ] Drag-and-drop dashboard layout builder
- [x] Mosquitto MQTT broker integration (connect + status + publish + subscribe)
- [x] Sensor enrollment flow for topic subscription and automatic data persistence
- [ ] File/image upload for profile photos

### Backend and platform improvements
- [x] Admin/user roles and admin-only menu
- [x] Admin CRUD for subscription tiers and site config
- [x] Pricing/usage limits/special offer model
- [x] Stripe checkout integration hook
- [x] Structured project layout for maintainability
- [ ] CSRF protection middleware
- [ ] Rate limiting by tier and per API key
- [ ] Audit logs and admin activity history
- [ ] PostgreSQL migrations (Alembic)

---

## Major feature log (branch order)
1. `main` - Initial platform scaffold with secure auth, dashboard widgets, admin backend, help/splash UI, and Stripe-ready subscription flow.
2. `work` - Added a simple door open/close widget with OPEN/CLOSED state display, flexible sensor payload parsing (open/closed/on/off/1/0), and dedicated tests.
3. `work` - Added end-to-end Mosquitto integration: broker connection test, live status panel, MQTT publish endpoint, topic enrollment/subscription, and automatic chart persistence for subscribed sensor topics.

---

## Debugging support
- Application logs are enabled (DEBUG in dev mode).
- Useful status feedback appears in forms and pages.
- Inspect API behavior via browser devtools or curl commands shown above.

---

## Notes for Raspberry Pi
- Use Python 3.11+ where possible.
- SQLite works for initial deployment; move to PostgreSQL for production load.
- Run service with systemd or Docker for reliability.
