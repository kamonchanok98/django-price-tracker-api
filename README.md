# Django REST Framework Backend API

A RESTful backend service built with **Django** and **Django REST Framework (DRF)** handling user authentication, accounts management, and API integrations.

---

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Framework:** Django 5.x, Django REST Framework (DRF)
- **Authentication & CORS:** `django-cors-headers`
- **Database:** SQLite (Development) / PostgreSQL (Production ready)
- **Testing:** Django `APITestCase` & Modular Test Suites

---

## 📁 Repository Structure

```text
backend/
├── manage.py
├── myproject/                  # Project configuration directory
│   ├── __init__.py
│   ├── settings.py            # Settings (CORS, Installed Apps, DRF config)
│   ├── urls.py                # Main URL routing
│   └── wsgi.py
└── accounts/                  # User & Auth App
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── serializers.py         # DRF Serializers (RegisterSerializer)
    ├── views.py               # Generics APIViews (RegisterView)
    ├── urls.py                # App routing (/register/)
    └── tests/                 # Modular Test Suite
        ├── __init__.py
        ├── test_register_api.py
        └── test_login_api.py

```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+ installed
- `pip` package manager

### 2. Install Dependencies

Clone the repository and create a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows (Command Prompt)
venv\Scripts\activate.bat

# Activate on Windows (PowerShell)
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```bash
pip install django djangorestframework django-cors-headers
```

### 3. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Start Development Server

```bash
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/`.

---

## 🧪 Modular Testing Guide

The test suite is structured into dedicated files within the `accounts/tests/` module directory.

### Running Test Commands

- **Run all app tests:**

  ```bash
  python manage.py test accounts
  ```

- **Run a single test file:**

  ```bash
  python manage.py test accounts.tests.test_register_api
  ```

- **Run a specific test class:**

  ```bash
  python manage.py test accounts.tests.test_register_api.RegisterAPITests
  ```

- **Run a single test method:**
  ```bash
  python manage.py test accounts.tests.test_register_api.RegisterAPITests.test_successful_registration
  ```

### Useful CLI Test Flags

| Flag         | Description                                                               |
| :----------- | :------------------------------------------------------------------------ |
| `--keepdb`   | Preserves the test database between test runs to increase execution speed |
| `--failfast` | Halts execution immediately upon encountering the first failed test       |
| `-v 2`       | Enables verbose output listing individual test names and outcomes         |

**Recommended Fast Development Test Command:**

```bash
python manage.py test accounts --keepdb --failfast
```
