# Arquitectura de la aplicación (nivel código)

Resumen técnico del **Servicio de descargas MOP – Telemetría** para mantenimiento y cambios futuros.

---

## Flujo general

```
Usuario (navegador)
       │
       ▼
  Flask (app/routes.py)
  · GET  /         → formulario + estado; si sesión nueva y job finalizado/cancelado → reset estado
  · POST /         → inicia job en hilo (run_download_job) si no hay otro en curso
  · GET  /api/estado-actual  → JSON con JOB_STATE + session_owner (polling desde el front)
  · POST /api/detener-descarga → STOP_REQUESTED.set() + status = "cancelado"
       │
       │  (threading.Thread, daemon=True)
       ▼
  core/mop_client.run_download_job(cfg, codes, lista_id, on_job_status, stop_event)
  · DISPLAY=:99, LANG=es_CL.UTF-8
  · base_dirs desde cfg["BASE_DEST_DIRS"] (o BASE_DEST_DIRS_REL + SHARED_ROOT_NAME)
  · Chrome (Selenium) → portal MOP → CAPTCHA (usuario en noVNC) → Buscar → Mediciones → fechas → Exportar
  · Descarga .xls en ~/Downloads/<lista>; mueve a /opt/quantica/.../<lista>/<año>/ por lista (P5,P12,P17,P22)
  · Callbacks on_job_status: pozo_update | job_finished | job_cancelled
       │
       ▼
  JOB_STATE actualizado en memoria (1 worker Gunicorn para compartir estado)
```

- **noVNC** (puerto 6080) muestra la pantalla de Xvfb donde corre Chrome; el usuario resuelve el CAPTCHA ahí.
- **Gunicorn** se lanza desde `scripts/start_servicio_gunicorn.sh` (1 worker, 4 threads) para que `JOB_STATE`, sesión única y `STOP_REQUESTED` compartan el mismo proceso.

---

## Módulos principales

| Módulo / archivo | Responsabilidad |
|------------------|-----------------|
| `run_flask.py` | Punto de entrada: crea la app Flask y la arranca (dev) o sirve como `application` para Gunicorn. |
| `app/__init__.py` | Factory `create_app()`: crea la app, registra el blueprint de rutas. |
| `app/routes.py` | Rutas web y API; sesión única (cookie `viewer_id`, timeout 45 s); `JOB_STATE`; lanzar job en hilo con `stop_event`; reset estado al volver con job finalizado/cancelado. |
| `app/templates/` | HTML (formulario, estado, iframe noVNC, botón Detener, polling). |
| `core/mop_client.py` | Flujo Selenium: abrir MOP, esperar CAPTCHA, rellenar código, Buscar, Mediciones, fechas, Exportar; esperar .xls; mover por lista a `BASE_DEST_DIRS` + año. |
| `core/downloads.py` | `downloads_folder_for_subfolder`, `find_existing_files_for_code`, `wait_for_new_xls_and_rename`. |
| `core/pozos.py` | `load_pozos_map`, `find_pozo_folder_in_bases`, `move_report_to_destination` (usado solo para archivos ya existentes al inicio; el movimiento post-descarga se hace en mop_client por lista). |
| `core/naming.py` | Nombres de archivo esperados y parseo de año del periodo. |
| `core/config.py` | Carga de `data/config.json` y de listas de códigos. |
| `data/config.json` | `NOVNC_URL`, `BASE_DEST_DIRS` (rutas absolutas, ej. `/opt/quantica/...`), fechas por defecto, etc. |
| `scripts/start_servicio_gunicorn.sh` | Arranque: pkill previos (Xvfb, openbox, x11vnc); Xvfb :99; Openbox; x11vnc 5900; Gunicorn 1 worker, 4 threads. |
| `scripts/systemd/mopdga.service` | Servicio systemd para producción (User, WorkingDirectory, PATH con Miniconda si aplica). |

---

## Dónde tocar para cambios frecuentes

| Objetivo | Dónde |
|----------|--------|
| Cambiar carpetas destino de los .xls | `data/config.json` → `BASE_DEST_DIRS` (rutas absolutas). Lógica de asignación por lista en `core/mop_client.py` → `_dest_root_for_lista`. |
| Cambiar tiempo de espera de descarga del .xls | `core/downloads.py` → `DOWNLOAD_WAIT_TIMEOUT`. |
| Cambiar tiempo de sesión inactiva (45 s) | `app/routes.py` → `SESSION_TIMEOUT_SEC`. |
| Cambiar reintentos de CAPTCHA / esperas Selenium | `core/mop_client.py` → `MAX_REFRESH`, `time.sleep`, `WebDriverWait(..., timeout=...)`. |
| Añadir otra lista (ej. P30) | `app/routes.py` → `lista_to_path` y archivo en `data/`; `core/mop_client.py` → `lista_to_pozos_map` y `_dest_root_for_lista`; `data/config.json` → nueva ruta en `BASE_DEST_DIRS` si aplica. |
| URL del portal MOP | `core/mop_client.py` → `ROOT1`. |
| Workers/hilos Gunicorn | `scripts/start_servicio_gunicorn.sh` → `--workers` / `--threads`. Debe ser 1 worker para compartir estado en memoria. |

---

## Estado en memoria y sesión única

- **JOB_STATE**: diccionario global en `app/routes.py` (status, lista, fechas, detalles por pozo, download_path). Lo actualiza el hilo de `run_download_job` vía `on_job_status`.
- **Sesión única**: cookie `viewer_id`; `ACTIVE_VIEWER_ID` y `LAST_HEARTBEAT` en `routes.py`. GET `/` y GET `/api/estado-actual` renuevan el heartbeat. Si otro usuario abre la app, ve "Sesión en uso" hasta que el dueño deje de hacer requests ~45 s.
- **Detener descarga**: `STOP_REQUESTED` (threading.Event). POST `/api/detener-descarga` hace `set()` y pone `JOB_STATE["status"] = "cancelado"`. El hilo en `mop_client` comprueba `stop_event.is_set()` en bucles (entre códigos, espera CAPTCHA, etc.) y sale; Chrome puede tardar unos segundos en cerrarse.

---

## Documentación relacionada

- **Uso** (usuario final): `docs/USO_APLICATIVO.md`
- **Instalación en servidor**: `docs/INSTALACION_EN_NUEVO_SERVIDOR.md`
- **Destino de archivos**: `docs/DESTINO_ARCHIVOS_EN_SERVIDOR.md`
- **Scripts de arranque**: `scripts/README.md`
