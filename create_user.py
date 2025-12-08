from werkzeug.security import generate_password_hash
from newZRL import create_app
from newZRL.models.user import User, db

app = create_app()
with app.app_context():
    if not User.query.filter_by(email="admin@teaminox.it").first():
        admin = User(
            profile_id=123456,
            email="admin@teaminox.it",
            password=generate_password_hash("password123"),
            role="admin",
            active=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin creato")
    else:
        print("⚠️ Admin già esistente")
