# Project Overview

This project is a Flask-based web application named "ZRL Manager". It appears to be a management tool for a Zwift Racing League (ZRL), a virtual cycling competition. The application is designed to handle user authentication, team management, race results, and various administrative tasks related to the league.

## Key Technologies

*   **Backend:** Python with Flask
*   **Database:** MySQL (using Flask-SQLAlchemy)
*   **Authentication:** Flask-Login
*   **Structure:** Modular with Flask Blueprints
*   **Frontend:** HTML templates (likely with a CSS framework, but not explicitly specified)

## Architecture

The application follows a standard Flask project structure:

*   `newZRL/`: The main application package.
    *   `__init__.py`: The application factory (`create_app`) where the Flask app is initialized, extensions are registered, and blueprints are mounted.
    *   `config.py`: Contains the application's configuration, including the database URI and secret key.
    *   `models/`: Defines the SQLAlchemy database models, such as `User`, `Team`, `Race`, etc.
    *   `blueprints/`: Contains the application's blueprints, which modularize the application into logical components (e.g., `auth`, `main`, `admin`).
    *   `templates/`: Holds the HTML templates for rendering the frontend.
    *   `static/`: Stores static assets like CSS, JavaScript, and images.
*   `run.py`: The main entry point for running the Flask development server.

# Building and Running

To run the application in a development environment:

1.  **Install dependencies:** While a `requirements.txt` file is not explicitly visible, the project uses `Flask`, `Flask-SQLAlchemy`, `Flask-Login`, and `pymysql`. These can be installed using pip:
    ```bash
    pip install Flask Flask-SQLAlchemy Flask-Login pymysql
    ```
2.  **Set up the database:** The application is configured to connect to a MySQL database named `zrl` on `localhost` with the credentials `RB:Ro12ba-12`. You will need to have a MySQL server running and create the `zrl` database.
3.  **Run the application:**
    ```bash
    python run.py
    ```
    This will start the Flask development server, and the application will be accessible at `http://127.0.0.1:5000/`. The application will automatically open a web browser to this address.

# Development Conventions

*   **Modular Structure:** The use of Flask Blueprints is a key convention, separating concerns into different modules.
*   **Database Migrations:** The presence of an `alembic.ini` file and a `migrations` directory suggests that Alembic is used for database schema migrations.
*   **Models:** Database models are defined in the `newZRL/models/` directory, with each model in its own file.
*   **Authentication:** User authentication is handled by Flask-Login, with user roles (`admin`, `captain`, `user`) controlling access to different parts of the application.
