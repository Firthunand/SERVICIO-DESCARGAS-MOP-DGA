"""Punto de entrada: en desarrollo se usa este script; en producción Gunicorn carga app con run_flask:app."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
    