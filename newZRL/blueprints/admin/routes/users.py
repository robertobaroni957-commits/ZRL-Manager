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
from newZRL.forms import UserForm # Import UserForm
from wtforms.validators import DataRequired, Length # Import DataRequired and Length

import logging
logger = logging.getLogger(__name__)

# --- Helper function for user forms ---
def process_user_form(form, user=None):
    """Processes user form data for creation or editing using a UserForm instance."""
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        profile_id = int(form.profile_id.data)
        role = form.role.data
        active = form.active.data

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
    else:
        # Flash form errors if validation fails
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Errore nel campo '{getattr(form, field).label.text}': {error}", "danger")
        return False


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
    form = UserForm()
    # Password is required for new users, so override Optional validator
    form.password.validators = [DataRequired(), Length(min=6)]
    if form.validate_on_submit():
        if process_user_form(form):
            return redirect(url_for("admin_bp.list_users"))
    return render_template("admin/new_user.html", form=form)

# --- Edit User ---
@admin_bp.route("/users/<int:profile_id>/edit", methods=["GET", "POST"])
@require_roles(["admin"])
@login_required
def edit_user(profile_id):
    user = User.query.get_or_404(profile_id)
    form = UserForm(obj=user) # Populate form with user data

    # Password is optional during edit
    form.password.validators = [Optional(), Length(min=6)]

    # Fetch associated WTRL_Rider and their availability
    rider = WTRL_Rider.query.filter_by(profile_id=user.profile_id).first()
    rider_availability = None
    if rider:
        rider_availability = RiderAvailability.query.filter_by(wtrl_rider_id=rider.id).first()

    if form.validate_on_submit():
        if process_user_form(form, user):
            return redirect(url_for("admin_bp.list_users"))
    elif request.method == 'GET':
        # Populate form fields from user object for GET requests
        form.email.data = user.email
        form.profile_id.data = str(user.profile_id) # Convert int to string for form field
        form.role.data = user.role
        form.active.data = user.active

    return render_template("admin/edit_user.html", form=form, user=user, rider=rider, rider_availability=rider_availability)

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
