# Servicio de descargas MOP – Telemetría

Aplicación web que automatiza la descarga de reportes desde el portal MOP (SNIA) usando Selenium y Chrome. El usuario resuelve el CAPTCHA en un navegador remoto (noVNC). Los archivos descargados se mueven a carpetas locales en el servidor (por defecto bajo `/opt/quantica`).

## Características

- Formulario web: selección de lista (P5, P12, P17, P22), rango de fechas e inicio de descarga.
- Una sola sesión activa a la vez; el resto de usuarios ve "Sesión en uso".
- Estado en tiempo real (tabla por pozo) y botón para detener la descarga.
- Destino de archivos configurable en `data/config.json` (`BASE_DEST_DIRS`); por lista y año.

## Requisitos

- Python 3, Flask, Selenium, Chrome/Chromium, ChromeDriver.
- En servidor: Xvfb, Openbox, x11vnc, noVNC (para el CAPTCHA).
- Locale `es_CL.UTF-8` en el servidor (validación de fechas en el portal MOP).

## Arranque rápido

- **Desarrollo:** `./scripts/start_servicio.sh` (Flask en 5000). noVNC aparte en 6080.
- **Producción:** `./scripts/start_servicio_gunicorn.sh` (Gunicorn 1 worker) o servicio systemd con `scripts/systemd/mopdga.service`.

Ver `scripts/README.md` para los scripts y `docs/INSTALACION_EN_NUEVO_SERVIDOR.md` para instalación completa.

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [docs/USO_APLICATIVO.md](docs/USO_APLICATIVO.md) | Uso para el usuario final (acceso, CAPTCHA, detener descarga). |
| [docs/INSTALACION_EN_NUEVO_SERVIDOR.md](docs/INSTALACION_EN_NUEVO_SERVIDOR.md) | Instalación paso a paso en un servidor Ubuntu. |
| [docs/DESTINO_ARCHIVOS_EN_SERVIDOR.md](docs/DESTINO_ARCHIVOS_EN_SERVIDOR.md) | Dónde se guardan los archivos (`/opt/quantica/...`) y configuración. |
| [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | Arquitectura y módulos a nivel código (mantenimiento). |
| [scripts/README.md](scripts/README.md) | Scripts de arranque y servicio systemd. |

## Configuración

- `data/config.json`: `NOVNC_URL`, `BASE_DEST_DIRS` (rutas absolutas de destino), fechas por defecto.
- Listas de códigos: `data/pozosADescargarP5.txt`, etc.

No se usa OneDrive ni rclone; el destino es solo carpeta local en el servidor.
