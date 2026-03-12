# OneDrive en el servidor Ubuntu – Guía paso a paso

> **Nota:** Este proyecto **ya no utiliza OneDrive**. Los archivos se dejan en una **carpeta local del servidor**; un script externo se encarga de subir la información a una base de datos. Ver **docs/DESTINO_ARCHIVOS_EN_SERVIDOR.md**.  
> La guía siguiente se mantiene por referencia por si en el futuro se requiriera de nuevo sincronización con OneDrive.

Objetivo (referencia): que los archivos descargados por la app se muevan a las **carpetas compartidas de OneDrive** y queden disponibles para todos los usuarios.

La app ya mueve los archivos a rutas definidas en `data/config.json`. Esas rutas deben ser una carpeta local que **sincronice con OneDrive** (o esté montada como OneDrive). Esta guía explica cómo dejarlo listo.

---

## 1. Qué usa la app (sin cambiar código)

La aplicación construye la ruta destino así:

- **Raíz:** `$HOME/<SHARED_ROOT_NAME>`  
  En tu `config.json`: `SHARED_ROOT_NAME` = `"Quantica"` → en el servidor es **`/home/datos/Quantica`** (si el usuario es `datos`).

- **Carpetas base:** dentro de esa raíz, las rutas de `BASE_DEST_DIRS_REL` (P12, P17, P22, P5, etc.).

Ejemplo de ruta completa en el servidor:

```text
/home/datos/Quantica/OP_TECH_DATOS - General/2026/2036 - 2253 - Q INTERNO TELEMETRIA/E2_DESARROLLO/D_TELEMETRIA/EXTRACCIONES MOP/2366 - CASUB_Soporte P12
```

Mientras esa estructura **exista** en el servidor (y sea la que OneDrive sincroniza), la app moverá ahí los archivos y quedarán disponibles en las carpetas compartidas.

---

## 2. Opción A: Cliente OneDrive (sincronizar una carpeta)

Sincronizas la cuenta/carpeta compartida de OneDrive a una carpeta local. La app escribe ahí y el cliente sube a la nube.

### 2.1 Instalar el cliente OneDrive (abraunegg)

En el servidor Ubuntu:

```bash
# Añadir el PPA e instalar (Ubuntu 22.04 / 24.04)
sudo add-apt-repository ppa:yann1ck/onedrive
sudo apt update
sudo apt install onedrive
```

Si el PPA no está disponible, ver instalación desde fuentes en:  
https://github.com/abraunegg/onedrive/blob/master/docs/INSTALL.md

### 2.2 Configurar la carpeta de sincronización

La carpeta local que OneDrive sincronice **debe ser** la raíz que usa la app: `$HOME/Quantica`.

```bash
mkdir -p ~/.config/onedrive
nano ~/.config/onedrive/config
```

Contenido mínimo (ajusta si tu estructura en OneDrive es distinta):

```ini
sync_dir = "/home/datos/Quantica"
```

Guarda el archivo. Asegúrate de que la estructura dentro de OneDrive (en la nube) coincida con las rutas de `BASE_DEST_DIRS_REL` de tu `config.json` (mismas carpetas P12, P17, P22, 2253 - COFANTI DGA 5 POZOS, etc.).

### 2.3 Autorizar con la cuenta Microsoft (solo la primera vez)

```bash
onedrive --synchronize
```

Te pedirá abrir un enlace en un navegador, iniciar sesión con la cuenta de la empresa y autorizar. En un servidor sin navegador puedes hacerlo desde tu PC y copiar el token si el cliente lo permite, o usar una sesión con port forwarding. Revisa la documentación del cliente para “headless”.

### 2.4 Sincronización

```bash
onedrive --synchronize
```

Para dejarlo corriendo en segundo plano (y que siga sincronizando):

```bash
nohup onedrive --monitor > ~/onedrive.log 2>&1 &
```

O configurar un servicio systemd (ver documentación del proyecto onedrive).

Cuando `/home/datos/Quantica` exista y contenga la estructura de carpetas (P12, P17, P22, etc.), la app moverá los archivos ahí y OneDrive los subirá a las carpetas compartidas.

---

## 3. Opción B: rclone (montar OneDrive como carpeta)

OneDrive se “monta” en una ruta local. Todo lo que la app escriba en esa ruta se sube a la nube. No hace falta sincronizar toda la estructura por separado.

### 3.1 Instalar rclone

```bash
sudo apt update
sudo apt install rclone
```

### 3.2 Configurar el remoto OneDrive

```bash
rclone config
```

- `n` (new remote), nombre p. ej. `onedrive`.
- Elige el tipo de almacenamiento (OneDrive, según la opción que muestre rclone).
- Sigue los pasos para iniciar sesión con la cuenta Microsoft (enlace, código, etc.).

### 3.3 Crear el punto de montaje y montar

La raíz que usa la app es `$HOME/Quantica`. Monta OneDrive de forma que esa ruta sea el “raíz” de lo que verá la app. Depende de cómo esté organizado en OneDrive:

