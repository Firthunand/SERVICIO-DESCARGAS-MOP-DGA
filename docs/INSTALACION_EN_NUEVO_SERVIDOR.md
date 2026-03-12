# Instalación del aplicativo MOP DGA en un nuevo servidor

Guía paso a paso para instalar y dejar corriendo el **Servicio de descargas MOP – Telemetría** en un servidor Ubuntu. En este ejemplo el servidor tiene IP **3.147.102.192** (sustituir por la IP real si cambia).

---

## Resumen

| Qué | Dónde / Cómo |
|-----|----------------|
| Aplicación web (formulario + estado) | `http://3.147.102.192:5000` |
| Navegador remoto (CAPTCHA) | `http://3.147.102.192:6080/vnc.html` (noVNC) |
| Usuario sugerido en el servidor | `datos` (o el que uses para ejecutar la app) |

---

## Requisitos del servidor

- **SO:** Ubuntu 20.04 o 22.04 (recomendado).
- **Acceso:** SSH al servidor con usuario con `sudo`.
- **Red:** Puertos **5000** (Flask) y **6080** (noVNC) accesibles desde los clientes que usarán la app.

---

## Paso 1: Conectarse al servidor por SSH

```bash
ssh usuario@3.147.102.192
```

Sustituir `usuario` por el usuario SSH del servidor.

---

## Paso 2: Actualizar el sistema e instalar paquetes base

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv unzip wget
```

---

## Paso 3: Instalar Chrome o Chromium y ChromeDriver

La aplicación usa Selenium con Chrome/Chromium para automatizar el portal MOP.

**Opción A – Google Chrome (recomendado)**

```bash
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install -y google-chrome-stable
```

ChromeDriver (ajustar la versión a la de Chrome instalada):

```bash
# Ver versión de Chrome
google-chrome --version

# Descargar ChromeDriver compatible (ejemplo: 131.x)
CHROME_VER=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
DRIVER_VER=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VER%%.*}")
wget -q "https://storage.googleapis.com/chrome-for-testing-public/${DRIVER_VER}/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip
unzip -o /tmp/chromedriver.zip -d /tmp
sudo mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64
```

**Opción B – Chromium (paquetes Ubuntu)**

```bash
sudo apt install -y chromium-browser chromium-chromedriver
```

Si usas Chromium, la app usará el `chromedriver` del paquete (suele estar en `PATH`).

**Nota:** Con Selenium 4.x, si Chrome/Chromium está instalado pero no encuentras ChromeDriver, Selenium puede descargarlo automáticamente la primera vez que ejecutes la app. En ese caso puedes omitir la instalación manual de ChromeDriver y probar directamente.

Comprobar:

```bash
chromedriver --version
# o
/usr/local/bin/chromedriver --version
```

---

## Paso 4: Instalar Xvfb, Openbox, x11vnc y noVNC

Necesarios para que Chrome se vea en una pantalla virtual y el usuario pueda resolver el CAPTCHA desde el navegador.

```bash
sudo apt install -y xvfb openbox x11vnc
```

**noVNC** (cliente VNC en el navegador):

```bash
cd ~
git clone https://github.com/novnc/noVNC.git
cd noVNC
./utils/novnc_proxy --vnc localhost:5900 --listen 6080 &
```

Para tener noVNC disponible siempre, se puede dejar este comando en un script o en un servicio systemd (ver Paso 9 opcional).

---

## Paso 5: Copiar el proyecto al servidor

Desde tu PC (donde está el código), por SCP o rsync:

```bash
# Desde tu PC (ajusta usuario y ruta del proyecto)
scp -r "C:\ruta\al\SERVICIO-DESCARGAS-MOP-DGA" usuario@3.147.102.192:~/
```

O si el proyecto está en un repositorio Git, en el servidor:

```bash
cd ~
git clone <URL_DEL_REPOSITORIO> SERVICIO-DESCARGAS-MOP-DGA
cd SERVICIO-DESCARGAS-MOP-DGA
```

Comprobar que existe la estructura:

```bash
ls -la
# Debe haber: app/, core/, data/, scripts/, run_flask.py, requirements.txt
```

---

## Paso 6: Entorno virtual Python e instalar dependencias

En el servidor, dentro de la carpeta del proyecto:

```bash
cd ~/SERVICIO-DESCARGAS-MOP-DGA
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Comprobar:

