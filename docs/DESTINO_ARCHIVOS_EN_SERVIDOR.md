# Destino de los archivos descargados (carpeta en el servidor)

Los archivos descargados desde el portal MOP se guardan **solo en el servidor**, en una carpeta local. No se usa OneDrive ni sincronización con la nube. Un script externo se encargará de leer esa carpeta y subir la información a una base de datos.

---

## Cómo funciona

1. **Descarga:** La app descarga los .xls en `~/Downloads/<lista>` (por ejemplo `~/Downloads/P5`).
2. **Movimiento:** Si en `data/config.json` están definidas las rutas destino y **existen en el servidor**, la app mueve cada archivo a la carpeta que corresponda según el pozo y el año.
3. **Destino final:** Esa carpeta es **local en el servidor** (por ejemplo `$HOME/Quantica/...` o la estructura que definas). Ahí quedan los archivos para que el script que sube a la base de datos los procese.

---

## Configuración en `data/config.json`

- **`SHARED_ROOT_NAME`**: nombre de la carpeta raíz bajo el home del usuario que ejecuta la app.  
  Ejemplo: `"Quantica"` → ruta real: `$HOME/Quantica` (en el servidor, p. ej. `/home/ubuntu/Quantica`).

- **`BASE_DEST_DIRS_REL`**: rutas relativas a esa raíz donde se organizan los archivos por proyecto/lista (P12, P17, P22, P5, etc.). La app busca dentro de cada una la subcarpeta del pozo (según `data/instalacion_cod_obra_titular_Pxx.txt`) y guarda el archivo en `<carpeta_pozo>/<año>/`.

Para que los archivos **se muevan** (y no se queden solo en `~/Downloads/<lista>`), esa estructura de carpetas debe **existir en el servidor**. Puedes crearla a mano o con un script, por ejemplo:

```bash
mkdir -p ~/Quantica/OP_TECH_DATOS\ -\ General/2026/2036\ -\ 2253\ -\ Q\ INTERNO\ TELEMETRIA/...
```

(o la estructura que tengas en `BASE_DEST_DIRS_REL`).

---

## Si no existe la estructura destino

Si las rutas de `SHARED_ROOT_NAME` + `BASE_DEST_DIRS_REL` **no existen** en el servidor, la app **no mueve** los archivos: permanecen en `~/Downloads/<lista>` (por ejemplo `/home/ubuntu/Downloads/P5`). El script que sube a la base de datos puede leer desde esa carpeta si lo prefieres.

---

## Resumen

| Objetivo | Qué hacer |
|----------|-----------|
| Archivos en una carpeta local con estructura por pozo/año | Crear en el servidor la estructura que define `config.json` (bajo `$HOME/<SHARED_ROOT_NAME>/<BASE_DEST_DIRS_REL>/...`). |
| Archivos solo en `~/Downloads/<lista>` | No crear esa estructura; la app dejará los .xls en `~/Downloads/P5`, `~/Downloads/P12`, etc. |
| Script que sube a BD | Debe leer desde la carpeta donde la app deja los archivos (ruta destino si existe, o `~/Downloads/<lista>`). |

OneDrive y rclone ya no forman parte del flujo; el destino es únicamente una carpeta dentro del servidor.
