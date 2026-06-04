# 🚀 GraphQL Microservices Platform

A GraphQL-based microservices platform built using Django, Graphene, Redis, and Docker.

The project demonstrates JWT authentication workflows, Redis-backed token/session management, GraphQL APIs, WebSocket communication, file upload handling, and Docker-based service orchestration across multiple backend services.

---

## 📖 Overview

This project follows a microservices-oriented backend architecture with separate services for authentication, API gateway routing, and content management.

Key areas covered:

- JWT authentication workflows using PyJWT
- Redis-based token and session management
- GraphQL APIs with Graphene
- WebSocket communication using Django Channels
- File upload support
- Docker Compose-based multi-service setup
- PostgreSQL and MongoDB integration
- Asynchronous background tasks using Celery
- Email verification and password reset workflows
- Device-based session tracking

---

## 🏗️ Architecture

```text
Client
   │
   ▼
API Gateway (Port 8000)
   │
   ├── Auth Service (Port 8001) ─── PostgreSQL (User Data)
   │                              ─── Redis (Token & Session Management)
   │
   └── Blog Service (Port 8002)  ─── MongoDB (Content Data)

WebSocket Communication (Port 8001)
Celery Background Tasks (Redis Broker)
Dockerized Multi-Service Environment
```

---

## 🔧 Middleware Architecture

### API Gateway JWT Middleware

- JWT verification for protected GraphQL operations
- Public operation detection (register, login, forgotPassword, verifyEmail)
- Token validation and 401 responses for unauthenticated requests
- Request routing to auth and blog services

### Auth Service Middleware

- Token extraction from Authorization header
- Redis-based token validation
- User context attachment for GraphQL resolvers
- Device ID and platform tracking

### WebSocket JWT Middleware

- JWT validation for WebSocket connections
- User authentication for real-time notifications
- Device/session association handling

---

## ✨ Features

### 🔐 Authentication & Security

- JWT Authentication using PyJWT
- Access & Refresh Token workflows
- Refresh token rotation
- Redis-based token storage and validation
- Device-based session tracking
- Multi-device session management
- Email verification workflow
- Password reset functionality (template-based)
- Secure password change with current password
- New login alert with secure reset link

---

## 🗄️ Redis Token Architecture

| Key Pattern | Purpose |
|---|---|
| `hash-rt-for-user-{user_id}` | User refresh tokens hash store |
| `pwd_reset:{user_id}` | Secure password reset token storage |
| `password_reset:{user_id}:*` | Password reset tokens (5 min expiry) |
| `email_verify:{user_id}:{token}` | Email verification tokens (5 min) |

---

## 🔐 JWT Security Implementation

### Access Token

- Short-lived access token for API authentication (15–30 minutes)
- Used for protected GraphQL operations
- Contains: `user_id`, `device_id`, `platform`, `jti`

### Refresh Token

- Used to generate new access tokens (7 days lifetime)
- Stored in Redis with device information
- Supports refresh token rotation

---

## 🔁 Refresh Token Rotation

Each refresh request:

1. Validates existing refresh token from Redis
2. Issues a new access token
3. Generates a new refresh token
4. Stores new token in Redis
5. Removes old refresh token

This helps reduce token replay risks and improves session security.

---

## 🚫 Token Blacklisting

- Refresh tokens are removed from Redis on logout
- Prevents reuse of invalidated tokens
- No blacklist table needed — Redis storage handles invalidation

---

## 🔐 Advanced JWT Security Practices

### 🚫 Minimal Token Claims

Tokens avoid storing sensitive user information:

- Email
- Username
- Personal details

Only minimal claims are included:

- `user_id` (UUID)
- `device_id` (UUID)
- `platform` (web/mobile)
- `jti` (unique identifier)
- `type` (access/refresh)

---

### 🧾 Issuer (`iss`) Validation

Each token includes an issuer claim to validate token origin:

```json
{
  "iss": "my-app"
}
```

---

### 🎯 Audience (`aud`) Validation

Each token includes an audience claim to validate intended usage:

```json
{
  "aud": "my-users"
}
```

---

### 🔐 Secure Algorithm Enforcement

- Explicit JWT algorithm validation using `HS256`
- Prevents insecure algorithm usage

---

### 🍪 Secure Cookie Storage (Web)

Refresh tokens can be stored using secure cookie settings:

```python
httponly=True
secure=False  # Set True in production
samesite="Lax"
path="/api/users/"
```

---

### 🔄 Token Replay Protection

- Refresh tokens rotate on every refresh request
- Previous refresh tokens are invalidated from Redis
- Prevents token replay attacks

---

### 📱 Device-Based Token Binding

Each token is associated with a `device_id` from the `Device` model.

This enables:

- Device tracking
- Device-level logout
- Multi-device session management
- New device login alerts

---

### ⚡ Real-Time Session Invalidation

- WebSocket-based logout notifications
- Session invalidation events across all devices
- Real-time session handling when password changes

---

### 🧠 Secure Token Lifecycle

- Short-lived access tokens (15–30 minutes)
- Rotating refresh tokens (7 days)
- Redis TTL-based expiry handling
- Automatic cleanup of expired tokens

---

## 📡 WebSocket Features

- Real-time logout notifications
- Device logout events
- WebSocket authentication using JWT token query parameter
- Redis-backed channel layer communication

---

## 📝 GraphQL APIs

### Auth Service Mutations

| Mutation | Description | Auth Required |
|---|---|---|
| `register` | Create new user account | ❌ No |
| `login` | Authenticate user | ❌ No |
| `refreshToken` | Get new access token | ❌ No |
| `logout` | Invalidate refresh token | ❌ No |
| `forgotPassword` | Request password reset email | ❌ No |
| `verifyEmail` | Verify email with token | ❌ No |
| `changePassword` | Reset password with token | ❌ No |
| `secureChangePassword` | Change password with current password | ❌ No (token from email) |

### Auth Service Queries

| Query | Description | Auth Required |
|---|---|---|
| `me` | Get current user info | ✅ Yes |
| `myDevices` | Get user's devices | ✅ Yes |
| `getUser` | Get user by ID | ✅ Yes |

### Blog Service Mutations

| Mutation | Description | Auth Required |
|---|---|---|
| `createUpload` | Create new blog post | ✅ Yes |
| `updateUpload` | Update existing post | ✅ Yes |
| `deleteUpload` | Delete blog post | ✅ Yes |

### Blog Service Queries

| Query | Description | Auth Required |
|---|---|---|
| `allUploads` | Get all blog posts | ❌ No |
| `myUploads` | Get user's posts | ✅ Yes |
| `upload` | Get single post by ID | ❌ No |

---

## 🔌 API Endpoints

### API Gateway

| Service | Endpoint | Port |
|---|---|---|
| Auth GraphQL | `http://localhost:8000/graphql/auth/` | 8000 |
| Blog GraphQL | `http://localhost:8000/graphql/blog/` | 8000 |

---

### Direct Service Access (Development)

| Service | Endpoint | Port |
|---|---|---|
| Auth Service | `http://localhost:8001/graphql/` | 8001 |
| Blog Service | `http://localhost:8002/graphql/` | 8002 |

---

### WebSocket Endpoint

```text
ws://localhost:8001/ws/auth/?token=<access_token>
```

---

### Template Endpoints (Email Links)

| Template | URL Pattern |
|---|---|
| Email Verification | `/verify-email?user_id={user_id}&token={token}` |
| Password Reset | `/password-change-template/{user_id}/{token}/` |
| Secure Password Change | `/secure-password-change-template/{user_id}/{token}/` |
| Login Page | `/login/` |

---

## 📁 File Upload Features

- Single and multi-file upload support
- Image validation (size, type)
- Cloud storage integration ready
- Media URL generation

---

## 🐳 Docker & Base Image Usage

This project uses Dockerized services with custom Docker base images to provide a consistent and isolated development environment across all microservices.

Benefits:

