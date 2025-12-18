from flask_login import UserMixin 
from newZRL import db
import traceback # Import traceback

class User(db.Model, UserMixin):
    __tablename__ = "users"

    profile_id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user")

    # ⚡ Cambiato da team_id → team_trc
    team_trc = db.Column(db.Integer, db.ForeignKey("teams.trc"), nullable=True)

    # Relazione aggiornata
    team = db.relationship("Team", backref="users", lazy=True, foreign_keys=[team_trc])

    active = db.Column(db.Boolean, default=True)

    # DEBUG: AGGIUNGI QUESTO BLOCCO TEMPORANEAMENTE
    @property
    def query(self):
        print("\n--- DEBUG: Accessing User.query property ---")
        traceback.print_stack(limit=5) # Print the last 5 calls
        print("--- END DEBUG ---\n")
        return super().query
    # FINE BLOCCO DEBUG

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

    def get_id(self):
        return str(self.profile_id)
