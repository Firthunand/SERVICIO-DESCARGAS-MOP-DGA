from flask import Blueprint, render_template, request, redirect, url_for, jsonify, make_response
from core.config import load_codes, load_config
from core.downloads import downloads_folder_for_subfolder
import threading
import time
import uuid
from core.mop_client import run_download_job
from datetime import datetime

# Una sola sesión activa: quien tiene la sesión puede usar la app; los demás ven "Sesión en uso"
SESSION_TIMEOUT_SEC = 45
ACTIVE_VIEWER_ID = None
LAST_HEARTBEAT = None


def _update_session_claim(viewer_id: str | None) -> bool:
    """Actualiza heartbeat o asigna sesión si está libre/expirada. Retorna True si viewer_id es el dueño."""
    global ACTIVE_VIEWER_ID, LAST_HEARTBEAT
    now = time.time()
    if ACTIVE_VIEWER_ID is not None and (now - LAST_HEARTBEAT) > SESSION_TIMEOUT_SEC:
        ACTIVE_VIEWER_ID = None
    if viewer_id:
        if ACTIVE_VIEWER_ID is None:
            ACTIVE_VIEWER_ID = viewer_id
            LAST_HEARTBEAT = now
        elif ACTIVE_VIEWER_ID == viewer_id:
            LAST_HEARTBEAT = now
    return viewer_id is not None and ACTIVE_VIEWER_ID == viewer_id


JOB_STATE = {
    "status": "idle",        # idle | en_curso | finalizado
    "lista": None,
    "start_date": None,
    "end_date": None,
    "total_pozos": 0,
    "procesados": 0,
    "detalles": [],          # lista de dicts por pozo
    "download_path": None,   # ruta en el servidor donde se guardan los .xls
}

def on_job_status(event: dict):
    etype = event.get("type")

    if etype == "pozo_update":
        codigo = event.get("codigo")
        nuevo_estado = event.get("estado")
        mensaje = event.get("mensaje", "")

        for item in JOB_STATE["detalles"]:
            if item["codigo"] == codigo:
                item["estado"] = nuevo_estado
                item["mensaje"] = mensaje
                break

        # Recalcular procesados como los que ya no están en "Pendiente"
        JOB_STATE["procesados"] = sum(
            1 for item in JOB_STATE["detalles"] if item["estado"] != "Pendiente"
        )

    elif etype == "job_finished":
        JOB_STATE["status"] = "finalizado"

bp = Blueprint("main", __name__)


@bp.route("/", methods=["GET", "POST"])
def index():
    viewer_id = request.cookies.get("viewer_id")
    if not viewer_id:
        viewer_id = str(uuid.uuid4())

    if request.method == "POST":
        if not _update_session_claim(viewer_id):
            return redirect(url_for("main.index"))
        if JOB_STATE["status"] == "en_curso":
            # Ya hay un job corriendo; no lanzamos otro
            cfg = load_config("data/config.json")
            novnc_url = cfg.get("NOVNC_URL", "http://127.0.0.1:6080")
            return render_template(
                "index.html",
                job_state=JOB_STATE,
                novnc_url=novnc_url,
                session_owner=True,
            )

        selected_list = request.form.get("lista")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        
        def to_ddmmyyyy(d: str) -> str:
            return datetime.strptime(d,"%Y-%m-%d").strftime("%d-%m-%Y")
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
            cfg = load_config("data/config.json")
            novnc_url = cfg.get("NOVNC_URL", "http://127.0.0.1:6080")
            return render_template(
                "index.html",
                job_state=JOB_STATE,
                novnc_url=novnc_url,
                session_owner=True,
            )

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
        JOB_STATE["download_path"] = str(downloads_folder_for_subfolder(selected_list).resolve())

        cfg = load_config("data/config.json")
        cfg["startValue"] = to_ddmmyyyy(start_date)
        cfg["endValue"] = to_ddmmyyyy(end_date)
        cfg["SUBFOLDER"] = selected_list
        '''
        cfg = {
            "startValue": to_ddmmyyyy(start_date),
            "endValue": to_ddmmyyyy(end_date),
            "SUBFOLDER": selected_list,
            "SHARED_ROOT_NAME": "Quantica",
            "BASE_DEST_DIRS_REL": [
                "OP_TECH_DATOS - General/2026/2036 - 2253 - Q INTERNO TELEMETRIA/E2_DESARROLLO/D_TELEMETRIA/EXTRACCIONES MOP/2366 - CASUB_Soporte P12",
                "OP_TECH_DATOS - General/2026/2036 - 2253 - Q INTERNO TELEMETRIA/E2_DESARROLLO/D_TELEMETRIA/EXTRACCIONES MOP/2368 - CASUB_Soporte P17",
                "OP_TECH_DATOS - General/2026/2036 - 2253 - Q INTERNO TELEMETRIA/E2_DESARROLLO/D_TELEMETRIA/EXTRACCIONES MOP/2367 - CASUB_Soporte P22",
                "OP_TECH_DATOS - General/2026/2036 - 2253 - Q INTERNO TELEMETRIA/E2_DESARROLLO/D_TELEMETRIA/EXTRACCIONES MOP/2253 - COFANTI DGA 5 POZOS"
            ]
        }
        '''

        # Lanzamos el job en un hilo en background
        t = threading.Thread(
            target=run_download_job,
            args=(cfg, codes, selected_list, on_job_status),
            daemon=True,
        )
        t.start()
        return redirect(url_for("main.index"))

    session_owner = _update_session_claim(viewer_id)
    cfg = load_config("data/config.json")
    novnc_url = cfg.get("NOVNC_URL", "http://127.0.0.1:6080")
    resp = make_response(
        render_template(
            "index.html",
            job_state=JOB_STATE,
            novnc_url=novnc_url,
            session_owner=session_owner,
        )
    )
    if not request.cookies.get("viewer_id"):
        resp.set_cookie("viewer_id", viewer_id, max_age=60 * 60 * 24 * 365)
    return resp

@bp.route("/api/estado-actual")
def api_estado_actual():
    viewer_id = request.cookies.get("viewer_id")
    session_owner = _update_session_claim(viewer_id)
    return jsonify({**JOB_STATE, "session_owner": session_owner})