from flask import redirect, url_for, flash, render_template
from flask_login import login_required
from newZRL.scripts.wtrl_local_import import run_import

from ..bp import admin_bp


@admin_bp.route("/imports/wtrl_local", methods=["GET"])
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

    return redirect(url_for("admin_bp.imports_main_page")) # Changed here


@admin_bp.route("/imports/", methods=["GET"], endpoint="imports_main_page") # Changed here
@login_required
def import_page():
    """
    Pagina con i pulsanti di import
    """
    return render_template("admin/imports.html")
