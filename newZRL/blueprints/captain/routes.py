# newZRL/blueprints/captain/routes.py
from datetime import date, timedelta
from flask import Blueprint, render_template, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from newZRL import db
from newZRL.models import Race, Round, Season, RiderAvailability, WTRL_Rider, User # Add all necessary models
import json # For parsing availability_data, though it's already a dict if loaded correctly

captain_bp = Blueprint("dashboard_captain", __name__, url_prefix="/captain")

@captain_bp.route("/dashboard")
@login_required # Ensure captain is logged in
def captain_dashboard():
    # Check if current_user has 'captain' role
    if current_user.role != 'captain': # Check the role attribute directly
        flash("Accesso negato. Solo i capitani possono accedere a questa dashboard.", "danger")
        return redirect(url_for('main.index')) # Redirect to a safe page

    today = date.today()
    
    # Find the next Tuesday's date (if today is Tuesday, it should be today)
    # Monday is 0, Tuesday is 1, ..., Sunday is 6
    days_until_next_tuesday = (1 - today.weekday() + 7) % 7
    # If today is Tuesday, and days_until_next_tuesday is 0, next_tuesday_date is today.
    # If today is not Tuesday, days_until_next_tuesday will correctly calculate days until next Tuesday.
    next_tuesday_date = today + timedelta(days=days_until_next_tuesday)

    # Find the next ZRL race on that specific Tuesday
    # Filter by Season.name containing 'ZRL', Race.race_date matching next_tuesday_date
    next_zrl_race = Race.query.join(Round).join(Season).\
        filter(Season.name.ilike('%ZRL%'), Race.race_date == next_tuesday_date).\
        order_by(Race.race_date).first() # In case there are multiple races on the same Tuesday, pick the first one

    if not next_zrl_race:
        flash(f"Nessuna gara ZRL trovata per il prossimo martedì ({next_tuesday_date.strftime('%d/%m/%Y')}).", "info")
        return render_template(
            "captain/dashboard.html",
            title="Dashboard Capitano",
            available_riders=[], # Empty list if no race
            next_race_date=next_tuesday_date,
            next_race=None
        )

    # Fetch riders available for this race date (specifically on Tuesday)
    available_riders_data = []
    
    # Get all WTRL Riders who have submitted availability, eager load User and RiderAvailability
    all_wtrl_riders_with_availability = WTRL_Rider.query.options(
        db.joinedload(WTRL_Rider.user), # Assuming WTRL_Rider has a relationship to User
        db.joinedload(WTRL_Rider.availability)
    ).all()

    for wtrl_rider in all_wtrl_riders_with_availability:
        # Check if rider has availability info and specifically for Tuesday (martedi)
        if wtrl_rider.availability and wtrl_rider.availability.availability_data and 'martedi' in wtrl_rider.availability.availability_data:
            tuesday_slot = wtrl_rider.availability.availability_data['martedi']
            
            # If tuesday_slot is not None (meaning they are available, even if times aren't specified)
            if tuesday_slot is not None:
                user = wtrl_rider.user # Access the eagerly loaded user
                
                # Placeholder for team name - needs proper team relationship
                team_name = "N/A" # Or fetch from user.team or wtrl_rider.team if such relation exists

                available_riders_data.append({
                    'wtrl_rider_id': wtrl_rider.id,
                    'rider_name': f"{user.firstname} {user.lastname}" if user and user.firstname and user.lastname else wtrl_rider.zwift_name,
                    'team_name': team_name, # To be properly implemented
                    'availability_start': tuesday_slot.get('start'),
                    'availability_end': tuesday_slot.get('end'),
                    'notes': wtrl_rider.availability.notes if wtrl_rider.availability.notes else ""
                })
    
    # Sort by rider name for better readability
    available_riders_data.sort(key=lambda x: x['rider_name'].lower())

    return render_template(
        "captain/dashboard.html",
        title="Dashboard Capitano",
        next_race=next_zrl_race,
        next_race_date=next_zrl_race.race_date,
        available_riders=available_riders_data
    )