```bash
pip list
# Debe aparecer flask y selenium
```

---

## Paso 7: Configurar la aplicación para este servidor

Editar `data/config.json` y poner la **IP de este servidor** en la URL de noVNC (para que el iframe del CAPTCHA apunte al mismo servidor):

```bash
nano data/config.json
```

Cambiar la línea de `NOVNC_URL` a:

```json
"NOVNC_URL": "http://3.147.102.192:6080",
```

Si en este servidor la IP pública es otra o usas nombre de dominio, usa esa URL. Guardar (Ctrl+O, Enter, Ctrl+X).

Revisar también (si aplica):

- **SHARED_ROOT_NAME** y **BASE_DEST_DIRS_REL**: definen la **carpeta local en el servidor** donde se mueven los archivos (no se usa OneDrive; un script externo leerá esa carpeta para subir a una base de datos). Ver `docs/DESTINO_ARCHIVOS_EN_SERVIDOR.md`.

---

## Paso 8: Dar permisos al script de arranque y ejecutarlo

```bash
chmod +x scripts/start_servicio.sh
./scripts/start_servicio.sh
```

El script hará en orden:

1. Iniciar Xvfb (pantalla virtual `:99`).
2. Iniciar Openbox (gestor de ventanas).
3. Iniciar x11vnc en el puerto 5900.
4. Iniciar la aplicación Flask en el puerto 5000.

Debe quedar algo como:

```text
Xvfb iniciado en display :99
Openbox iniciado
x11vnc escuchando en puerto 5900
Iniciando aplicación Flask...
 * Running on http://0.0.0.0:5000
```

**Importante:** noVNC debe estar corriendo en el puerto 6080. Si no lo iniciaste en el Paso 4, en otra terminal:

```bash
cd ~/noVNC
./utils/novnc_proxy --vnc localhost:5900 --listen 6080
```

Dejar esa terminal abierta o ejecutarla en segundo plano con `&`.

---

## Comprobar si los puertos entran en conflicto

La app usa estos puertos:

| Puerto | Uso |
|--------|-----|
| **5000** | Aplicación Flask (formulario y estado). |
| **6080** | noVNC (navegador remoto para el CAPTCHA). |
| **5900** | x11vnc (interno; noVNC se conecta a él desde el mismo servidor). |

### Ver qué está usando cada puerto

En el servidor ejecuta:

```bash
# Ver qué proceso escucha en el puerto 5000 (Flask)
sudo ss -tlnp | grep :5000
# o
sudo lsof -i :5000

# Ver qué proceso escucha en el puerto 6080 (noVNC)
sudo ss -tlnp | grep :6080
sudo lsof -i :6080

# Ver qué proceso escucha en el puerto 5900 (x11vnc)
sudo ss -tlnp | grep :5900
sudo lsof -i :5900
```

**Interpretación:**

- Si **no sale ninguna línea**: el puerto está libre, no hay conflicto.
- Si **sale una línea** con otro proceso (por ejemplo `systemd` en 5000, u otra app en 6080): ese puerto ya está ocupado y puede haber conflicto cuando arranques la app.

**Ver todos los puertos en escucha (TCP):**

```bash
sudo ss -tlnp
```

Busca en la columna de puertos las filas que muestren `:5000`, `:6080` o `:5900`.

### Si hay conflicto: cambiar los puertos

**1. Cambiar el puerto de Flask (por defecto 5000)**

Editar `run_flask.py` y usar otro puerto (por ejemplo 5001):

```python
app.run(host='0.0.0.0', port=5001, debug=False)
```