- Consistent runtime environment across all services
- Faster onboarding and setup process
- Reduces duplication by allowing multiple images to share and reuse common layers, saving storage space and improving build efficiency.
- Simplified dependency management
- Lightweight and reproducible containers
- Easier deployment and scalability
- Improved development-to-production consistency
- Better microservices orchestration using Docker Compose

Docker Compose manages:

- API Gateway (Django + Daphne)
- Auth Service (Django + Celery)
- Blog Service (Django + MongoDB)
- Redis (Cache + Session + Celery broker)
- PostgreSQL (User data)
- MongoDB (Blog content)
- Celery Worker (Async tasks)

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| Backend | Django 4+ |
| GraphQL | Graphene-Django |
| Authentication | PyJWT |
| User Database | PostgreSQL 15 |
| Content Storage | MongoDB 6 |
| Token/Session Store | Redis 7 |
| Async Tasks | Celery 5+ |
| WebSockets | Django Channels + Daphne |
| Containerization | Docker + Docker Compose |
| ASGI Server | Daphne |
| WSGI Server | Gunicorn |
| Email | SMTP (Configured) |

---

## 📁 Project Structure

```text
microservices-graphql/
│
├── api_gateway/                    # API Gateway Service
│   ├── apps/                       # App routing
│   ├── middleware/                 # JWT middleware
│   └── settings.py
│
├── auth_service/                   # Authentication Service
│   ├── users/                      # User models, views, utils
│   ├── gql_schema/                 # GraphQL schema
│   │   ├── mutations.py
│   │   ├── queries.py
│   │   ├── types.py
│   │   └── schema.py
│   ├── templates/                  # Email templates
│   │   └── users/
│   └── settings.py
│
├── blog_service/                   # Blog/Content Service
│   ├── blogs/                      # Blog models, GraphQL
│   ├── gql_schema/                 # GraphQL schema
│   └── settings.py
│
├── middleware/                     # Shared middleware
├── tests/                          # Integration tests
├── docker-compose.yml
├── postman_collection.json
└── README.md
```

---

## 🚀 Local Development Setup

### Prerequisites

- Docker & Docker Compose v2+
- Python 3.11+
- Git

---

### Clone Repository

```bash
git clone https://github.com/PritpalSingh786/graphql-microservices-platform.git
cd graphql-microservices-platform
```

---

### Environment Variables

Create `.env` file in root:

```env
# Auth Service
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ISSUER=my-app
JWT_AUDIENCE=my-users
ACCESS_TOKEN_LIFETIME=15  # minutes
REFRESH_TOKEN_LIFETIME=7  # days

# Database
DB_NAME=auth_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres_auth
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# MongoDB
MONGO_HOST=mongo_blog
MONGO_PORT=27017
MONGO_DB_NAME=blog_db

# Email (for development)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourapp.com

# Domain
DOMAIN_URL=http://localhost:8000

# pgAdmin
PGADMIN_EMAIL=admin@admin.com
PGADMIN_PASSWORD=admin
PGADMIN_PORT=5050
```

---

### Start Services

```bash
# Build and start all services
docker compose up -d --build

# Wait for services to initialize (30 seconds)
sleep 30

# Run migrations
docker compose exec auth_service python manage.py migrate

# Create superuser (optional)
docker compose exec auth_service python manage.py createsuperuser
```

---

### Verify Services

```bash
# Check all containers are running
docker compose ps

# Check logs
docker compose logs -f

# Test GraphQL endpoint
curl -X POST http://localhost:8000/graphql/auth/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
```

---

### Access Services

| Service | URL |
|---|---|
| API Gateway | `http://localhost:8000` |
| GraphQL Auth | `http://localhost:8000/graphql/auth/` |
| GraphQL Blog | `http://localhost:8000/graphql/blog/` |
| pgAdmin | `http://localhost:5050` |
| Redis Commander | `http://localhost:8081` (if configured) |

---

## 🔧 Useful Docker Commands

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Stop and remove volumes (reset data)
docker compose down -v

# View logs for specific service
docker compose logs auth_service -f
docker compose logs blog_service -f
docker compose logs api_gateway -f