**Si en OneDrive la raíz de las carpetas compartidas es una carpeta “Quantica” (o similar):**

```bash
mkdir -p /home/datos/Quantica
rclone mount onedrive:Quantica /home/datos/Quantica --vfs-cache-mode full --dir-cache-time 5m --daemon
```

**Si en OneDrive las carpetas están en la raíz del OneDrive:**

Puedes montar el remoto en `/home/datos/Quantica` y que la estructura bajo `BASE_DEST_DIRS_REL` coincida con la de la nube, o montar en otra ruta y usar en `config.json` una raíz distinta (ver sección 4).

Comprueba que las rutas que escribe la app (según `config.json`) existan dentro del montaje. Si no, créalas una vez montado o ajusta `config.json`.

### 3.4 Montar al arrancar el servidor (opcional)

Puedes crear un servicio systemd que ejecute el `rclone mount` al inicio. Ejemplo de unidad (ajusta rutas y nombre del remoto):

```ini
# /etc/systemd/system/rclone-onedrive.service
[Unit]
Description=Rclone mount OneDrive (Quantica)
After=network-online.target

[Service]
Type=notify
User=datos
ExecStart=/usr/bin/rclone mount onedrive:Quantica /home/datos/Quantica --vfs-cache-mode full --dir-cache-time 5m
ExecStop=/bin/fusermount -uz /home/datos/Quantica
Restart=on-failure

[Install]
WantedBy=default.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable rclone-onedrive
sudo systemctl start rclone-onedrive
```

---

## 4. Ajustar config.json si la ruta en el servidor es otra

Si en el servidor la carpeta de OneDrive no va a ser `~/Quantica`, sino otra (por ejemplo `~/OneDrive/Quantica`):

1. En `data/config.json` cambia `SHARED_ROOT_NAME` a la **parte que va después de `$HOME`**:
   - Si la ruta real es `/home/datos/OneDrive/Quantica`, puedes poner en config una ruta absoluta solo si la app lo soporta; actualmente la app hace `Path.home() / SHARED_ROOT_NAME`, así que la raíz sería `OneDrive/Quantica` si pones `"SHARED_ROOT_NAME": "OneDrive/Quantica"` (dependiendo de cómo esté implementado, puede que solo acepte un segmento). Revisa `core/mop_client.py`: `shared_root = Path.home() / cfg["SHARED_ROOT_NAME"]`. Con `Path("OneDrive/Quantica")` sí daría `/home/datos/OneDrive/Quantica`. Así que en ese caso:
   - `"SHARED_ROOT_NAME": "OneDrive/Quantica"`
2. Mantén `BASE_DEST_DIRS_REL` igual si la estructura bajo esa raíz es la misma (P12, P17, P22, 2253 - COFANTI, etc.).

---

## 5. Comprobar que todo está listo

1. **Rutas existentes en el servidor**

   Desde la cuenta con la que corre la app (p. ej. `datos`):

   ```bash
   echo $HOME
   ls -la "$HOME/Quantica"
   ```

   Deberías ver las carpetas base (o la estructura que definas en `BASE_DEST_DIRS_REL`). Si usas rclone, después de montar deben aparecer ahí.

2. **Prueba con la app**

   - Lanza una descarga con pocos pozos (p. ej. lista P5).
   - Revisa en el servidor que los .xls aparezcan en la carpeta correspondiente bajo `$HOME/Quantica/...`.
   - Si usas Opción A (cliente OneDrive), en unos segundos/minutos deberían verse en OneDrive (carpetas compartidas). Si usas Opción B (rclone mount), deberían verse en la nube al escribirse en el montaje.

3. **Logs de la app**

   En la salida de Flask verás líneas como:

   ```text
   DEBUG shared_root: /home/datos/Quantica
   DEBUG base_dirs:
    - /home/datos/Quantica/.../2366 - CASUB_Soporte P12 exists? True
   ```

   Si `exists? True`, la app podrá mover los archivos ahí. Si es `False`, crea la estructura (o corrige OneDrive/sync_dir/mount) y vuelve a probar.

---

## 6. Resumen

| Paso | Acción |
|------|--------|
| 1 | Decidir: **Opción A** (cliente OneDrive, sync a `~/Quantica`) o **Opción B** (rclone mount en `~/Quantica`). |
| 2 | Instalar y configurar el cliente o rclone según la opción. |
| 3 | Asegurar que la ruta que usa la app (`$HOME/Quantica` con la estructura de `BASE_DEST_DIRS_REL`) exista y sea la que sincroniza o monta OneDrive. |
| 4 | Ajustar `SHARED_ROOT_NAME` en `config.json` solo si la raíz real en el servidor es otra (p. ej. `OneDrive/Quantica`). |
| 5 | Probar una descarga y comprobar que los archivos aparecen en el servidor y en las carpetas compartidas de OneDrive. |

Con esto, la app solo descarga y mueve; los archivos quedarán en las carpetas compartidas para todos los usuarios.
