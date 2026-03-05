from flask import Blueprint, render_template, request,  redirect, url_for
from core.config import load_codes, load_config
import threading
from core.mop_client import run_download_job


JOB_STATE = {
    "status": "idle",        # idle | en_curso | finalizado
    "lista": None,
    "start_date": None,
    "end_date": None,
    "total_pozos": 0,
    "procesados": 0,
    "detalles": [],          # luego será una lista de dicts por pozo
}

def on_job_status(event: dict):
    """Callback llamado desde run_download_job (versión mínima)."""
    if event.get("type") == "job_finished":
        JOB_STATE["status"] = "finalizado"

bp = Blueprint("main", __name__)

'''
@bp.route("/", methods=["GET", "POST"])
def index():
    # Más adelante aquí leeremos lista + fechas y llamaremos a run_download_job
    selected_list = None
    start_date = None
    end_date = None

    if request.method == "POST":
        selected_list = request.form.get("lista")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        
        # TODO: disparar job en una fase posterior

    return render_template(
        "index.html",
        selected_list=selected_list,
        start_date=start_date,
        end_date=end_date,
    )
    '''
    
@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if JOB_STATE["status"] == "en_curso":
            # Ya hay un job corriendo; no lanzamos otro
            return render_template("index.html", job_state=JOB_STATE)
        
        selected_list = request.form.get("lista")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
                # Elegir archivo de lista según la selección
        lista_to_path = {
            "P5": "data/pozosADescargarP5.txt",
            "P12": "data/pozosADescargarP12.txt",
            "P17": "data/pozosADescargarP17.txt",
            "P22": "data/pozosADescargarP22.txt"
        }

        path_lista = lista_to_path.get(selected_list)
        if not path_lista:
            # Caso defensivo: lista sin archivo asociado
            JOB_STATE["status"] = "idle"
            JOB_STATE["detalles"] = []
            return render_template("index.html", job_state=JOB_STATE)

        codes = load_codes(path_lista)

        # Por ahora: simulamos un job en memoria sin Selenium
        JOB_STATE["status"] = "en_curso"
        JOB_STATE["lista"] = selected_list
        JOB_STATE["start_date"] = start_date
        JOB_STATE["end_date"] = end_date

        JOB_STATE["detalles"] = [
            {"codigo": code, "estado": "Pendiente", "mensaje": ""}
            for code in codes
        ]
        JOB_STATE["total_pozos"] = len(JOB_STATE["detalles"])
        JOB_STATE["procesados"] = 0
        
        cfg = load_config("data/config.json")

        # Lanzamos el job en un hilo en background
        t = threading.Thread(
            target=run_download_job,
            args=(cfg, codes, selected_list, on_job_status),
            daemon=True,
        )
        t.start()
        return redirect(url_for("main.index"))
    return render_template(
        "index.html",
        job_state=JOB_STATE,
    )