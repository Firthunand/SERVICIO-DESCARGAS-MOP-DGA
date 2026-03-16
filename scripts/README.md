# Scripts del servicio MOP DGA

## start_servicio.sh

Arranca en orden: **Xvfb** → **Openbox** → **x11vnc** → **Flask**.

**Uso (desde la raíz del proyecto, modo desarrollo):**

```bash
chmod +x scripts/start_servicio.sh
./scripts/start_servicio.sh
```

O desde la carpeta `scripts/`:

```bash
./start_servicio.sh
```

- Si el display `:99` ya está en uso (Xvfb corriendo), no lo vuelve a iniciar.
- Al pulsar **Ctrl+C** se detienen Flask, x11vnc, Openbox y Xvfb (si los inició este script).

**Requisitos:** `Xvfb`, `openbox`, `x11vnc` instalados. Opcional: `openbox` (`sudo apt install openbox`).

**noVNC:** Si usas noVNC en el navegador, debes tenerlo corriendo aparte (por ejemplo `~/noVNC/utils/novnc_proxy --vnc localhost:5900 --listen 6080`).

---

## start_servicio_gunicorn.sh

Arranca en orden: **Xvfb** → **Openbox** → **x11vnc** → **Gunicorn** (app Flask).

**Uso (desde la raíz del proyecto, modo producción simple):**

```bash
chmod +x scripts/start_servicio_gunicorn.sh
./scripts/start_servicio_gunicorn.sh
```

- Al iniciar, mata procesos previos de Xvfb, openbox y x11vnc para evitar conflictos de puertos.
- Usa **1 worker** de Gunicorn (estado en memoria compartido). Si usas entorno virtual `env/`, actívalo antes o configúralo en el servicio systemd (PATH con Miniconda o venv).
- Levanta la app en `0.0.0.0:5000` con `run_flask:app`.

Se recomienda combinar este script con un servicio **systemd** (`mopdga.service`) para que quede permanente.

---

## systemd/mopdga.service

Servicio systemd de ejemplo para dejar la app MOP DGA corriendo de forma permanente (Xvfb + VNC + Gunicorn).

**Pasos básicos en el servidor (ajustar rutas/usuario si es necesario):**

```bash
sudo cp scripts/systemd/mopdga.service /etc/systemd/system/
sudo nano /etc/systemd/system/mopdga.service  # revisar User, WorkingDirectory, PATH y rutas
sudo systemctl daemon-reload
sudo systemctl enable --now mopdga
sudo systemctl status mopdga
```

Una vez habilitado, el servicio se levantará automáticamente al arrancar el servidor y **seguirá activo aunque cierres la sesión SSH**.
