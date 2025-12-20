from flask import render_template, request, flash, redirect, url_for, jsonify, session # Import session
from flask_login import login_required, current_user
from newZRL import db
from newZRL.models import WTRL_Rider, RiderAvailability
from utils.auth_decorators import require_roles
from . import rider_bp
from flask_wtf.csrf import generate_csrf # Add this import

import json
import logging # Import logging
logger = logging.getLogger(__name__) # Get logger instance

@rider_bp.route("/availability", methods=["GET", "POST"])
@login_required
@require_roles(["user", "captain"]) # Captains also need to set availability
def set_availability():
    # Debug session on GET request
    if request.method == "GET":
        session['test_value'] = 'Hello Session!' # Set a test value
        logger.debug(f"GET request - Session ID: {session.sid if hasattr(session, 'sid') else 'N/A'}, CSRF token in session: {session.get('_csrf_token')}, Test Value: {session.get('test_value')}")

    # Find the WTRL_Rider associated with the current user's profile_id
    rider = WTRL_Rider.query.filter_by(profile_id=current_user.profile_id).first()

    if not rider:
        flash("❌ Rider non trovato. Assicurati che il tuo Profile ID sia associato a un rider esistente.", "danger")
        return redirect(url_for("main.index")) # Redirect to a safe page

    availability = RiderAvailability.query.filter_by(wtrl_rider_id=rider.id).first()
    
    if request.method == "POST":
        # Debug session on POST request
        logger.debug(f"POST request - Session ID: {session.sid if hasattr(session, 'sid') else 'N/A'}, CSRF token in session: {session.get('_csrf_token')}, Test Value: {session.get('test_value')}")

        data = request.get_json() # Expecting JSON data from frontend

        
        if not data:
            flash("❌ Nessun dato ricevuto. Assicurati di inviare un JSON valido.", "danger")
            # For AJAX requests, return JSON error
            if request.is_json:
                return jsonify({"status": "error", "message": "Nessun dato JSON ricevuto."}), 400
            return redirect(url_for("rider.set_availability"))

        # Basic validation
        if "availability_data" not in data or not isinstance(data["availability_data"], dict):
            flash("❌ Dati di disponibilità non validi.", "danger")
            if request.is_json:
                return jsonify({"status": "error", "message": "Dati di disponibilità JSON non validi."}), 400
            return redirect(url_for("rider.set_availability"))
        
        # Parse notes, default to empty string if not provided or not string
        notes = data.get("notes")
        if not isinstance(notes, str):
            notes = ""
        else:
            notes = notes.strip()

        if availability:
            # Update existing availability
            availability.availability_data = data["availability_data"]
            availability.notes = notes
            flash("✅ Disponibilità aggiornata con successo.", "success")
        else:
            # Create new availability
            availability = RiderAvailability(
                wtrl_rider_id=rider.id,
                availability_data=data["availability_data"],
                notes=notes
            )
            db.session.add(availability)
            flash("✅ Disponibilità salvata con successo.", "success")
        
        try:
            db.session.commit()
            if request.is_json:
                return jsonify({"status": "success", "message": "Disponibilità salvata con successo."}), 200
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Errore durante il salvataggio della disponibilità: {str(e)}", "danger")
            if request.is_json:
                return jsonify({"status": "error", "message": f"Errore DB: {str(e)}"}), 500
        
        return redirect(url_for("rider.set_availability")) # Redirect for non-AJAX POST

    # GET request - prepare data for the form
    # Load current availability data as a dictionary
    current_availability = {}
    current_notes = ""
    if availability and availability.availability_data:
        current_availability = availability.availability_data
        current_notes = availability.notes or ""

    return render_template(
        "rider/availability_form.html",
        rider=rider,
        current_availability=current_availability,
        current_notes=current_notes,
        csrf_token=generate_csrf() # Pass CSRF token to template
    )
