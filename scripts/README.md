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

- Usa el entorno virtual `env/` si existe.
- Levanta la app con Gunicorn en `0.0.0.0:5000` usando `run_flask:app` como entrypoint.

Se recomienda combinar este script con un servicio **systemd** para que quede permanente.

## systemd/rclone-onedrive.service

Servicio para montar OneDrive con rclone en `/home/datos/Quantica` (para que la app guarde ahí los archivos). Ver **docs/ONEDRIVE_RCLONE_PASO_A_PASO.md** para la guía completa.

```bash
sudo cp scripts/systemd/rclone-onedrive.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now rclone-onedrive
```

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
