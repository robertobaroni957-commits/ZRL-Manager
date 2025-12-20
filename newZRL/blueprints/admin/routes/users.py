# newZRL/blueprints/admin/routes/users.py

from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from newZRL import db
from newZRL.models.user import User
from newZRL.models.wtrl_rider import WTRL_Rider
from newZRL.models import RiderAvailability # Import RiderAvailability # Might be needed for profile_id checks
from werkzeug.security import generate_password_hash
from ..bp import admin_bp
from utils.auth_decorators import require_roles

import logging
logger = logging.getLogger(__name__)

# --- Helper function for user forms ---
def process_user_form(user=None):
    """Processes user form data for creation or editing."""
    email = request.form.get("email").strip()
    password = request.form.get("password").strip()
    profile_id_str = request.form.get("profile_id").strip()
    role = request.form.get("role").strip()
    active = True if request.form.get("active") == "on" else False

    # Validation
    if not email:
        flash("L'email è obbligatoria.", "danger")
        return False
    if not role:
        flash("Il ruolo è obbligatorio.", "danger")
        return False
    if not profile_id_str.isdigit():
        flash("L'ID profilo deve essere un numero valido.", "danger")
        return False
    profile_id = int(profile_id_str)

    # Check for existing email (only if creating or changing email)
    if not user or (user and user.email != email):
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash(f"Un utente con l'email '{email}' esiste già.", "danger")
            return False

    # Check for existing profile_id (only if creating or changing profile_id)
    if not user or (user and user.profile_id != profile_id):
        existing_profile = User.query.filter_by(profile_id=profile_id).first()
        if existing_profile:
            flash(f"Un utente con l'ID profilo '{profile_id}' esiste già.", "danger")
            return False

    if user: # Editing existing user
        user.email = email
        user.profile_id = profile_id
        user.role = role
        user.active = active
        if password: # Only update password if provided
            user.password = generate_password_hash(password)
        flash(f"Utente '{user.email}' aggiornato con successo.", "success")
    else: # Creating new user
        if not password:
            flash("La password è obbligatoria per un nuovo utente.", "danger")
            return False
        user = User(
            email=email,
            password=generate_password_hash(password),
            profile_id=profile_id,
            role=role,
            active=active
        )
        db.session.add(user)
        flash(f"Utente '{user.email}' creato con successo.", "success")
    
    db.session.commit()
    return True


# --- List Users ---
@admin_bp.route("/users")
@require_roles(["admin"])
@login_required
def list_users():
    users = User.query.order_by(User.email.asc()).all()
    return render_template("admin/list_users.html", users=users)

# --- Create User ---
@admin_bp.route("/users/new", methods=["GET", "POST"])
@require_roles(["admin"])
@login_required
def new_user():
    if request.method == "POST":
        if process_user_form():
            return redirect(url_for("admin_bp.list_users"))
    return render_template("admin/new_user.html")

# --- Edit User ---
@admin_bp.route("/users/<int:profile_id>/edit", methods=["GET", "POST"])
@require_roles(["admin"])
@login_required
def edit_user(profile_id):
    user = User.query.get_or_404(profile_id)
    
    # Fetch associated WTRL_Rider and their availability
    rider = WTRL_Rider.query.filter_by(profile_id=user.profile_id).first()
    rider_availability = None
    if rider:
        rider_availability = RiderAvailability.query.filter_by(wtrl_rider_id=rider.id).first()

    if request.method == "POST":
        if process_user_form(user):
            return redirect(url_for("admin_bp.list_users"))
    return render_template("admin/edit_user.html", user=user, rider=rider, rider_availability=rider_availability) # Pass availability

# --- Delete User ---
@admin_bp.route("/users/<int:profile_id>/delete", methods=["POST"])
@require_roles(["admin"])
@login_required
def delete_user(profile_id):
    user = User.query.get_or_404(profile_id)
    if user.role == "admin":
        flash("Non puoi eliminare un utente con ruolo 'admin'.", "danger")
    else:
        try:
            db.session.delete(user)
            db.session.commit()
            flash(f"Utente '{user.email}' eliminato con successo.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Errore durante l'eliminazione dell'utente: {str(e)}", "danger")
            logger.error(f"Error deleting user {user.profile_id}: {e}", exc_info=True)
    return redirect(url_for("admin_bp.list_users"))
