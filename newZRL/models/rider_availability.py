from newZRL import db
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON # For storing complex availability data

class RiderAvailability(db.Model):
    __tablename__ = "rider_availability"

    id = db.Column(db.Integer, primary_key=True)
    wtrl_rider_id = db.Column(db.String(100), db.ForeignKey("wtrl_riders.id"), nullable=False, unique=True) # One-to-one with WTRL_Rider

    # Example fields for availability (flexible approach)
    # Could be a JSON string like:
    # {
    #   "Monday": {"start": "18:00", "end": "22:00"},
    #   "Tuesday": {"start": "19:00", "end": "21:00"},
    #   "Wednesday": null, # Not available
    #   "Thursday": {"start": "20:00", "end": "23:00"},
    #   "Friday": null,
    #   "Saturday": {"start": "10:00", "end": "12:00", "type": ["race", "training"]},
    #   "Sunday": null
    # }
    # Or a more structured approach with separate columns per day.
    # For now, a JSON column is most flexible for AI composition.
    availability_data = db.Column(JSON, nullable=True) 
    
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to WTRL_Rider
    rider = db.relationship("WTRL_Rider", back_populates="availability")

    def __repr__(self):
        return f"<RiderAvailability {self.wtrl_rider_id}>"
