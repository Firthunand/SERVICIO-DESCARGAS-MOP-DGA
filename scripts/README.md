# Scripts del servicio MOP DGA

## start_servicio.sh

Arranca en orden: **Xvfb** → **Openbox** → **x11vnc** → **Flask**.

**Uso (desde la raíz del proyecto):**

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

## systemd/rclone-onedrive.service

Servicio para montar OneDrive con rclone en `/home/datos/Quantica` (para que la app guarde ahí los archivos). Ver **docs/ONEDRIVE_RCLONE_PASO_A_PASO.md** para la guía completa.

```bash
sudo cp scripts/systemd/rclone-onedrive.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now rclone-onedrive
```
