# Sustainability Framework – Requirements

## Tech Stack Summary

| Layer | Technology |
|---|---|
| Browser Extension | Chrome Extension (Manifest V3), JavaScript |
| Content Script | `content.js` – DOM observation on chatgpt.com, token UI, prompt/response capture |
| Service Worker | `background.js` – Keycloak OIDC (Auth Code + PKCE), token refresh, API relay |
| Popup UI | `popup.html / popup.js / popup.css` – Canvas chart, auth panel |
| Backend API | FastAPI (Python), SQLAlchemy ORM |
| Database | SQLite (default, configurable via `DB_URL`) |
| Authentication | Keycloak 24 (OIDC, RS256 JWT), containerized via Docker Compose |
| ML Model | scikit-learn `RandomForestRegressor` (multi-output: output tokens + GPU energy in Joules) |

---

## Marketing Requirements

| ID | Requirement |
|---|---|
| MR-1 | The system shall provide users with a real-time energy estimation for prompts sent to AI models. |
| MR-2 | The system shall keep track of conversation histories and store per-message metrics (token counts, energy consumption). |
| MR-3 | The frontend shall be user-friendly and self-explanatory; the user should not question the functionality of the extension. |
| MR-4 | The extension shall automatically refresh and update based on the current status of the active page. |
| MR-5 | The system shall require user authentication to protect individual conversation data and ensure each user only sees their own usage. |
| MR-6 | The system shall support reproducible, containerized deployment so the backend can be started with minimal configuration effort. |

---

## Engineering Requirements

| ID | Description | Verification Method | Traceable To |
|---|---|---|---|
| ER-01 | The content script shall display a live token count estimate adjacent to the ChatGPT message composer, updating on every `input` and `keyup` event before the user submits a prompt. | Manual UI test: type text in the ChatGPT composer and verify the token estimate label updates in real time. | MR-1 |
| ER-02 | The `GET /estimate_tokens` endpoint shall accept a `text` query parameter and return a token count using a whitespace-based estimator within 200 ms. | API integration test: send a known text string and assert the returned `tokens` value matches the expected word count. | MR-1 |
| ER-03 | The ML pipeline (RandomForestRegressor with TF-IDF + numeric preprocessing) shall predict GPU energy consumption in Joules for a given (input_text, input_tokens) pair with an R² score ≥ 0.80 on the held-out test set. | Model evaluation script: run `train_model.py` and assert R² ≥ 0.80 on the test split. | MR-1 |
| ER-04 | The `POST /messages` endpoint shall invoke the ML energy predictor and persist the estimated energy (Joules) alongside each recorded message when no energy value is supplied by the client. | Integration test: POST a message without an `energy` field and assert the response body contains a non-null `energy` value that is stored in the database. | MR-1, MR-2 |
| ER-05 | The database shall maintain three tables – `users`, `conversations` (keyed by ChatGPT conversation URL and user), and `messages` (input text, output text, input tokens, output tokens, energy, created_at timestamp) – created automatically on API startup. | Schema inspection test: start the API and assert all three tables exist with the correct columns using SQLAlchemy introspection. | MR-2 |
| ER-06 | The `GET /conversations/messages` endpoint shall return all stored messages for the authenticated user matching the provided conversation URL, in ascending `created_at` order. | API integration test: insert known messages into the DB and assert the endpoint returns them in chronological order for the correct user only. | MR-2 |
| ER-07 | The content script shall detect ChatGPT assistant response completion (absence of the streaming stop-button) using a MutationObserver, capture the final input and output text along with estimated token counts, and forward the exchange to the background service worker via `chrome.runtime.sendMessage`. | End-to-end test: simulate a ChatGPT conversation in a controlled test page and assert that a `RECORD_MESSAGE` message is received by the background worker with correct fields. | MR-2 |
| ER-08 | The popup shall display a status badge that transitions between `LOADING`, `LOADED`, and `SELECTED` states to reflect the current data-fetch lifecycle. | Manual UI test: open the popup during and after a data fetch and verify the badge text and color change correctly for each state. | MR-3 |
| ER-09 | The popup shall display the authenticated user's name after a successful login and show login/logout buttons appropriate to the current authentication state. | Manual UI test: log in and verify the user name appears; log out and verify the login button reappears. | MR-3, MR-5 |
| ER-10 | The popup shall render per-message energy data as a Canvas line chart with labeled aggregate statistics (message count, total input tokens, total output tokens, total energy in Joules) derived from the `GET /conversations/messages` response. | Manual UI test: navigate to a ChatGPT conversation with recorded messages, open the popup, and assert the chart renders data points and the aggregates match the stored values. | MR-3, MR-1 |
| ER-11 | The content script shall detect ChatGPT SPA URL changes via polling (`location.href` comparison) and reset all per-conversation state (pending input, recorded turn count) when navigating to a new conversation. | Manual test: navigate between two ChatGPT conversations and verify no messages from the previous conversation are attributed to the new one. | MR-4 |
| ER-12 | The popup shall provide a manual refresh button that re-fetches conversation messages from the API and re-renders the chart without requiring the user to close and reopen the popup. | Manual UI test: send a new ChatGPT message, click the refresh button, and verify the new data point appears in the chart. | MR-4 |
| ER-13 | The background service worker shall implement Keycloak OIDC Authorization Code + PKCE login using `chrome.identity.launchWebAuthFlow`, store the resulting access and refresh tokens in `chrome.storage.local`, and expose the authentication state to the popup via `chrome.runtime.onMessage`. | Manual auth test: click login, complete the Keycloak flow, and assert that `access_token` is present in `chrome.storage.local` after redirect. | MR-5 |
| ER-14 | The background service worker shall automatically refresh an expired access token using the stored refresh token before forwarding any API request, without requiring user interaction. | Timed test: manually expire the `expires_at` value in local storage and trigger a `RECORD_MESSAGE` event; assert the API call succeeds and a new `access_token` is stored. | MR-5 |
| ER-15 | All authenticated API endpoints (`POST /messages`, `GET /conversations/messages`) shall validate the `Authorization: Bearer <token>` header against Keycloak's RS256 public key and return HTTP 401 for missing or invalid tokens. | Security test: call each authenticated endpoint without a token (expect 401) and with an invalid token (expect 401); call with a valid token (expect 200). | MR-5 |
| ER-16 | The Keycloak identity provider shall be deployable as a Docker Compose service (`quay.io/keycloak/keycloak:24.0`) with a persistent volume, enabling the full auth stack to start with a single `docker-compose up` command. | Deployment test: run `docker-compose up` on a clean machine and assert Keycloak is reachable at `http://localhost:8080` and the `GET /health` endpoint of the API returns `{"ok": true}`. | MR-6 |
