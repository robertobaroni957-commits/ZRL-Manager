from flask_login import UserMixin 
from newZRL import db

class User(db.Model, UserMixin):
    __tablename__ = "users"

    profile_id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user")

    # ⚡ Cambiato da team_id → team_trc
    team_trc = db.Column(db.Integer, db.ForeignKey("teams.trc"), nullable=True)

    # Relazione aggiornata
    team = db.relationship("Team", backref="users", lazy=True, foreign_keys=[team_trc])

    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

    def get_id(self):
        return str(self.profile_id)