Quien acceda a la app usará `http://<IP>:5001`.

**2. Cambiar el puerto de noVNC (por defecto 6080)**

- Al arrancar noVNC, usa otro puerto, por ejemplo 6081:
  ```bash
  ~/noVNC/utils/novnc_proxy --vnc localhost:5900 --listen 6081
  ```
- En `data/config.json` actualiza la URL con el nuevo puerto:
  ```json
  "NOVNC_URL": "http://3.147.102.192:6081"
  ```
- Abre el nuevo puerto en el firewall si usas UFW: `sudo ufw allow 6081/tcp`.

**3. Cambiar el puerto de x11vnc (por defecto 5900)**

Solo hace falta si 5900 está ocupado. Editar `scripts/start_servicio.sh`: en la línea de `x11vnc` cambiar `-rfbport 5900` por `-rfbport 5901`. Y arrancar noVNC apuntando a 5901: `--vnc localhost:5901`.

---

## Paso 9: Abrir puertos en el firewall (si hay UFW)

Si el servidor usa UFW:

```bash
sudo ufw allow 5000/tcp
sudo ufw allow 6080/tcp
sudo ufw reload
sudo ufw status
```

---

## Paso 10: Probar el acceso desde un navegador

Desde cualquier PC en la red (o con acceso a la IP del servidor):

1. **Aplicación web:**  
   Abrir: **http://3.147.102.192:5000**  
   Debe verse el formulario “Descarga de reportes MOP – Telemetría” (lista, fechas, botón Iniciar descarga).

2. **Navegador remoto (CAPTCHA):**  
   Al iniciar una descarga, en la misma página debe cargarse el iframe con noVNC. Si no carga, abrir en otra pestaña: **http://3.147.102.192:6080/vnc.html**

3. **Prueba de descarga:**  
   Elegir lista (ej. P5), fechas y pulsar “Iniciar descarga”. Resolver el CAPTCHA en el recuadro inferior y comprobar que los archivos se descargan y, si está configurado, se mueven a las carpetas destino.

---

## Dejar todo corriendo de forma permanente (opcional)

- **Flask + Xvfb + Openbox + x11vnc:** se puede crear un servicio systemd que ejecute `scripts/start_servicio.sh` al arrancar el servidor (o dividir en varios servicios: uno para Xvfb, otro para Flask, etc.).
- **noVNC:** crear un servicio systemd que ejecute `~/noVNC/utils/novnc_proxy --vnc localhost:5900 --listen 6080` al arrancar.

Si quieres, en un siguiente paso se puede detallar el contenido exacto de los archivos `.service` para este servidor.

---

## Resumen de pasos (checklist)

| # | Paso |
|---|------|
| 1 | Conectarse por SSH al servidor (3.147.102.192). |
| 2 | `sudo apt update && sudo apt install -y python3 python3-pip python3-venv unzip wget`. |
| 3 | Instalar Chrome (o Chromium) y ChromeDriver. |
| 4 | Instalar Xvfb, Openbox, x11vnc; clonar noVNC y levantar `novnc_proxy` en 6080. |
| 5 | Copiar el proyecto al servidor (SCP o git clone). |
| 6 | Crear venv, activar y `pip install -r requirements.txt`. |
| 7 | En `data/config.json` poner `"NOVNC_URL": "http://3.147.102.192:6080"`. |
| 8 | Ejecutar `./scripts/start_servicio.sh` desde la raíz del proyecto. |
| 9 | Abrir puertos 5000 y 6080 en el firewall si aplica. |
| 10 | Probar en el navegador: http://3.147.102.192:5000 y, si hace falta, http://3.147.102.192:6080/vnc.html. |

(Opcional) Crear en el servidor la estructura de carpetas destino (`SHARED_ROOT_NAME` + `BASE_DEST_DIRS_REL`) para que la app mueva ahí los .xls; un script externo puede leer esa carpeta para subir a una base de datos. Ver `docs/DESTINO_ARCHIVOS_EN_SERVIDOR.md`.
