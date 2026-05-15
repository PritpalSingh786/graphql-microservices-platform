# 🚀 GraphQL Microservices Platform

A GraphQL-based microservices platform built using Django, Graphene, Redis, and Docker.

The project demonstrates JWT authentication workflows, Redis-backed token/session management, GraphQL APIs, WebSocket communication, file upload handling, and Docker-based service orchestration across multiple backend services.

---

# 📖 Overview

This project follows a microservices-oriented backend architecture with separate services for authentication, API gateway routing, and content management.

Key areas covered:

* JWT authentication workflows using PyJWT
* Redis-based token and session management
* GraphQL APIs with Graphene
* WebSocket communication using Django Channels
* File upload support
* Docker Compose-based multi-service setup
* PostgreSQL and MongoDB integration
* Asynchronous background tasks using Celery

---

# 🏗️ Architecture

```text
Client
   │
   ▼
API Gateway
   │
   ├── Auth Service
   └── Blog Service
        │
        ├── PostgreSQL (User Data)
        ├── MongoDB (Content Data)
        └── Redis (Token & Session Management)

WebSocket Communication
Celery Background Tasks
Dockerized Multi-Service Environment
```

---

# 🔧 Middleware Architecture

## API Gateway JWT Middleware

* JWT verification and request routing
* Public and protected GraphQL operation handling
* Token validation and authorization checks

## Auth Service Middleware

* Token extraction from request headers
* Redis-based blacklist/session validation
* User context attachment for GraphQL requests

## Logging Middleware

* Request logging
* Basic request timing and monitoring

## WebSocket JWT Middleware

* JWT validation for WebSocket connections
* WebSocket scope authentication
* Device/session association handling

---

# ✨ Features

## 🔐 Authentication & Security

* JWT Authentication using PyJWT
* Access & Refresh Token workflows
* Refresh token rotation
* Redis-based token blacklisting
* Device-based session tracking
* Session management support
* Email verification workflow
* Password reset functionality
* Rate limiting on authentication endpoints

---

## 🗄️ Redis Token Architecture

| Key Pattern           | Purpose                      |
| --------------------- | ---------------------------- |
| `rt:<jti>`            | Refresh token storage        |
| `bl:<jti>`            | Blacklisted token references |
| `user:<id>:tokens`    | User session/token mapping   |
| `device:<uuid>:token` | Device-token association     |

---

# 🔐 JWT Security Implementation

## Access Token

* Short-lived access token for API authentication
* Used for protected GraphQL operations

## Refresh Token

* Used to generate new access tokens
* Stored securely using HttpOnly cookies for web clients
* Managed through Redis-backed session workflows

---

# 🔁 Refresh Token Rotation

Each refresh request:

1. Issues a new access token
2. Generates a new refresh token
3. Invalidates the previous refresh token
4. Updates Redis token references

This helps reduce token replay risks and improves session security.

---

# 🚫 Token Blacklisting

* Refresh tokens are blacklisted on logout
* Prevents reuse of invalidated tokens
* Blacklist references are managed through Redis

When using refresh token rotation and token blacklisting, JWT authentication becomes a hybrid approach combining stateless access tokens with stateful refresh token/session management.

---

# 🔐 Advanced JWT Security Practices

## 🚫 Minimal Token Claims

Tokens avoid storing sensitive user information such as:

* Email
* Username
* Personal details

Only minimal claims are included:

* `user_id`
* `device_id`
* `jti`

---

## 🧾 Issuer (`iss`) Validation

Each token includes an issuer claim to validate token origin.

Example:

```json
{
  "iss": "my-app"
}
```

---

## 🎯 Audience (`aud`) Validation

Each token includes an audience claim to validate intended token usage.

Example:

```json
{
  "aud": "my-app-users"
}
```

---

## 🔐 Secure Algorithm Enforcement

* Explicit JWT algorithm validation using `HS256`
* Prevents insecure algorithm usage

---

## 🍪 Secure Cookie Storage

Refresh tokens can be stored using secure cookie settings:

```python
httponly=True
secure=True
samesite="Strict"
```

This helps improve protection against XSS and CSRF-related risks.

---

## 🔄 Token Replay Protection

* Refresh tokens rotate on every refresh request
* Previous refresh tokens are invalidated
* Redis helps manage token/session references

---

## 📱 Device-Based Token Binding

Each token is associated with a `device_id`.

This enables:

* Device tracking
* Device-level logout
* Multi-device session management

---

## ⚡ Real-Time Session Invalidation

* WebSocket-based logout notifications
* Session invalidation events across connected devices
* Real-time session handling workflows

---

