from flask import Blueprint, render_template, request

JOB_STATE = {
    "status": "idle",        # idle | en_curso | finalizado
    "lista": None,
    "start_date": None,
    "end_date": None,
    "total_pozos": 0,
    "procesados": 0,
    "detalles": [],          # luego será una lista de dicts por pozo
}

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
        selected_list = request.form.get("lista")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        # Por ahora: simulamos un job en memoria sin Selenium
        JOB_STATE["status"] = "en_curso"
        JOB_STATE["lista"] = selected_list
        JOB_STATE["start_date"] = start_date
        JOB_STATE["end_date"] = end_date

        # Simulamos 3 pozos “dummy” para probar la tabla
        JOB_STATE["detalles"] = [
            {"codigo": "OB-TEST-001", "estado": "Pendiente", "mensaje": ""},
            {"codigo": "OB-TEST-002", "estado": "Pendiente", "mensaje": ""},
            {"codigo": "OB-TEST-003", "estado": "Pendiente", "mensaje": ""},
        ]
        JOB_STATE["total_pozos"] = len(JOB_STATE["detalles"])
        JOB_STATE["procesados"] = 0

    return render_template(
        "index.html",
        job_state=JOB_STATE,
    )