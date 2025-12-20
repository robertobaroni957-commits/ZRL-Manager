# newZRL/blueprints/admin/routes/import_status.py

from flask import jsonify, render_template
from ..bp import admin_bp

# This dictionary will hold the progress of long-running tasks.
# In a production environment, this should be replaced with a more robust solution
# like Redis or a database-backed task queue (e.g., Celery).
import_status_data = {
    'progress': 0,
    'message': 'Nessuna importazione in corso.',
    'is_running': False
}

@admin_bp.route("/wtrl_import/status")
def get_import_status():
    """Returns the current status of the import task."""
    return jsonify(import_status_data)

@admin_bp.route("/wtrl_import/progress")
def import_progress():
    """Displays the import progress page."""
    return render_template("admin/import_progress.html")

