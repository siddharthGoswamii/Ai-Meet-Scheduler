<div align="center">

<img src="https://img.shields.io/badge/AI%20Meet%20Scheduler-v1.0--beta-6366f1?style=for-the-badge&logo=googlecalendar&logoColor=white" alt="AI Meet Scheduler"/>

# 🤖 AI Meet Scheduler

### _Schedule smarter, not harder_

**AI-powered meeting scheduling that eliminates calendar back-and-forth forever.**  
Analyzes every attendee's Google Calendar in real-time, surfaces conflict-free slots ranked by an intelligent scoring algorithm, and provisions Google Meet rooms — all in one click.

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Google Calendar](https://img.shields.io/badge/Google%20Calendar-API-4285F4?style=flat-square&logo=googlecalendar&logoColor=white)](https://developers.google.com/calendar)
[![Deployed on Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?style=flat-square&logo=render&logoColor=white)](https://render.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

<br/>

[**Live Demo**](https://ai-meet-scheduler-eimp.onrender.com) · [**API Docs**](https://ai-meet-scheduler-eimp.onrender.com/docs) · [**Report a Bug**](issues) · [**Request Feature**](issues)

</div>

---

## 📸 Screenshots

<table>
  <tr>
    <td align="center" width="50%">
      <strong>Login — Google OAuth 2.0</strong><br/><br/>
      <img src="screenshots/login.png" alt="Login Screen" width="100%" style="border-radius:12px;"/>
      <br/><sub>One-click Google authentication with OAuth 2.0</sub>
    </td>
    <td align="center" width="50%">
      <strong>Dashboard — Smart Scheduling</strong><br/><br/>
      <img src="screenshots/dashboard.png" alt="Dashboard" width="100%" style="border-radius:12px;"/>
      <br/><sub>AI-powered slot suggestions from real calendar data</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <strong>Time Picker — Precision Booking</strong><br/><br/>
      <img src="screenshots/time-picker.png" alt="Time Picker" width="100%" style="border-radius:12px;"/>
      <br/><sub>Fine-tune meeting start time within the available window</sub>
    </td>
    <td align="center" width="50%">
      <strong>Confirmed — Google Meet Provisioned</strong><br/><br/>
      <img src="screenshots/booked.png" alt="Booked Slot" width="100%" style="border-radius:12px;"/>
      <br/><sub>Instant Meet link, WhatsApp sharing, one-click cancel</sub>
    </td>
  </tr>
</table>

> 💡 **To add screenshots**: Create a `screenshots/` folder in the root of the repo and add `login.png`, `dashboard.png`, `time-picker.png`, and `booked.png`.

---

## ✨ What makes this different?

| Feature | Traditional Scheduling | AI Meet Scheduler |
|---|---|---|
| Finding a free slot | Manual calendar checking | ✅ Automatic cross-calendar analysis |
| Back-and-forth emails | 3–5 exchanges average | ✅ Zero — one click books it |
| Google Meet link | Create manually | ✅ Auto-provisioned on booking |
| Smart time ranking | None | ✅ AI scores slots by time of day, day preference |
| Multi-attendee support | Check one by one | ✅ All calendars checked simultaneously |
| Mobile friendly | Varies | ✅ Responsive across all devices |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT (React)                        │
│         Login → Dashboard → Suggest → Book → Meet           │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS REST API
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │   Auth   │  │   Meetings   │  │    AI Scheduler     │    │
│  │  /api/   │  │   /api/      │  │   /calendar/        │    │
│  │  auth/   │  │  meetings/   │  │   suggest           │    │
│  └──────────┘  └──────────────┘  └────────────────────┘    │
└────────┬──────────────┬───────────────────┬─────────────────┘
         │              │                   │
         ▼              ▼                   ▼
   ┌──────────┐  ┌──────────────┐  ┌──────────────────┐
   │PostgreSQL│  │  Google      │  │   Google Meet    │
   │   (RDS)  │  │  Calendar    │  │      API         │
   │          │  │  API v3      │  │                  │
   └──────────┘  └──────────────┘  └──────────────────┘
```

---

## 🚀 Features

### Core
- **🔐 Google OAuth 2.0** — Secure sign-in, no passwords stored
- **📅 Real Calendar Analysis** — Live free/busy lookup across all attendees' Google Calendars
- **🤖 AI Slot Ranking** — Intelligent scoring based on time of day, day of week, back-to-back avoidance
- **📹 Auto Google Meet** — Every booking instantly creates a Meet link
- **📧 Email Invites** — Attendees receive calendar invitations automatically
- **❌ One-Click Cancel** — Cancel with automatic Google Calendar cleanup

### Smart Scheduling
- Checks availability for all attendees **simultaneously**
- Avoids scheduling on **Monday mornings** and **Friday afternoons** by default
- Ranks **Tuesday–Thursday** mid-morning slots highest
- Auto-calculates **end time** based on selected duration
- Falls back to **business-hours defaults** (09:00–18:00) if calendar fetch fails

### Security
- **JWT authentication** with configurable expiry
- **Fernet encryption** for all stored Google tokens
- **PKCE OAuth flow** — protection against CSRF attacks
- Tokens never exposed in logs or responses

---

## 🛠️ Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Framework | FastAPI 0.109 + Uvicorn |
| Database | PostgreSQL 15 + asyncpg |
| ORM | SQLAlchemy 2.0 (async) |
| Auth | Google OAuth 2.0 + JWT (python-jose) |
| Calendar | Google Calendar API v3 |
| HTTP Client | httpx (async) |
| Encryption | cryptography (Fernet) |
| Validation | Pydantic v2 |

### Frontend
| Layer | Technology |
|---|---|
| Framework | React 18 |
| Routing | React Router v6 |
| HTTP | Axios |
| Styling | Inline styles (zero dependencies) |
| Auth Flow | Cookie-based PKCE state management |

### Infrastructure
| Layer | Technology |
|---|---|
| Backend hosting | Render (Web Service) |
| Database | Render PostgreSQL |
| Frontend | Vercel / Local dev |
| CI/CD | GitHub → Render auto-deploy |

---

## 📁 Project Structure

```
ai-meet-scheduler/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py           # Google OAuth endpoints
│   │   │   ├── meetings.py       # Meeting CRUD + AI suggest
│   │   │   └── calendar.py       # Free/busy + Meet creation
│   │   ├── core/
│   │   │   └── config.py         # Pydantic settings
│   │   ├── db/
│   │   │   └── database.py       # Async SQLAlchemy engine
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── meeting.py
│   │   │   ├── meeting_attendee.py
│   │   │   └── meeting_reminder.py
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   └── meeting.py
│   │   ├── services/
│   │   │   ├── auth_service.py       # JWT + Fernet + PKCE
│   │   │   ├── google_calendar_service.py  # Calendar API client
│   │   │   └── ai_scheduler.py       # Slot ranking algorithm
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx         # Google sign-in UI
│   │   │   └── Dashboard.jsx     # Scheduling interface
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
│
└── README.md
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Google Cloud project with Calendar API enabled

### 1. Clone

```bash
git clone https://github.com/siddharthGoswamii/Ai-Meet-Scheduler.git
cd Ai-Meet-Scheduler
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your values (see Environment Variables below)

# Run
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm start
# Opens at http://localhost:3000
```

---

## 🔑 Environment Variables

Create `backend/.env`:

```env
# ── Application ──────────────────────────────────────
APP_NAME=AI Meeting Scheduler
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

# ── Server ───────────────────────────────────────────
HOST=0.0.0.0
PORT=8000

# ── Database ─────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/gmeet_scheduler
DATABASE_ECHO=False

# ── Google OAuth 2.0 ─────────────────────────────────
# Get from console.cloud.google.com → APIs & Services → Credentials
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback

# ── JWT ──────────────────────────────────────────────
SECRET_KEY=your_32+_character_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# ── Encryption (generate with command below) ─────────
ENCRYPTION_KEY=your_fernet_key_here

# ── CORS ─────────────────────────────────────────────
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_ALLOW_CREDENTIALS=True
```

**Generate encryption key:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 🌐 Google Cloud Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. **Create project** → Enable **Google Calendar API**
3. **APIs & Services → Credentials → Create OAuth 2.0 Client ID**
4. Application type: **Web application**
5. Add Authorized redirect URIs:
   ```
   http://localhost:8000/api/auth/callback
   https://your-app.onrender.com/api/auth/callback
   ```
6. Copy **Client ID** and **Client Secret** → paste into `.env`
7. **OAuth consent screen** → Add scopes:
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/calendar.events`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/auth/login` | Get Google OAuth authorization URL |
| `GET` | `/api/auth/callback` | Handle OAuth callback, issue JWT |
| `POST` | `/api/auth/refresh` | Refresh access token |
| `POST` | `/api/auth/logout` | Invalidate session |

### Meetings

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/meetings` | Create meeting + Google Meet link |
| `GET` | `/api/meetings` | List meetings (paginated, filterable) |
| `GET` | `/api/meetings/{id}` | Get meeting details |
| `PATCH` | `/api/meetings/{id}` | Update meeting |
| `DELETE` | `/api/meetings/{id}` | Cancel meeting |

### AI Scheduling

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/meetings/suggest` | Get AI-ranked free slots for all attendees |
| `POST` | `/calendar/auto-schedule` | Auto-book at optimal time |
| `GET` | `/calendar/busy-slots` | Get user's busy time slots |
| `POST` | `/calendar/find-free-slots` | Find slots across multiple attendees |

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root — returns app status |
| `GET` | `/health` | Health check |

---

### Example: Get AI Slot Suggestions

```bash
curl -X POST https://ai-meet-scheduler-eimp.onrender.com/api/meetings/suggest \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "participants": ["alice@gmail.com", "bob@company.com"],
    "duration_mins": 60,
    "preferred_date": "2026-05-27"
  }'
```

**Response:**
```json
{
  "date": "2026-05-27",
  "suggestions": [
    {
      "start": "10:00",
      "end": "11:00",
      "reason": "Mid-morning — all attendees available, peak productivity window"
    },
    {
      "start": "14:00",
      "end": "15:00",
      "reason": "Post-lunch — no conflicts detected across calendars"
    },
    {
      "start": "15:30",
      "end": "16:30",
      "reason": "Afternoon slot — good energy, avoids end-of-day fatigue"
    }
  ],
  "total_found": 4
}
```

### Example: Book a Meeting

```bash
curl -X POST https://ai-meet-scheduler-eimp.onrender.com/api/meetings \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Product Sync",
    "description": "Weekly product team standup",
    "start_time": "2026-05-27T10:00:00Z",
    "end_time": "2026-05-27T11:00:00Z",
    "timezone": "Asia/Kolkata",
    "attendees": [
      { "email": "alice@gmail.com", "display_name": "Alice", "is_required": true },
      { "email": "bob@company.com", "display_name": "Bob",   "is_required": true }
    ],
    "is_online": true
  }'
```

---

## 🚢 Deployment

### Backend — Render

1. Push to GitHub
2. **render.com → New Web Service → Connect repo**
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (all from `.env`)
6. Add a **Render PostgreSQL** database → copy connection string to `DATABASE_URL`

### Frontend — Vercel

```bash
cd frontend
npm run build
# Deploy build/ folder to Vercel or Netlify
```

Or set `REACT_APP_API_URL=https://your-app.onrender.com` in Vercel environment variables.

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t ai-meet-scheduler .
docker run -p 8000:8000 --env-file .env ai-meet-scheduler
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=app --cov-report=html

# Specific module
pytest tests/test_meetings.py -v
```

---

## 🔒 Security

- **PKCE OAuth flow** — state + code_verifier stored in httpOnly cookies
- **Fernet symmetric encryption** — all Google tokens AES-128-CBC encrypted at rest
- **JWT expiry** — short-lived access tokens (60 min), refresh tokens (7 days)
- **CORS whitelist** — explicit origins only, credentials require explicit opt-in
- **Pydantic validation** — all inputs validated at schema level before processing
- **No secrets in code** — all secrets via environment variables

---

## 🗺️ Roadmap

- [ ] **Recurring meetings** — weekly / bi-weekly scheduling
- [ ] **Slack / Teams notifications** — meeting reminders via chat
- [ ] **Smart rescheduling** — AI suggests reschedule when conflicts arise
- [ ] **Analytics dashboard** — meeting load, busiest hours, attendee patterns
- [ ] **Multi-timezone support** — automatically convert slots per attendee timezone
- [ ] **Microsoft Outlook integration** — support non-Google calendars
- [ ] **Mobile app** — React Native companion app

---

## 🤝 Contributing

Contributions are welcome!

```bash
# Fork the repo and clone
git clone https://github.com/YOUR_USERNAME/Ai-Meet-Scheduler.git

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes, then
git add .
git commit -m "feat: describe your change"
git push origin feature/your-feature-name

# Open a Pull Request on GitHub
```

Please follow conventional commit format: `feat:`, `fix:`, `docs:`, `refactor:`

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👥 Team

Built with ❤️ during the hackathon by the **AI Meet Scheduler** team.

| Role | Contribution |
|---|---|
| Backend | FastAPI, Google OAuth, Calendar API, PostgreSQL |
| Data Engineering | ETL pipeline, pricing database, cost calculation engine |
| DevOps | Render deployment, CI/CD, Docker, environment management |

---

<div align="center">

**⭐ If this project helped you, consider giving it a star!**

<br/>

[![GitHub stars](https://img.shields.io/github/stars/siddharthGoswamii/Ai-Meet-Scheduler?style=social)](https://github.com/siddharthGoswamii/Ai-Meet-Scheduler)

<br/>

_Made with FastAPI + React + Google Calendar API_

</div>
