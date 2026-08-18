# Product Price Tracker REST API & Background Worker

A RESTful backend service built with **Django**, **Django REST Framework (DRF)**, **Celery**, and **Redis** for managing product tracking, user accounts, and automated price scraping.

---

## 🛠️ Tech Stack

- **Language:** Python 3.12+
- **Framework:** Django 6.x, Django REST Framework (DRF)
- **Database:** PostgreSQL 15 (Docker) / SQLite fallback (Local dev)
- **Task Queue & Automation:** Celery 5.x, Redis 8.x, `django-celery-beat`
- **Web Scraping:** `beautifulsoup4`, `lxml`, `requests`
- **Containerization:** Docker & Docker Compose
- **Testing & Coverage:** Django `TestCase`, `unittest.mock`, `coverage`

---

## 📁 Repository Structure

```text
.
├── core/                       # Project configuration directory (settings, celery, urls)
│   ├── __init__.py
│   ├── celery.py               # Celery app instance configuration
│   ├── settings.py             # Settings (Database, Celery, DRF, CORS)
│   └── urls.py
├── tracker/                    # Price Tracking & Scraping App
│   ├── models.py               # Product models
│   ├── tasks.py                # Celery background & periodic tasks
│   ├── views.py
│   └── tests/                  # App test suite
│       ├── __init__.py
│       └── test_task.py        # Celery task unit tests
├── accounts/                   # User & Authentication App
│   ├── models.py
│   ├── serializers.py
│   └── views.py
├── Dockerfile                  # Container definition for Django & Celery
├── docker-compose.yml          # Multi-container orchestration (DB, Redis, Web, Worker, Beat)
├── requirements.txt            # Main project dependencies
├── .env                        # Environment variable configuration
├── .coveragerc                 # Test coverage configuration
└── manage.py
```

---

## ⚙️ Environment Configuration

Create a .env file in the root directory before launching the services:

ข้อมูลโค้ด

```.env
# Database Settings
DB_NAME=price_tracker_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_PORT=5432

# Redis & Celery
REDIS_URL="redis://redis:6379/0"

# Django
DJANGO_DEBUG=True
SECRET_KEY="your-secret-key-here"
```

---

## 🚀 Quick Start (Docker Compose)

The entire stack (PostgreSQL, Redis, Django, Celery Worker, and Celery Beat) runs as a unified set of services using Docker Compose.

1. Build and Launch All Services

```Bash
docker compose up -d --build
```

This starts 5 background containers:

- postgres_db (PostgreSQL database on port 5432)
- price_tracker_redis (Redis message broker on port 6379)
- price_tracker_web (Django development server on http://localhost:8000)
- price_tracker_worker (Celery background worker process)
- price_tracker_beat (Celery Beat periodic scheduler)

2. Apply Database Migrations
   Run database migrations inside the running Django web container:

```Bash
docker compose exec web python manage.py migrate
```

3. Create Superuser (Admin Access)
   Create an administrative account to access the Django Admin panel:

```Bash
docker compose exec web python manage.py createsuperuser
```

## Access the Django Admin dashboard at http://localhost:8000/admin/.

## 🧪 Testing & Code Coverage

Tests run inside the container with task eager execution (CELERY_TASK_ALWAYS_EAGER=True) to execute Celery tasks synchronously in-memory.

Run All Unit Tests

```Bash
docker compose exec web python manage.py test
```

Run Tests with Coverage Report

```Bash
# Execute test suite and collect coverage
docker compose exec web coverage run --source='.' manage.py test

# View command-line report
docker compose exec web coverage report

# Generate HTML report (saved to htmlcov/index.html)
docker compose exec web coverage html
```

# Useful Project Commands Cheat Sheet

Quick reference for managing Docker Compose, Django, Celery, PostgreSQL, and testing suite.

---

## 🐳 Docker Compose Management

| Command                                | Description                                                           |
| :------------------------------------- | :-------------------------------------------------------------------- |
| `docker compose up -d`                 | Start all services in background (detached mode)                      |
| `docker compose up -d --build`         | Rebuild images and start all services                                 |
| `docker compose down`                  | Stop and remove all containers                                        |
| `docker compose down -v`               | Stop containers and remove persistent volumes (deletes database data) |
| `docker compose ps`                    | List status of all running containers                                 |
| `docker compose logs -f`               | Stream logs for all services                                          |
| `docker compose logs -f web`           | Stream logs for Django web service only                               |
| `docker compose logs -f celery_worker` | Stream logs for Celery worker only                                    |
| `docker compose restart web`           | Restart specific service (e.g., `web`, `celery_worker`, `redis`)      |

---

## 🐍 Django Operations

| Command                                                    | Description                                          |
| :--------------------------------------------------------- | :--------------------------------------------------- |
| `docker compose exec web python manage.py makemigrations`  | Generate new database migration files                |
| `docker compose exec web python manage.py migrate`         | Apply database migrations to PostgreSQL              |
| `docker compose exec web python manage.py createsuperuser` | Create an admin account interactively                |
| `docker compose exec web python manage.py shell`           | Open interactive Django Python shell                 |
| `docker compose exec web python manage.py showmigrations`  | Check migration status across apps                   |
| `docker compose exec web python manage.py collectstatic`   | Gather static files (for production)                 |
| `docker compose exec web bash`                             | Open interactive terminal shell inside web container |

---

## ⚙️ Celery & Redis Debugging

| Command                                                              | Description                                       |
| :------------------------------------------------------------------- | :------------------------------------------------ |
| `docker compose exec redis redis-cli ping`                           | Check if Redis broker is running (expects `PONG`) |
| `docker compose exec redis redis-cli monitor`                        | Stream live commands received by Redis            |
| `docker compose exec celery_worker celery -A core status`            | Check status of active Celery workers             |
| `docker compose exec celery_worker celery -A core inspect active`    | List tasks currently executing                    |
| `docker compose exec celery_worker celery -A core inspect scheduled` | List tasks scheduled for future execution         |
| `docker compose exec celery_worker celery -A core purge`             | Clear all pending tasks from Redis queue          |

---

## 🐘 PostgreSQL Commands

| Command                                                                    | Description                        |
| :------------------------------------------------------------------------- | :--------------------------------- |
| `docker compose exec db psql -U postgres -d price_tracker_db`              | Open PostgreSQL interactive shell  |
| `docker compose exec db pg_dump -U postgres price_tracker_db > backup.sql` | Export full database backup        |
| `docker compose exec -T db psql -U postgres price_tracker_db < backup.sql` | Restore database from `backup.sql` |

---

## 🧪 Testing & Coverage

| Command                                                                 | Description                                            |
| :---------------------------------------------------------------------- | :----------------------------------------------------- |
| `docker compose exec web python manage.py test`                         | Run entire test suite                                  |
| `docker compose exec web python manage.py test tracker`                 | Run tests for `tracker` app only                       |
| `docker compose exec web python manage.py test tracker.tests.test_task` | Run a specific test file                               |
| `docker compose exec web coverage run --source='.' manage.py test`      | Run tests while tracking coverage                      |
| `docker compose exec web coverage report`                               | Display coverage percentage summary in terminal        |
| `docker compose exec web coverage html`                                 | Generate interactive HTML coverage report (`htmlcov/`) |

---

## 🧹 Cleanup & Maintenance

| Command                  | Description                                           |
| :----------------------- | :---------------------------------------------------- |
| `docker system prune -f` | Remove unused Docker containers, networks, and images |
| `docker volume prune -f` | Remove all unused Docker volumes                      |
