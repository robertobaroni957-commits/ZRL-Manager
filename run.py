# run.py
import os
from waitress import serve
from newZRL import create_app, db
from newZRL.models.user import User
from werkzeug.security import generate_password_hash
import click
from dotenv import load_dotenv

load_dotenv()

# Crea l'app
app = create_app(os.environ.get("FLASK_ENV", "production")) 

@app.cli.command("create_user")
@click.option("--email", required=True, help="Email for the new user.")
@click.option("--password", required=True, help="Password for the new user.")
@click.option("--profile_id", required=True, help="Zwift Profile ID for the new user.")
@click.option("--role", default="user", help="Role for the new user (e.g., admin, captain).")
def create_user_command(email, password, profile_id, role):
    """Creates a new user in the database."""
    if User.query.filter_by(email=email).first():
        print(f"⚠️ User with email '{email}' already exists.")
        return

    hashed_pw = generate_password_hash(password)
    new_user = User(
        email=email,
        password=hashed_pw,
        profile_id=profile_id,
        role=role,
        active=True
    )
    db.session.add(new_user)
    db.session.commit()
    print(f"✅ User '{email}' created with role '{role}' and Profile ID '{profile_id}'")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    if os.environ.get("FLASK_DEBUG") == "1":
        # Dev server
        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        # Production server con Waitress
        serve(app, host="0.0.0.0", port=port)