# Run Django management commands
docker compose exec auth_service python manage.py shell
docker compose exec auth_service python manage.py dbshell

# Execute tests
docker compose exec auth_service python manage.py test users.tests --verbosity=2

# Rebuild specific service
docker compose build auth_service
docker compose up -d auth_service

# Check database
docker compose exec postgres_auth psql -U postgres -d auth_db -c "\dt"
docker compose exec mongo_blog mongosh --eval "db.getCollectionNames()"
```

---

## 🧪 Testing

### Run Unit Tests

```bash
# Auth service tests
docker compose exec auth_service python manage.py test users.tests --verbosity=2

# Blog service tests
docker compose exec blog_service python manage.py test blogs.tests --keepdb --verbosity=2

# API Gateway tests
docker compose exec api_gateway python manage.py test --verbosity=2
```

### Run Integration Tests

```bash
# Make sure services are running
docker compose up -d

# Run integration tests
python3 tests/test_integration.py
```

### Postman Collection

Import `postman_collection.json` into Postman to test all endpoints.

---

## 📊 Current Development Status

| Component | Status |
|---|---|
| Auth Service | ✅ Working |
| Blog Service | ✅ Working |
| API Gateway | ✅ Working |
| Redis Integration | ✅ Working |
| WebSocket Support | ✅ Working |
| File Upload | ✅ Working |
| Docker Setup | ✅ Working |
| Email Verification | ✅ Working |
| Password Reset | ✅ Working |
| Refresh Token Rotation | ✅ Working |
| Device Tracking | ✅ Working |
| Celery Tasks | ✅ Working |
| Unit Tests | ✅ Passing |
| Integration Tests | ✅ Passing |

---

## 🔮 Future Improvements

- [ ] CI/CD Pipeline (GitHub Actions)
- [ ] OAuth2 Integration (Google, GitHub)
- [ ] GraphQL Subscriptions for real-time
- [ ] Prometheus + Grafana Monitoring
- [ ] Kubernetes Deployment
- [ ] Role-Based Access Control (RBAC)
- [ ] API Rate Limiting per user
- [ ] Audit Logging
- [ ] Swagger/OpenAPI Documentation
- [ ] Helm Charts for Kubernetes
- [ ] Service Mesh Integration (Istio)

---

## 🧠 What This Project Demonstrates

- GraphQL-based microservices architecture
- JWT authentication with refresh token rotation
- Redis-backed token/session management
- WebSocket real-time notifications
- Docker-based service orchestration
- PostgreSQL & MongoDB dual database setup
- Celery async task processing
- Device/session management workflows
- Email verification and password reset flows
- Template-based email handling
- Secure password change workflows
- Multi-device session tracking

---

## ⚠️ Security Notes for Production

Before deploying to production, ensure:

1. **Change all secrets** — Use strong, unique keys
2. **Enable HTTPS** — Use SSL/TLS certificates
3. **Set `DEBUG=False`** in all settings files
4. **Use secure cookies** — Set `secure=True`, `httponly=True`
5. **Restrict `ALLOWED_HOSTS`** — Add your domain only
6. **Use strong database passwords**
7. **Enable rate limiting** on auth endpoints
8. **Use environment-specific `.env` files**
9. **Set up proper logging and monitoring**
10. **Regular security updates** for dependencies

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📝 License

This project is open-source and available under the MIT License.

---

## 👨‍💻 Author

**Pritpal Singh**

- 🔗 [GitHub Profile](https://github.com/PritpalSingh786)
- 🔗 [Project Repository](https://github.com/PritpalSingh786/graphql-microservices-platform)
- 🔗 [Demo Video Link](https://youtu.be/9GweB-SjDbM)

---


## 🙏 Acknowledgments

- Django & Graphene communities
- Docker for containerization
- Redis for excellent caching and session management
- MongoDB for flexible document storage
- PostgreSQL for reliable relational data

---

## ⭐ Show Your Support

If you found this project helpful, please give it a ⭐ on GitHub!
