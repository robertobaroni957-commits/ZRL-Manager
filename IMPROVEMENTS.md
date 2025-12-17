# Project Improvement Suggestions

Here are some detailed suggestions for improving the ZRL Manager project.

## 1. Code Structure and Organization

### Refactor Large Blueprints

Some blueprints, like the `admin` blueprint, are quite large and could be refactored for better organization. Instead of having a single `routes.py` file with many routes, you can split them into multiple files based on their functionality.

**Example: Refactoring the `admin` blueprint**

Instead of having all admin routes in `newZRL/blueprints/admin/bp.py`, you can create a `routes` directory within the `admin` blueprint and split the routes into multiple files:

```
newZRL/blueprints/admin/
├── __init__.py
├── bp.py
└── routes/
    ├── __init__.py
    ├── dashboard.py
    ├── reports.py
    └── users.py
```

Then, in `newZRL/blueprints/admin/bp.py`, you can import and register these routes:

```python
# newZRL/blueprints/admin/bp.py
from flask import Blueprint

admin_bp = Blueprint("admin_bp", __name__)

from .routes import dashboard, reports, users
```

### Organize Scripts

The root directory contains several script-like files (`avatar.py`, `create_user.py`, `zwift_scraper.py`). It's a good practice to move these into a dedicated `scripts` directory.

```
scripts/
├── __init__.py
├── create_user.py
├── zwift_scraper.py
└── ...
```

## 2. Configuration and Secrets Management

### Use Environment Variables for All Secrets

The `newZRL/config.py` file has a hardcoded database URI as a fallback. In a production environment, you should always load sensitive information from environment variables and fail loudly if they are not set.

You can use a library like `python-dotenv` to manage environment variables in your local development environment.

**Example: Improved `newZRL/config.py`**

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("No DATABASE_URL set for Flask application")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

### Create Separate Configurations for Different Environments

You can create different configuration classes for development, testing, and production environments.

**Example: `newZRL/config.py` with multiple configurations**

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DEV_DATABASE_URL")

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL")

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("PROD_DATABASE_URL")

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
```

Then, in your `newZRL/__init__.py`, you can select the appropriate configuration based on an environment variable:

```python
# newZRL/__init__.py
from newZRL.config import config_by_name

def create_app():
    app = Flask(__name__)
    config_name = os.getenv("FLASK_CONFIG", "development")
    app.config.from_object(config_by_name[config_name])
    # ...
```

## 3. Error Handling and Logging

### Set Up Centralized Logging

Configure a centralized logger to record application events, errors, and other useful information.

**Example: `newZRL/config.py` with logging configuration**

```python
import logging

class Config:
    # ...
    LOGGING_LEVEL = logging.INFO
```

**Example: `newZRL/__init__.py` with logger initialization**

```python
# newZRL/__init__.py
import logging

def create_app():
    app = Flask(__name__)
    # ...
    logging.basicConfig(level=app.config["LOGGING_LEVEL"])
    # ...
```

### Create Custom Error Pages

Create custom error pages for common HTTP errors like 404 (Not Found) and 500 (Internal Server Error).

**Example: `newZRL/blueprints/main/routes.py` with error handlers**

```python
# newZRL/blueprints/main/routes.py
from flask import render_template
from . import main_bp

@main_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@main_bp.app_errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500
```

You will also need to create the corresponding `404.html` and `500.html` templates.

## 4. Testing

### Structure the Test Suite

Create a dedicated `tests` directory in the root of your project to store all your tests.

```
tests/
├── __init__.py
├── conftest.py
├── test_auth.py
└── test_main.py
```

### Write More Comprehensive Tests

Write unit tests for your models, utility functions, and blueprint routes. Use a test runner like `pytest` to run your tests.

**Example: `tests/test_auth.py`**

```python
import pytest
from newZRL import create_app, db
from newZRL.models.user import User

@pytest.fixture
def client():
    app = create_app("testing")
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_login(client):
    # Create a test user
    user = User(email="test@example.com", password="password")
    db.session.add(user)
    db.session.commit()

    # Test the login route
    response = client.post("/login", data={"email": "test@example.com", "password": "password"})
    assert response.status_code == 302 # Redirect on successful login
```

## 5. Frontend

### Use a Modern CSS Framework

Consider using a modern CSS framework like Bootstrap or Tailwind CSS to create a more polished and responsive user interface. You can integrate these frameworks into your base template.

### Manage Frontend Assets with a Build Tool

Use a frontend build tool like Webpack or Parcel to manage and optimize your CSS and JavaScript assets. This will allow you to bundle and minify your assets, which can improve the performance of your application.

## 6. Database

### Optimize the Database Schema

Review your database schema and add indexes to frequently queried columns. This can significantly improve the performance of your database queries.

**Example: Adding an index to the `User` model**

```python
# newZRL/models/user.py
from newZRL import db

class User(db.Model):
    __tablename__ = "users"
    # ...
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    # ...
```

### Improve Database-Related Code

The `onupdate=datetime.utcnow` in the `Team` model might not work as expected with all database backends. A database-level default value or a trigger would be more reliable. Alternatively, you can use SQLAlchemy's event listeners to update the `updated_at` field.

**Example: Using SQLAlchemy event listeners**

```python
# newZRL/models/team.py
from datetime import datetime
from newZRL import db
from sqlalchemy import event

class Team(db.Model):
    # ...
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

@event.listens_for(Team, "before_update")
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()
```

## 7. API

### Document the API

If you plan to expose a public API, it's a good practice to document it. You can use a tool like Swagger or OpenAPI to generate interactive API documentation. Libraries like `flasgger` can help you with this.
