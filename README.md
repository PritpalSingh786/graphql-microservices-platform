# 🚀 GraphQL Microservices Platform

A **production-ready GraphQL microservices platform** with pure JWT authentication, **Redis-based token management** (no database tokens!), real-time WebSocket notifications, file upload support, and Docker containerization.

---

## 📋 Table of Contents

* [Overview](#-overview)
* [Architecture](#-architecture)
* [Features](#-features)
* [Tech Stack](#-tech-stack)
* [Project Structure](#-project-structure)
* [Quick Start](#-quick-start)
* [API Endpoints](#-api-endpoints)
* [WebSocket Testing](#-websocket-testing)
* [Environment Variables](#-environment-variables)
* [Docker Commands](#-docker-commands)
* [Testing](#-testing)
* [Postman Collection](#-postman-collection)
* [Troubleshooting](#-troubleshooting)
* [Future Plans](#-future-plans)

---

## 📖 Overview

This is a **complete microservices-based authentication and content management platform** built from scratch. It features a **pure JWT implementation** (no third-party libraries), **Redis-first token storage** with automatic TTL expiry (no Celery Beat needed!), **GraphQL APIs**, **real-time WebSocket notifications**, and **Docker containerization** with 7 services.

### Current Status: ✅ Fully Functional Locally

| Component             | Status    |
| --------------------- | --------- |
| Auth Service          | ✅ Working |
| Blog Service          | ✅ Working |
| API Gateway           | ✅ Working |
| WebSocket             | ✅ Working |
| File Upload           | ✅ Working |
| PostgreSQL            | ✅ Working |
| MongoDB               | ✅ Working |
| Redis + Celery Worker | ✅ Working |

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                         Client (Browser/Postman)                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API Gateway (Port 8000)                      │
│                    JWT Verification + Routing                    │
└──────────────┬─────────────────────────────┬────────────────────┘
               │                             │
               ▼                             ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│    Auth Service          │   │    Blog Service          │
│       (Port 8001)        │   │       (Port 8002)        │
│                          │   │                          │
│  • User Registration     │   │  • Create Upload         │
│  • Login/Logout          │   │  • File Upload           │
│  • JWT Tokens (Pure)     │   │  • Get Uploads           │
│  • Email Verification    │   │  • Delete Uploads        │
│  • Password Reset        │   │                          │
│  • Device Management     │   │                          │
│  • Session Management    │   │                          │
└──────────┬───────────────┘   └──────────┬───────────────┘
           │                              │
           ▼                              ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│       PostgreSQL         │   │        MongoDB           │
│    (User + Device)       │   │    (Blog Data)           │
│  ❌ NO token tables!      │   │                          │
└──────────────────────────┘   └──────────────────────────┘

                    ┌──────────────────────────┐
                    │     Redis (Primary!)      │
                    │  • Refresh Tokens (Hash)  │
                    │  • Blacklist (String)     │
                    │  • User Sessions (Set)    │
                    │  • Device Mapping         │
                    │  • Auto TTL Cleanup       │
                    └──────────────────────────┘

                    ┌──────────────────────────┐
                    │   Celery Worker Only      │
                    │   (Email Async Tasks)     │
                    │   ❌ No Celery Beat!      │
                    └──────────────────────────┘
```

---

## 🔧 Middleware Architecture

All requests go through a layered middleware pipeline for authentication, logging, and security.

### API Gateway JWT Middleware

**📁 Path:** `api_gateway/middleware/jwt_middleware.py`

| Function             | Description                                            |
| -------------------- | ------------------------------------------------------ |
| Public Operations    | `register`, `login`, `verifyEmail` → No token required |
| Protected Operations | `me`, `myDevices`, `logout` → Valid JWT required       |
| Token Validation     | Checks expiry, signature, issuer, audience             |
| Error Response       | Returns `401 Unauthorized` for invalid/expired tokens  |

### Auth Service GraphQL Middleware

**📁 Path:** `auth_service/gql_schema/middleware.py`

| Function              | Description                                  |
| --------------------- | -------------------------------------------- |
| Token Extraction      | From `Authorization: Bearer <token>` header  |
| Redis Blacklist Check | O(1) lookup - no database query!             |
| User Lookup           | Fetches user from PostgreSQL using `user_id` |
| Context Attachment    | Attaches `user` object to GraphQL context    |

### Auth Service Logging Middleware

**📁 Path:** `auth_service/middleware/simple_middleware.py`

| Function               | Description                  |
| ---------------------- | ---------------------------- |
| Request Logging        | Logs method, path, timestamp |
| Performance Monitoring | Tracks request duration      |

### Blog Service GraphQL Middleware

**📁 Path:** `blog_service/gql_schema/middleware.py`

| Function         | Description                                  |
| ---------------- | -------------------------------------------- |
| Token Extraction | From Authorization header                    |
| Lightweight Auth | Decodes JWT without DB query for performance |

### WebSocket JWT Middleware

**📁 Path:** `auth_service/users/websocketjwtmiddleware.py`

| Function              | Description                                    |
| --------------------- | ---------------------------------------------- |
| Token Extraction      | From WebSocket URL query string (`?token=xxx`) |
| Redis Blacklist Check | Async O(1) lookup                              |
| Scope Attachment      | Sets `user` and `device_id` in WebSocket scope |

---

## ✨ Features

### 🔐 Authentication & Security (Pure PyJWT + Redis)

* **Pure PyJWT Implementation** - No third-party JWT libraries, written from scratch
* **Redis-First Token Storage** - O(1) token validation, 10x faster than database
* **Automatic Token Expiry** - Redis TTL handles cleanup, **no Celery Beat needed!**
* **Access & Refresh Tokens** - 15 min access, 7 day refresh with rotation
* **Token Blacklisting** - Immediate revocation in Redis (O(1) lookup)
* **Rate Limiting** - Login: 5/min, Register: 3/min, Password reset: 3/min
* **Device Tracking** - Track active devices with unique device IDs
* **Session Management** - Limit concurrent sessions (configurable, default 5)
* **Email Verification** - Verify user emails with expiry (24 hours)
* **Password Reset Flow** - Secure password recovery with 2-hour expiry

### 🗄️ Redis Token Storage Architecture

| Key Pattern           | Type   | Purpose                 | TTL    |
| --------------------- | ------ | ----------------------- | ------ |
| `rt:<jti>`            | Hash   | Refresh token data      | 7 days |
| `bl:<jti>`            | String | Blacklisted tokens      | 7 days |
| `user:<id>:tokens`    | Set    | User's token JTIs       | 7 days |
| `device:<uuid>:token` | String | Device to token mapping | 7 days |

### 📝 GraphQL APIs (30+ endpoints)

**Auth Service (20+ mutations/queries):**

* `register`, `login`, `logout`, `refreshToken`
* `me`, `changePassword`, `verifyEmail`
* `passwordResetRequest`, `setNewPassword`
* `myDevices`, `removeDevice`, `removeOtherDevices`
* `mySessions` (fetches from Redis!)

**Blog Service (10+ mutations/queries):**

* `createUpload`, `updateUpload`, `deleteUpload`
* `allUploads`, `myUploads`, `upload`

### 📡 WebSocket Real-time

* **Connection**: `ws://localhost:8001/ws/auth/?token=<jwt>`
* **Session Kill Notifications**: Real-time alerts when session terminated
* **Device Logout**: Instant notification when logged out from other devices

### 📁 File Upload

* **Multi-file upload** support
* **Validation**: Max 5MB, allowed formats (jpg, jpeg, png, gif, webp)
* **Automatic storage** in `blog_service/media/blog_uploads/`

---

## 🛠️ Tech Stack

| Category               | Technology                      | Version |
| ---------------------- | ------------------------------- | ------- |
| **Backend**            | Django                          | 5.2.12  |
| **API**                | Graphene (GraphQL)              | 3.2.0   |
| **Auth**               | PyJWT (Pure implementation)     | 2.12.0  |
| **Database (User)**    | PostgreSQL                      | 15      |
| **Database (Content)** | MongoDB                         | 7       |
| **Token Storage**      | Redis (Primary!)                | 7       |
| **Cache/Queue**        | Redis                           | 7       |
| **Task Queue**         | Celery (Worker only - no Beat!) | 5.6.2   |
| **WebSocket**          | Django Channels + Daphne        | 4.2.0   |
| **Container**          | Docker + Docker Compose         | -       |
| **Testing**            | Django Test                     | -       |
| **Async Server**       | Daphne                          | 4.1.2   |

---

## 📁 Project Structure

```text
microservices-graphql/
│
├── api_gateway/                    # API Gateway Service (Port 8000)
│   ├── apps/auth_gateway/          # Auth service proxy
│   ├── apps/blog_gateway/          # Blog service proxy
│   ├── middleware/jwt_middleware.py # JWT verification
│   └── api_gateway/settings.py
│
├── auth_service/                   # Authentication Service (Port 8001)
│   ├── users/                      # User models, JWT utils, WebSocket
│   │   ├── models.py               # User, Device ONLY! (No token models!)
│   │   ├── utils.py                # Pure JWT + Redis functions
│   │   ├── redis_token_manager.py  # Redis operations (Hash, Set, TTL)
│   │   ├── consumers.py            # WebSocket consumer
│   │   └── tasks.py                # Celery email tasks (no cleanup!)
│   ├── gql_schema/                 # GraphQL schema
│   │   ├── mutations.py            # 15+ mutations
│   │   ├── queries.py              # 5+ queries
│   │   └── types.py                # GraphQL types
│   └── auth_service/settings.py
│
├── blog_service/                   # Blog Service (Port 8002)
│   ├── blogs/models.py             # Upload model (MongoDB)
│   ├── blogs/utils.py              # File upload utilities
│   └── gql_schema/                 # GraphQL schema for blog
│
├── docker-compose.yml              # 7 services orchestration (No Beat!)
├── tests/                          # Integration tests
│   ├── test_integration.py
│   └── test_websocket.py
├── Microservices-GraphQL.postman_collection.json
└── scripts/
    ├── migrate.sh
    └── dev.sh
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites

* Docker & Docker Compose installed
* Git
* 8GB+ RAM recommended

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/graphql-microservices-platform.git
cd graphql-microservices-platform
```

### Step 2: Environment Setup

```bash
# Create .env files (copy from examples below)
nano api_gateway/.env
nano auth_service/.env
nano blog_service/.env
```

### Step 3: Build and Run

```bash
# Build and start all 7 services (No Beat!)
docker compose up -d --build

# Wait for services to be ready (30 seconds)
sleep 30

# Run database migrations
docker compose exec auth_service python manage.py migrate

# Check all services are running
docker compose ps
```

**Expected Output:**

```text
NAME                    STATUS
api_gateway             Up
auth_service            Up
blog_service            Up
postgres_auth           Up (healthy)
mongo_blog              Up (healthy)
redis                   Up (healthy)
celery_worker           Up
# ❌ NO celery_beat - Redis handles token expiry!
```

### Step 4: Test the API

```bash
# Register a user
curl -X POST http://localhost:8000/graphql/auth/ \
  -H "Content-Type: application/json" \
  -d '{
    "operationName": "RegisterUser",
    "query": "mutation RegisterUser($username: String!, $email: String!, $password: String!) { register(username: $username, email: $email, password: $password) { success message } }",
    "variables": {
      "username": "testuser",
      "email": "test@test.com",
      "password": "Test@123"
    }
  }'

# Login to get token
curl -X POST http://localhost:8000/graphql/auth/ \
  -H "Content-Type: application/json" \
  -d '{
    "operationName": "Login",
    "query": "mutation Login($username: String!, $password: String!, $platform: String!, $deviceName: String!) { login(username: $username, password: $password, platform: $platform, deviceName: $deviceName) { success message accessToken refreshToken } }",
    "variables": {
      "username": "testuser",
      "password": "Test@123",
      "platform": "web",
      "deviceName": "Postman"
    }
  }'
```

---

## 📡 API Endpoints

### GraphQL Playgrounds

| Service                        | URL                                                                         |
| ------------------------------ | --------------------------------------------------------------------------- |
| **Auth Service (via Gateway)** | `http://localhost:8000/graphql/auth/`                                       |
| **Blog Service (via Gateway)** | `http://localhost:8000/graphql/blog/`                                       |
| **Auth Service (Direct)**      | `http://localhost:8001/graphql/`                                            |
| **Blog Service (Direct)**      | `http://localhost:8002/graphql/`                                            |
| **pgAdmin**                    | `http://localhost:5050` ([admin@admin.com](mailto:admin@admin.com) / admin) |
| **Tiny RDM (Redis GUI)**       | Download from: `https://github.com/tiny-craft/tiny-rdm`                     |
| **MongoDB Compass**            | `mongodb://localhost:27018/`                                                |

### Sample Queries

#### Register

```graphql
mutation {
  register(username: "testuser", email: "test@test.com", password: "Test@123") {
    success
    message
  }
}
```

#### Login

```graphql
mutation {
  login(username: "testuser", password: "Test@123", platform: "web", deviceName: "Chrome") {
    success
    message
    accessToken
    refreshToken
    user {
      id
      username
      email
    }
  }
}
```

#### Get Current User (with Authorization header)

```graphql
query {
  me {
    id
    username
    email
    emailVerified
  }
}
```

---

## 🔌 WebSocket Testing

### Connection URL

```text
ws://localhost:8001/ws/auth/?token=YOUR_ACCESS_TOKEN
```

### Test with Python

```python
import asyncio
import websockets
import json

async def test_websocket():
    token = "YOUR_ACCESS_TOKEN"
    uri = f"ws://localhost:8001/ws/auth/?token={token}"

    async with websockets.connect(uri) as websocket:
        print("✅ Connected!")
        await websocket.send(json.dumps({"type": "ping"}))
        response = await websocket.recv()
        print(f"Response: {response}")

asyncio.run(test_websocket())
```

---

## 🔧 Environment Variables

### `api_gateway/.env`

```env
GATEWAY_SECRET_KEY=your-secret-key
DEBUG=True
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
AUTH_SERVICE_URL=http://auth_service:8001
BLOG_SERVICE_URL=http://blog_service:8002
REDIS_URL=redis://redis:6379/0
```

### `auth_service/.env`

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALGORITHM=HS256
JWT_ISSUER=my-app
JWT_AUDIENCE=my-users
ACCESS_TOKEN_LIFETIME=15
REFRESH_TOKEN_LIFETIME=7
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
FRONTEND_URL=http://localhost:3000
REDIS_URL=redis://redis:6379/0
DB_NAME=auth_db
DB_USER=postgres
DB_PASSWORD=Admin@123
DB_HOST=postgres_auth
DB_PORT=5432
```

### `blog_service/.env`

```env
SECRET_KEY=blog-secret-key
DEBUG=True
MONGO_DB_NAME=blog_db
MONGO_HOST=mongo_blog
MONGO_PORT=27017
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
```

---

## 🐳 Docker Commands

```bash
# Start all services
docker compose up -d

# Rebuild and start
docker compose up -d --build

# Stop all services
docker compose down

# View logs (all services)
docker compose logs -f

# View specific service logs
docker compose logs auth_service -f
docker compose logs blog_service -f
docker compose logs api_gateway -f

# Run migrations
docker compose exec auth_service python manage.py migrate

# Create superuser
docker compose exec auth_service python manage.py createsuperuser

# Check Redis tokens
docker compose exec redis redis-cli KEYS "rt:*"

# Access PostgreSQL
docker compose exec postgres_auth psql -U postgres -d auth_db

# Check service health
docker compose ps
```

---

## 🧪 Testing

### Run All Tests

```bash
# Make test script executable
chmod +x scripts/run_tests.sh

# Run all tests
./scripts/run_tests.sh
```

### Run Individual Tests

```bash
# Auth service tests
docker compose exec auth_service python manage.py test users.tests

# Blog service tests
docker compose exec blog_service python manage.py test blogs.tests

# Integration tests (from host)
python tests/test_integration.py

# WebSocket tests
python tests/test_websocket.py
```

---

## 📦 Postman Collection

Import `Microservices-GraphQL.postman_collection.json` into Postman for complete API testing.

### Includes:

* 30+ pre-configured requests
* Environment variables (`accessToken`, `refreshToken`)
* Auth token auto-management
* File upload examples

---

## 🐛 Troubleshooting

| Issue                          | Solution                                                              |
| ------------------------------ | --------------------------------------------------------------------- |
| `DisallowedHost` error         | Patch already applied in `settings.py`                                |
| `Connection refused`           | Wait 30 seconds for services to start                                 |
| `Port already in use`          | Change port in `.env` files                                           |
| `Redis tokens not visible`     | Check port mapping: Tiny RDM on `6380`, not `6379`                    |
| `MongoDB connection failed`    | Check `MONGO_HOST=mongo_blog` (not `localhost`)                       |
| `PostgreSQL connection failed` | Ensure `postgres_auth` container is healthy                           |
| `WebSocket 404 error`          | Use Daphne: `daphne -b 0.0.0.0 -p 8001 auth_service.asgi:application` |
| `No tokens in Redis`           | Login again and check `docker compose exec redis redis-cli KEYS "*"`  |

### Debugging Commands

```bash
# Check all service status
docker compose ps

# Check Redis tokens (should see rt:*, user:*, device:*)
docker compose exec redis redis-cli KEYS "*"

# Check token TTL (automatic expiry working)
docker compose exec redis redis-cli TTL "rt:your-jti"

# Verify no celery_beat running
docker compose ps | grep beat  # Should return nothing!

# Check database has no token tables
docker compose exec postgres_auth psql -U postgres -d auth_db -c "\dt" | grep token
# Should return nothing!
```

---

## 📊 Current Development Status

| Feature                    | Status                          |
| -------------------------- | ------------------------------- |
| **Local Development**      | ✅ Fully Functional              |
| **Docker Compose**         | ✅ 7 Services Running (No Beat!) |
| **GraphQL APIs**           | ✅ 30+ Endpoints                 |
| **Pure JWT Auth**          | ✅ Working                       |
| **Redis Token Storage**    | ✅ Working (O(1) lookups)        |
| **Automatic Token Expiry** | ✅ Redis TTL (No Celery Beat!)   |
| **WebSocket**              | ✅ Working                       |
| **File Upload**            | ✅ Working                       |
| **Email Service**          | ✅ Working (via Celery Worker)   |
| **Database Integration**   | ✅ PostgreSQL + MongoDB          |
| **Testing Suite**          | ✅ Complete                      |

---

## 🔮 Future Plans

* [ ] Deploy to Oracle Cloud Free Tier (4 ARM64 cores + 24GB RAM)
* [ ] Set up CI/CD pipeline with GitHub Actions
* [ ] Add monitoring with Prometheus + Grafana
* [ ] Implement rate limiting per user/IP
* [ ] Add API versioning
* [ ] Create React/Next.js frontend
* [ ] Add GraphQL subscriptions for real-time updates
* [ ] Implement refresh token rotation with reuse detection

---

## 🙏 Acknowledgments

* **Django** & **Graphene** for the amazing framework
* **Docker** for containerization
* **Redis** for blazing fast token storage
* All open-source contributors

---

## 📧 Contact

**Author:** Pritpal Singh
**Project:** GraphQL Microservices Platform
**GitHub:** `github.com/PritpalSingh786`

---

**Built with ❤️ using Django, GraphQL, Docker, Redis (No Celery Beat!), and Pure PyJWT**
