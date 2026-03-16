"""Factory de la aplicación Flask: crea la app y registra el blueprint de rutas (formulario, API estado, detener)."""
from flask import Flask


def create_app():
    """Crea y devuelve la instancia Flask con el blueprint main registrado."""
    app = Flask(__name__)

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app