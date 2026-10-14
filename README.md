# Dynamic Full-Stack Web Application (FastAPI, Redis, PostgreSQL, Docker)

A complete, production-grade dynamic web application containerized with **Docker**, built using **FastAPI**, **PostgreSQL**, and **Redis**.

---

## 🌟 Architecture & Workflow Overview

### **Workflow Requirements Fulfilled:**
1. **User Registration & Login**: Users register and log in through the modern dynamic frontend interface.
2. **Email Verification Link**: Upon registration, an email verification link with a secure unique token is generated and dispatched to the user's email address.
3. **Temporary Storage in Redis**: The user's pending details (`name`, `email`, `hashed_password`) and verification token are stored temporarily in **Redis** with a 15-minute Time-To-Live (TTL).
4. **PostgreSQL Database Storage**: Upon email verification token submission, FastAPI validates the token against Redis, retrieves the pending details, inserts the verified user into **PostgreSQL**, and flushes the temporary Redis keys.
5. **Verified Users Only**: Unverified accounts are strictly barred from logging in. Authenticated sessions produce signed JWT bearer tokens.
6. **Docker Multi-Container Compose**: All 4 services (**Frontend Nginx**, **FastAPI Backend**, **PostgreSQL 16**, **Redis 7**) are orchestrated via Docker Compose.

---

## 🏗️ Services Topology

| Service | Technology | Port | Purpose |
| :--- | :--- | :--- | :--- |
| **frontend** | Nginx & Vanilla JS/CSS | `8081` (mapped from 80) | Serves dynamic glassmorphic SPA & reverse proxies `/api/` |
| **backend** | FastAPI & Uvicorn | `8000` | REST API, bcrypt hashing, JWT issuance & business logic |
| **postgres** | PostgreSQL 16 | `5432` | Relational persistent store for verified users |
| **redis** | Redis 7 Alpine | `6379` | In-memory temporary store for pending registration data & tokens |

---

## 🚀 Quick Start (Running with Docker)

### 1. Build and Start All Containers
From the project root directory (`c:\buildwithai\sample`), run:

```bash
docker compose up --build -d
```

### 2. Access the Application
- **Web Application Frontend**: [http://localhost:8081](http://localhost:8081)
- **FastAPI Backend & Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Direct API Root**: [http://localhost:8000](http://localhost:8000)

### 3. Check Container Health
```bash
docker compose ps
```

---

## 🧪 Testing the Email Verification Flow

### Option A: Via the Web Frontend (Zero Setup Required)
1. Navigate to **[http://localhost:8081](http://localhost:8081)**.
2. Fill in the **Register** form (Name, Email, Password).
3. Once submitted, notice:
   - Redis status reflects `1 pending` registration.
   - An instant **"Pending Registration in Redis!"** banner appears with the 1-click verification link.
   - You can also click the **"Dev Inbox"** button in the top navigation bar to open the simulated mailbox and click **⚡ 1-Click Verify Token**.
4. After verification, your account is activated in PostgreSQL.
5. Switch to **Login** to sign into your account and view the live JWT session dashboard.

### Option B: Viewing Real-time Container Logs
To see the verification email link logged directly by the FastAPI backend container:

```bash
docker compose logs -f backend
```
Look for lines formatted as:
```text
============================================================
 [EMAIL DISPATCHED] To: user@example.com | Subject: Verify your email address
 Verification Link: http://localhost:8080/#verify?token=...
============================================================
```

---

## 🛡️ API Endpoints Summary

- `POST /api/auth/register`: Register user and store pending details in Redis.
- `POST /api/auth/verify`: Verify token from Redis and save to PostgreSQL.
- `POST /api/auth/login`: Authenticate verified user and return JWT bearer token.
- `GET /api/auth/me`: Protected endpoint to retrieve authenticated user details.
- `GET /api/system/status`: Live diagnostic status of PostgreSQL and Redis connectivity.
- `GET /api/dev/recent-emails`: Inspect recent simulated emails for rapid development.
- `GET /api/health`: Healthcheck endpoint for Docker.

---

## 🛑 Stopping the Application

To stop and remove containers while preserving data volumes:
```bash
docker compose down
```

To stop and delete all database and Redis volumes:
```bash
docker compose down -v
```
