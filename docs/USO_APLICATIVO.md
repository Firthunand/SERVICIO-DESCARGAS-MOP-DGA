# Guía de uso – Descarga de reportes MOP (Telemetría)

Esta guía está dirigida al usuario que utiliza la aplicación desde el navegador para descargar reportes desde el portal MOP DGA.

---

## 1. Cómo acceder

- Abre el navegador (Chrome, Edge, Firefox, etc.).
- Escribe la dirección que te haya indicado el administrador (por ejemplo: `http://<IP-del-servidor>:5000`).
- Pulsa Enter.

Si ves el mensaje **“Sesión en uso”** significa que otra persona está usando la aplicación en ese momento. Solo puede haber **una sesión activa**. Debes esperar a que esa persona cierre la pestaña o finalice; en unos segundos podrás pulsar **“Reintentar”** para comprobar si la sesión está libre.

---

## 2. Iniciar una descarga

1. **Lista de pozos**  
   Elige la lista que corresponda (P5, P12, P17 o P22). Las listas están definidas por el área técnica.

2. **Desde / Hasta**  
   Indica el **periodo** de fechas para el que quieres los reportes (fecha de inicio y fecha de fin). El sistema usará ese rango para buscar en el portal MOP.

3. **Iniciar descarga**  
   Pulsa el botón azul **“Iniciar descarga”**.  
   - La página se actualizará y verás la sección **“Estado de la descarga actual”** y la tabla con los pozos.  
   - En la parte inferior aparecerá el **“Navegador remoto (CAPTCHA)”**.

---

## 3. Resolver el CAPTCHA

El portal MOP pide que resuelvas un CAPTCHA para continuar.

- En la **misma página**, en la sección **“Navegador remoto (CAPTCHA)”**, verás una ventana con la pantalla del portal MOP.
- **Resuelve el CAPTCHA** directamente en esa ventana (marca la casilla o completa lo que pida la imagen).
- Si no ves bien la zona del CAPTCHA, usa la **barra de desplazamiento** del recuadro para bajar o mover la vista.
- Cuando lo resuelvas, la descarga **continuará sola** para todos los pozos de la lista; no hace falta que hagas nada más en el CAPTCHA.

**Importante:** No cierres esta pestaña mientras la descarga esté en curso. Si cierras, la sesión quedará libre para otro usuario y tu descarga se interrumpirá.

---

## 4. Estado de la descarga

En **“Estado de la descarga actual”** se muestra:

- **Lista:** La lista que elegiste (P5, P12, etc.).
- **Periodo:** Las fechas Desde–Hasta que configuraste.
- **Estado:** Puede ser:
  - **idle** – No hay descarga en curso.
  - **en_curso** – La descarga está ejecutándose.
  - **finalizado** – La descarga terminó con normalidad.
  - **cancelado** – La descarga se detuvo (por ejemplo porque pulsaste “Detener descarga”).
- **Carpeta en el servidor:** Ruta donde se guardan los archivos en el servidor (visible cuando hay o hubo una descarga).

La **tabla** debajo muestra, por cada pozo (código OB):

| Columna   | Significado                                                                 |
|----------|-----------------------------------------------------------------------------|
| Código OB| Identificador del pozo.                                                     |
| Estado   | **Pendiente** – Aún no se procesa. **En proceso** – Se está descargando. **OK** – Completado. **Error** – Falló (ver mensaje). |
| Mensaje  | Detalle del resultado (por ejemplo “Movido a …” o un texto de error).      |

La tabla se actualiza sola cada pocos segundos.

---

## 5. Detener la descarga

Si quieres **parar** la descarga antes de que termine:

- Pulsa el botón rojo **“Detener descarga”** (solo aparece cuando el estado es **en_curso**).
- La aplicación dejará de procesar más pozos, cerrará el navegador automático y el estado pasará a **cancelado**.
- Los archivos que ya se hayan descargado **no se borran**; solo se detiene el resto del proceso.

---

## 6. Dónde quedan los archivos

- Los archivos se guardan **en el servidor**, en la carpeta que se indica en **“Carpeta en el servidor”** (por ejemplo una ruta como `.../Downloads/P5` u otra configurada por el administrador).
- Un script o proceso aparte se encarga de leer esa carpeta y subir la información a la base de datos; no tienes que copiar los archivos manualmente desde la aplicación.

---

## 7. Resumen rápido

| Acción              | Qué hacer                                                                 |
|---------------------|---------------------------------------------------------------------------|
| Entrar a la app     | Abrir en el navegador la URL que te dieron (ej. `http://...:5000`).      |
| Si dice “Sesión en uso” | Esperar y pulsar “Reintentar” hasta que la sesión esté libre.        |
| Iniciar descarga    | Elegir lista, fechas Desde/Hasta y pulsar “Iniciar descarga”.            |
| Resolver CAPTCHA    | Hacerlo en la ventana “Navegador remoto (CAPTCHA)” de la misma página.  |
| Ver avance          | Revisar la tabla y el estado (se actualizan solos).                     |
| Parar la descarga   | Pulsar “Detener descarga” mientras el estado sea “en_curso”.             |

Si tienes problemas (por ejemplo la descarga no avanza o no ves el CAPTCHA), contacta al responsable técnico o al administrador del servidor.