## 🧠 Secure Token Lifecycle

* Short-lived access tokens
* Rotating refresh tokens
* Redis TTL-based expiry handling

---

## 📡 WebSocket Features

* Real-time session notifications
* Device logout notifications
* WebSocket authentication using JWT
* Redis-backed channel layer communication

---

## 📝 GraphQL APIs

### Auth Service Operations

* `register`
* `login`
* `logout`
* `refreshToken`
* `verifyEmail`
* `passwordResetRequest`
* `setNewPassword`
* `changePassword`
* `me`
* `myDevices`
* `removeDevice`
* `removeOtherDevices`
* `mySessions`

### Blog Service Operations

* `createUpload`
* `updateUpload`
* `deleteUpload`
* `allUploads`
* `myUploads`
* `upload`

---

# 🔌 API Endpoints

## API Gateway

| Service      | Endpoint                              |
| ------------ | ------------------------------------- |
| Auth GraphQL | `http://localhost:8000/graphql/auth/` |
| Blog GraphQL | `http://localhost:8000/graphql/blog/` |

---

## Direct Service Access

| Service      | Endpoint                         |
| ------------ | -------------------------------- |
| Auth Service | `http://localhost:8001/graphql/` |
| Blog Service | `http://localhost:8002/graphql/` |

---

## WebSocket Endpoint

```text
ws://localhost:8001/ws/auth/?token=<access_token>
```

---

# 📁 File Upload Features

* Multi-file upload support
* File validation handling
* Media storage integration

---

# 🛠️ Tech Stack

| Category            | Technology      |
| ------------------- | --------------- |
| Backend             | Django          |
| GraphQL             | Graphene        |
| Authentication      | PyJWT           |
| Database            | PostgreSQL      |
| Content Storage     | MongoDB         |
| Token/Session Store | Redis           |
| Async Tasks         | Celery          |
| WebSockets          | Django Channels |
| Containerization    | Docker          |
| Async Server        | Daphne          |

---

# 📁 Project Structure

```text
microservices-graphql/
│
├── api_gateway/
│   ├── apps/
│   ├── middleware/
│   └── settings.py
│
├── auth_service/
│   ├── users/
│   ├── gql_schema/
│   └── settings.py
│
├── blog_service/
│   ├── blogs/
│   ├── gql_schema/
│   └── settings.py
│
├── tests/
├── scripts/
├── docker-compose.yml
└── postman_collection.json
```

---

# 🚀 Local Development Setup

## Prerequisites

* Docker & Docker Compose
* Python 3
* Redis
* PostgreSQL
* MongoDB

---

## Clone Repository

```bash
git clone https://github.com/PritpalSingh786/graphql-microservices-platform.git
```

---

## Start Services

```bash
docker compose up -d --build
```

---

## Run Database Migrations

```bash
docker compose exec auth_service python manage.py migrate
```

---

## Check Running Containers

```bash
docker compose ps
```

---

# 🔧 Environment Variables

## Auth Service

```env
JWT_SECRET_KEY=your-secret
JWT_ALGORITHM=HS256
REDIS_URL=redis://redis:6379/0
DB_NAME=auth_db
```

---

## Blog Service

```env
MONGO_DB_NAME=blog_db
JWT_SECRET_KEY=your-secret
```

---

# 🐳 Docker Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# Run migrations
docker compose exec auth_service python manage.py migrate
```

---

# 🧪 Testing

```bash
# Run Django tests
python manage.py test
```

---

# 📊 Current Development Status

| Component         | Status    |
| ----------------- | --------- |
| Auth Service      | ✅ Working |
| Blog Service      | ✅ Working |
| API Gateway       | ✅ Working |
| Redis Integration | ✅ Working |
| WebSocket Support | ✅ Working |
| File Upload       | ✅ Working |
| Docker Setup      | ✅ Working |

---

# 🔮 Future Improvements

* CI/CD Pipeline
* OAuth Integration
* GraphQL Subscriptions
* Monitoring & Logging
* Kubernetes Deployment
* Role-Based Access Control (RBAC)

---

# 🧠 What This Project Demonstrates

* GraphQL-based microservices architecture
* JWT authentication workflows
* Redis-backed token/session handling
* WebSocket communication
* Docker-based service orchestration
* PostgreSQL & MongoDB integration
* Async task processing using Celery
* Device/session management workflows

---

# 👨‍💻 Author

**Pritpal Singh**

🔗 [GitHub Profile](https://github.com/PritpalSingh786?utm_source=chatgpt.com)

🔗 [Project Repository](https://github.com/PritpalSingh786/graphql-microservices-platform?utm_source=chatgpt.com)
