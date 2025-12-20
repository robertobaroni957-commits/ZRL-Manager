from flask import Blueprint

rider_bp = Blueprint("rider", __name__, url_prefix="/rider")

from . import routes