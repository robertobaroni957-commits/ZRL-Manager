from flask_login import UserMixin 
from newZRL import db
from newZRL.models.team import Team # Import Team model

class User(db.Model, UserMixin):
    __tablename__ = "users"

    profile_id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user")

    # Relazione per identificare la squadra di cui l'utente è capitano
    captain_of_team = db.relationship(
        "Team",
        primaryjoin="User.profile_id == foreign(Team.captain_profile_id)",
        backref=db.backref("captain_user", uselist=False),
        uselist=False, # Un capitano è associato a una sola squadra (come capitano)
        lazy=True
    )

    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

    def get_id(self):
        return str(self.profile_id)
