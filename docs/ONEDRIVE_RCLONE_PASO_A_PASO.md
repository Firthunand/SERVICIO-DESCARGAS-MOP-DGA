# OneDrive con rclone (Opción B) – Paso a paso

Guía para montar las carpetas compartidas de OneDrive en el servidor Ubuntu y que la app MOP guarde ahí los archivos descargados.

---

## Requisitos

- Servidor Ubuntu con acceso a internet.
- Cuenta Microsoft (OneDrive personal o Microsoft 365 / OneDrive de la empresa).
- Usuario del servidor que ejecuta la app (en esta guía: `datos`). La ruta que usa la app es `$HOME/Quantica` → `/home/datos/Quantica`.

---

## Paso 1: Instalar rclone

En el servidor (SSH):

```bash
sudo apt update
sudo apt install rclone
```

Comprobar:

```bash
rclone version
```

---

## Paso 2: Configurar el remoto OneDrive

Ejecuta el asistente de configuración:

```bash
rclone config
```

### 2.1 Crear un nuevo remoto

- Te pregunta **"e) Edit existing remote"** / **"n) New remote"** → pulsa **`n`** y Enter.
- **name>** → escribe un nombre, por ejemplo: **`onedrive`** y Enter.

### 2.2 Tipo de almacenamiento

- En la lista de tipos, busca **"Microsoft OneDrive"** o **"onedrive"**.
- Introduce el número que corresponda y Enter.

### 2.3 OneDrive personal vs OneDrive de empresa

- **OneDrive personal o Microsoft 365 (cuenta @outlook, @hotmail o @tuempresa.com):**  
  Suele aparecer como **"Microsoft OneDrive"** o **"OneDrive"**. Elige esa.
- **OneDrive for Business / SharePoint:**  
  A veces aparece como **"SharePoint"** o **"OneDrive for Business"**. Elige el que aplique a tu cuenta.

### 2.4 Autenticación

- **client_id>** y **client_secret>** → por defecto puedes dejar en blanco (Enter) para usar los de rclone.
- Te mostrará un **enlace** y un **código**. Necesitas abrir el enlace en un navegador (puede ser en tu PC):
  1. Copia el enlace que muestra rclone.
  2. Ábrelo en un navegador (en tu propio equipo si el servidor no tiene escritorio).
  3. Inicia sesión con la cuenta Microsoft de la empresa (la que tiene acceso a las carpetas compartidas).
  4. Introduce el código que rclone te mostró.
  5. Acepta los permisos.
- Vuelve al servidor y continúa (Enter).
- **Edit advanced config?** → **n** (salvo que sepas qué cambiar).
- **Use auto config?** → si estás en el servidor sin navegador, **n** y tendrás que usar “configurar desde otro equipo” (ver nota abajo). Si tienes escritorio en el servidor, **y**.
- **Configure as team drive?** → **n** (a menos que uses Google; en OneDrive no aplica).

### 2.5 Guardar

- **y** (yes) para confirmar.
- **q** (quit) para salir de `rclone config`.

**Nota (servidor sin navegador):** Si configuras desde SSH y no puedes abrir el enlace en el servidor, en tu PC ejecuta `rclone config` localmente, crea el remoto `onedrive` igual, y luego en el servidor copia el archivo de configuración:

- En tu PC (Windows): `%APPDATA%\rclone\rclone.conf`
- Cópialo al servidor a: `/home/datos/.config/rclone/rclone.conf`

---

## Paso 3: Identificar la ruta en OneDrive

La app escribe en rutas como (según tu `config.json`):

```text
/home/datos/Quantica/OP_TECH_DATOS - General/2026/2036 - 2253 - Q INTERNO TELEMETRIA/E2_DESARROLLO/...
```

Eso debe coincidir con la estructura **dentro de OneDrive**. Hay dos casos típicos:

**Caso A – En OneDrive tienes una carpeta “Quantica” (o similar) y dentro el resto:**

En rclone, la ruta del remoto sería: **`onedrive:Quantica`**  
(al montar `onedrive:Quantica` en `/home/datos/Quantica`, todo lo que está dentro de “Quantica” en la nube se ve en esa carpeta local).

**Caso B – En OneDrive las carpetas están en la raíz (sin carpeta “Quantica”):**

Entonces la raíz del remoto es la raíz del OneDrive. En rclone: **`onedrive:`** (vacío después de los dos puntos).  
Montarías: **`onedrive:`** en **`/home/datos/Quantica`**, y la estructura que ves en la raíz de OneDrive sería la que vería la app bajo `Quantica/`.

Listar contenido del remoto para comprobarlo:

```bash
# Listar raíz del OneDrive
rclone lsd onedrive:

# Si tienes una carpeta "Quantica" (o el nombre que uses)
rclone lsd onedrive:Quantica
```

Ajusta el nombre de carpeta según lo que veas (puede ser "Quantica", "Mi unidad", nombre de la empresa, etc.).

