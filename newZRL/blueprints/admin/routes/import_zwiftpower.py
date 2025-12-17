# newZRL/blueprints/admin/import_zwiftpower.py
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required
from newZRL.scripts.zwiftpower_importer import scrape_team, import_members_to_db

from ..bp import admin_bp

@admin_bp.route("/import_zwiftpower/", methods=["GET", "POST"])
@login_required
def import_zwift_team():
    """Importa tutti i rider del team INOX da ZwiftPower."""
    if request.method == "POST":
        try:
            flash("⏳ Importazione in corso del team INOX...", "info")

            # scraping
            members = scrape_team()

            if not members:
                flash("❌ Nessun corridore trovato o errore durante lo scraping.", "danger")
                return redirect(url_for("admin_bp.import_zwift_team"))

            # importa nel DB
            results = import_members_to_db(members)
            flash(
                f"✅ Importazione completata: {results['new']} nuovi, "
                f"{results['updated']} aggiornati, {results.get('deactivated', 0)} disattivati.",
                "success"
            )

        except Exception as e:
            flash(f"❌ Errore durante l'importazione: {e}", "danger")

        return redirect(url_for("admin_bp.import_zwift_team"))

    # GET: mostra la pagina
    return render_template("admin/import_zwiftpower.html")
