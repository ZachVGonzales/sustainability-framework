# Setup Requirements

This document describes all the steps required to run the Sustainability Framework
end-to-end, including the Python API backend, Keycloak authentication server, the
database, and the Chrome extension.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Repository Setup](#2-repository-setup)
3. [Environment Variables (.env)](#3-environment-variables-env)
4. [Database Setup](#4-database-setup)
5. [Keycloak Setup (Docker)](#5-keycloak-setup-docker)
6. [Running the API](#6-running-the-api)
7. [Chrome Extension – Load & Configure](#7-chrome-extension--load--configure)
8. [End-to-End Flow](#8-end-to-end-flow)
9. [Production Notes](#9-production-notes)

---

## 1. Prerequisites

| Tool | Minimum Version | Notes |
|------|-----------------|-------|
| Python | 3.14 | Managed via the repo's `.venv` |
| pip / uv | latest | `pip install --upgrade pip` |
| Docker | 24+ | Required for Keycloak |
| Docker Compose | v2 | Bundled with Docker Desktop |
| Chromium / Chrome | 120+ | For the extension |

---

## 2. Repository Setup

```bash
# Clone the repo (if not already done)
git clone <repo-url>
cd sustainability-framework

# Create & activate virtual environment
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\activate.bat    # Windows

# Install all dependencies
pip install -e .
```

---

## 3. Environment Variables (.env)

Copy the template and fill in your values:

```bash
cp apps/my-web-app/.env apps/my-web-app/.env.local
```

Edit `apps/my-web-app/.env` (or `.env.local` if you prefer):

```ini
# SQLite (default for local dev – no extra setup required)
DB_URL=sqlite:///./sustainability.db

# PostgreSQL (for production – see section 4b)
# DB_URL=postgresql+psycopg2://postgres:password@localhost:5432/sustainability

KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=sustainability
KEYCLOAK_CLIENT_ID=sustainability-extension

# Optional: override path to the trained ML model
# Defaults to apps/ml-training/models/model.joblib (relative to repo root)
# MODEL_PATH=/absolute/path/to/model.joblib
```

> **Never commit the real `.env` file with secrets to source control.**

---

## 4. Database Setup

### 4a. SQLite (default – no extra setup)

The database file (`sustainability.db`) is created automatically in
`apps/my-web-app/` when the API starts for the first time.  All tables are
created via SQLAlchemy's `Base.metadata.create_all()`.

### 4b. PostgreSQL (production)

1. Create a database:
   ```bash
   psql -U postgres -c "CREATE DATABASE sustainability;"
   ```
2. Update `DB_URL` in `.env`:
   ```ini
   DB_URL=postgresql+psycopg2://postgres:password@localhost:5432/sustainability
   ```
3. The API creates all tables on startup.

---

## 5. Keycloak Setup (Docker)

Keycloak provides OpenID Connect (OIDC) authentication for the Chrome extension.

### 5a. Start Keycloak via Docker Compose

Create `docker-compose.yml` at the repo root (or inside `apps/my-web-app/`):

```yaml
version: "3.9"
services:
  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    hostname: keycloak
    command: start-dev
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
    ports:
      - "8080:8080"
    volumes:
      - keycloak_data:/opt/keycloak/data

volumes:
  keycloak_data:
```

Start it:

```bash
docker compose up -d keycloak
```

Keycloak is now available at **http://localhost:8080**.

### 5b. Configure the Realm

1. Open the [Keycloak Admin Console](http://localhost:8080) and log in with
   `admin` / `admin`.
2. Create a new **Realm** named **`sustainability`**:
   - Hover over the realm dropdown (top-left) → **Create Realm**
   - Name: `sustainability` → **Create**

### 5c. Create the Client

Inside the `sustainability` realm:

1. Go to **Clients** → **Create client**
2. Fill in:
   - **Client type**: `OpenID Connect`
   - **Client ID**: `sustainability-extension`
3. Click **Next**
4. Enable **Standard flow** (Authorization Code Flow) – leave others OFF
5. Click **Next**
6. Set **Valid redirect URIs**:
   - `https://<your-extension-id>.chromiumapp.org/*`
   
   > **Getting the extension ID**: Load the unpacked extension in Chrome
   > (see [section 7](#7-chrome-extension--load--configure)), then copy the
   > ID shown on `chrome://extensions/`.
   >
   > You can also add `https://*.chromiumapp.org/*` as a wildcard during
   > development.
7. Set **Web origins**: `+` (same as redirect URIs)
8. Under **Capability config**, make sure **Client authentication** is **OFF**
   (public client, required for PKCE from an extension).
9. Click **Save**

### 5d. Enable PKCE on the Client

1. Open the client → **Advanced** tab
2. Set **Proof Key for Code Exchange Code Challenge Method** to `S256`
3. **Save**

### 5e. Create a Test User

1. Go to **Users** → **Add user**
2. Fill in username/email → **Create**
3. Go to the **Credentials** tab → **Set password** (uncheck Temporary)

### 5f. Verify Realm Public Key (used by the API)

The API fetches the realm's public key automatically from:

```
http://localhost:8080/realms/sustainability
```

No manual key configuration is needed.

---

## 6. Running the API

The API lives in `apps/my-web-app/api/`.  Start it with Uvicorn:

```bash
cd apps/my-web-app
source ../../.venv/bin/activate
uvicorn api.main:app --host 127.0.0.1 --port 8787 --reload
```

Verify it's running:

```bash
curl http://127.0.0.1:8787/health
# → {"ok": true}
```

Interactive API docs are available at:
- **Swagger UI**: http://127.0.0.1:8787/docs
- **ReDoc**: http://127.0.0.1:8787/redoc

### API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET`  | `/health` | No | Liveness probe |
| `GET`  | `/estimate_tokens?text=…` | No | Token count estimation |
| `POST` | `/messages` | Bearer JWT | Record a ChatGPT message exchange |
| `GET`  | `/conversations/messages?url=…` | Bearer JWT | Fetch messages for a conversation URL |

---

## 7. Chrome Extension – Load & Configure

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle, top-right)
3. Click **Load unpacked** → select
   `apps/my-web-app/extension/`
4. Note the **Extension ID** shown on the card (e.g. `abcdefghijklmnopqrstuvwxyz123456`)
5. Return to Keycloak and update the **Valid redirect URIs** to:
   ```
   https://<your-extension-id>.chromiumapp.org/*
   ```
6. The extension icon should now appear in the toolbar.

### First Use

1. Click the extension icon → the **Login with Keycloak** panel appears.
2. Click **Login with Keycloak** → a Keycloak login window opens.
3. Enter your credentials → the popup switches to the dashboard view.
4. Navigate to a ChatGPT conversation on https://chatgpt.com.
5. Send a message – the extension intercepts the exchange and records it.
6. Open the popup while on that ChatGPT URL → click **Refresh** to load the
   recorded messages as datapoints on the chart.

---

## 8. End-to-End Flow

```
User (ChatGPT tab)
  │  types & sends message
  ▼
content.js
  │  detects streaming start/end
  │  captures input text + output text + word-count token estimate
  │  sendMessage(RECORD_MESSAGE, payload)
  ▼
background.js
  │  attaches Bearer JWT (from chrome.storage.local)
  │  POST /messages
  ▼
FastAPI API (port 8787)
  │  validates Keycloak JWT
  │  upserts User from JWT "sub" claim
  │  upserts Conversation for conversation URL
  │  inserts Message row (input/output text, tokens, energy estimate)
  ▼
SQLite / PostgreSQL (sustainability.db)

User opens popup
  │  popup.js → AUTH_STATE check
  │  background.js → verifies/refreshes token
  │  popup.js → FETCH_CONVERSATION with current tab URL
  │  background.js → GET /conversations/messages?url=…
  │  popup.js → renders messages as line chart (total tokens per message)
```

---

## 9. Production Notes

- **HTTPS**: Run the API behind a reverse proxy (nginx / Caddy) with a TLS
  certificate.  Update `API_BASE` in `background.js` and `host_permissions` in
  `manifest.json` accordingly.
- **Database**: Use PostgreSQL in production.  Apply Alembic migrations rather
  than relying on `create_all()`.
- **Keycloak**: Use the production-mode Keycloak image (`start` command) with a
  proper database backend (PostgreSQL recommended).
- **CORS**: Tighten the `allow_origins` list in `api/main.py` to your actual
  domain(s).
- **ML Model**: Energy is predicted by the trained model at
  `apps/ml-training/models/model.joblib`.  Set `MODEL_PATH` in `.env` to use a
  different model file.