---

## Paso 4: Crear la carpeta local y montar (prueba)

Sustituye `Quantica` por el nombre de carpeta en OneDrive si es distinto (en los ejemplos se usa `Quantica`).

```bash
# Crear el punto de montaje (no debe existir con contenido previo)
mkdir -p /home/datos/Quantica

# Montar (si tu estructura está en la raíz de OneDrive, usa "onedrive:" sin nombre de carpeta)
rclone mount onedrive:Quantica /home/datos/Quantica --vfs-cache-mode full --dir-cache-time 5m --daemon
```

**Si las carpetas están en la raíz del OneDrive (no hay carpeta “Quantica”):**

```bash
rclone mount onedrive: /home/datos/Quantica --vfs-cache-mode full --dir-cache-time 5m --daemon
```

Comprobar que se ve el contenido:

```bash
ls -la /home/datos/Quantica
```

Si ves las carpetas (OP_TECH_DATOS..., etc.), el montaje está bien. Si no, revisa el nombre del remoto (`rclone listremotes`) y la ruta usada (`onedrive:NombreCarpeta` o `onedrive:`).

Para desmontar (cuando quieras dejar de usarlo):

```bash
fusermount -uz /home/datos/Quantica
```

---

## Paso 5: Montar al arrancar el servidor (servicio systemd)

Así OneDrive queda montado al iniciar el servidor y la app siempre tendrá la ruta disponible.

### 5.1 Copiar el archivo de servicio

En el proyecto hay un archivo de ejemplo:

```text
scripts/systemd/rclone-onedrive.service
```

En el servidor, cópialo a systemd (ajusta la ruta del proyecto si es distinta):

```bash
sudo cp /home/datos/SERVICIO-DESCARGAS-MOP-DGA/scripts/systemd/rclone-onedrive.service /etc/systemd/system/
```

### 5.2 Ajustar el servicio (si hace falta)

Edita el servicio si tu remoto o ruta no son los por defecto:

```bash
sudo nano /etc/systemd/system/rclone-onedrive.service
```

- **Remoto:** si no se llama `onedrive`, cambia en `ExecStart` el nombre del remoto.
- **Ruta en OneDrive:** si usas la raíz del OneDrive en vez de una carpeta "Quantica", deja `onedrive:` (con espacio o sin nada después de los dos puntos, según sintaxis de rclone).
- **Usuario:** si el usuario no es `datos`, cambia `User=datos` por el usuario que ejecuta la app.
- **Ruta local:** si quieres montar en otra ruta, cambia `/home/datos/Quantica` en `ExecStart` y en `ExecStop`.

Guarda (Ctrl+O, Enter, Ctrl+X).

### 5.3 Activar e iniciar el servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable rclone-onedrive
sudo systemctl start rclone-onedrive
```

Comprobar estado:

```bash
sudo systemctl status rclone-onedrive
```

Debería estar **active (running)**. Ver de nuevo el contenido:

```bash
ls -la /home/datos/Quantica
```

---

## Paso 6: Verificar que la app ve las rutas

1. Arranca la app (por ejemplo con `./scripts/start_servicio.sh`).
2. Inicia una descarga (lista P5 u otra con pocos pozos).
3. En la salida de Flask deberías ver algo como:

   ```text
   DEBUG shared_root: /home/datos/Quantica
   DEBUG base_dirs:
    - .../2366 - CASUB_Soporte P12 exists? True
    - .../2253 - COFANTI DGA 5 POZOS exists? True
   ```

   Si **exists? True**, la app puede mover los archivos ahí. Si **exists? False**, la estructura en OneDrive no coincide con `BASE_DEST_DIRS_REL` de `config.json`; revisa nombres de carpetas en la nube y en el config.

4. Tras la descarga, comprueba en el servidor que el .xls esté en la subcarpeta correspondiente bajo `/home/datos/Quantica/...` y en OneDrive (en el navegador o en la app de OneDrive).

---

## Resumen de comandos (Opción B – rclone)

| Acción | Comando |
|--------|--------|
| Instalar | `sudo apt install rclone` |
| Configurar remoto | `rclone config` |
| Listar remotos | `rclone listremotes` |
| Listar carpetas en OneDrive | `rclone lsd onedrive:` o `rclone lsd onedrive:Quantica` |
| Montar (prueba) | `rclone mount onedrive:Quantica /home/datos/Quantica --vfs-cache-mode full --dir-cache-time 5m --daemon` |
| Desmontar | `fusermount -uz /home/datos/Quantica` |
| Activar servicio | `sudo systemctl enable --now rclone-onedrive` |
| Ver estado | `sudo systemctl status rclone-onedrive` |

Cuando el montaje esté activo y las rutas coincidan con `config.json`, la app descargará del MOP y dejará los archivos en las carpetas compartidas de OneDrive para todos los usuarios.
