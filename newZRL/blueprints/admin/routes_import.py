from flask import Blueprint, redirect, url_for, flash, render_template
from flask_login import login_required
from newZRL.scripts.wtrl_local_import import run_import

bp_import = Blueprint("admin_import", __name__, url_prefix="/admin/imports")


@bp_import.route("/wtrl_local", methods=["GET"])
@login_required
def import_wtrl_local():
    """
    Avvia importazione WTRL da JSON locali
    """
    try:
        run_import()
        flash("Importazione completata con successo!", "success")
    except Exception as e:
        flash(f"Errore durante l'importazione: {e}", "danger")

    return redirect(url_for("admin_import.import_page"))


@bp_import.route("/", methods=["GET"])
@login_required
def import_page():
    """
    Pagina con i pulsanti di import
    """
    return render_template("admin/imports.html")

