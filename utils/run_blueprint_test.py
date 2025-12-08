from flask import Flask, Blueprint

# Blueprint di test
test_bp = Blueprint("test_bp", __name__, url_prefix="/test")

@test_bp.route("/")
def test_index():
    return "Blueprint funzionante!"

# App principale
app = Flask(__name__)
app.register_blueprint(test_bp)

if __name__ == "__main__":
    app.run(debug=True)
