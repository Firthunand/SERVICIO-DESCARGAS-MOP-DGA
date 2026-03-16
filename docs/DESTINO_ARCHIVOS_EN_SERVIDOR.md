# Destino de los archivos descargados (carpeta en el servidor)

Los archivos descargados desde el portal MOP se guardan **solo en el servidor**, en una carpeta local bajo `/opt/quantica`. No se usa OneDrive ni sincronización con la nube. Un script externo se encargará de leer esas carpetas y subir la información a una base de datos.

---

## Cómo funciona

1. **Descarga inicial:** La app descarga los `.xls` en `~/Downloads/<lista>` (por ejemplo `~/Downloads/P5`, `~/Downloads/P12`, etc.).
2. **Movimiento por lista:** Si en `data/config.json` están definidas las rutas destino (`BASE_DEST_DIRS`) y **existen en el servidor**, la app mueve cada archivo a la carpeta que corresponda según la **lista** (P5, P12, P17 o P22) y el **año** del periodo consultado.
3. **Destino final:** La carpeta final es local en el servidor, con la forma:
   - P12 → `/opt/quantica/EXTRACCIONES MOP/2366 - CASUB_Soporte P12/<año>/`
   - P17 → `/opt/quantica/EXTRACCIONES MOP/2368 - CASUB_Soporte P17/<año>/`
   - P22 → `/opt/quantica/EXTRACCIONES MOP/2367 - CASUB_Soporte P22/<año>/`
   - P5  → `/opt/quantica/EXTRACCIONES MOP/2253 - COFANTI DGA 5 POZOS/<año>/`

Ahí quedan los archivos para que el script que sube a la base de datos los procese.

---

## Configuración en `data/config.json`

La configuración relevante es:

```json
"BASE_DEST_DIRS": [
  "/opt/quantica/EXTRACCIONES MOP/2366 - CASUB_Soporte P12",
  "/opt/quantica/EXTRACCIONES MOP/2368 - CASUB_Soporte P17",
  "/opt/quantica/EXTRACCIONES MOP/2367 - CASUB_Soporte P22",
  "/opt/quantica/EXTRACCIONES MOP/2253 - COFANTI DGA 5 POZOS"
]
```

- Cada entrada de `BASE_DEST_DIRS` debe existir físicamente en el servidor y ser propiedad del usuario que ejecuta el servicio (por ejemplo `ubuntu`).  
  Ejemplo de creación:

```bash
sudo mkdir -p "/opt/quantica/EXTRACCIONES MOP/2366 - CASUB_Soporte P12"
sudo mkdir -p "/opt/quantica/EXTRACCIONES MOP/2368 - CASUB_Soporte P17"
sudo mkdir -p "/opt/quantica/EXTRACCIONES MOP/2367 - CASUB_Soporte P22"
sudo mkdir -p "/opt/quantica/EXTRACCIONES MOP/2253 - COFANTI DGA 5 POZOS"
sudo chown -R ubuntu:ubuntu /opt/quantica
```

> Nota: Los campos `SHARED_ROOT_NAME` y `BASE_DEST_DIRS_REL` se mantienen por compatibilidad, pero el flujo actual usa `BASE_DEST_DIRS` con rutas absolutas en `/opt/quantica`.

---

## Si no existe la estructura destino

Si las rutas de `BASE_DEST_DIRS` **no existen** en el servidor, la app **no mueve** los archivos: permanecen en `~/Downloads/<lista>` (por ejemplo `/home/ubuntu/Downloads/P5`). El script que sube a la base de datos puede leer desde esa carpeta si se prefiere.

---

## Resumen

| Objetivo | Qué hacer |
|----------|-----------|
| Archivos en carpetas por lista/año bajo `/opt/quantica` | Definir `BASE_DEST_DIRS` en `data/config.json` con las rutas absolutas en `/opt/quantica/EXTRACCIONES MOP/...` y crear esas carpetas en el servidor. |
| Archivos solo en `~/Downloads/<lista>` | No definir/crear `BASE_DEST_DIRS`; la app dejará los `.xls` en `~/Downloads/P5`, `~/Downloads/P12`, etc. |
| Script que sube a BD | Debe leer desde la carpeta donde la app deja los archivos (ruta destino en `/opt/quantica/...` si existe, o `~/Downloads/<lista>`). |

OneDrive y rclone ya no forman parte del flujo; el destino es únicamente una o varias carpetas dentro del servidor.*** End Patch```} */}
