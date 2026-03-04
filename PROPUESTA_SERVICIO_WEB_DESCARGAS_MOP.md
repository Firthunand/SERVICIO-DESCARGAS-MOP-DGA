# PROPUESTA DE SOLUCIÓN
## Servicio Web de Descarga de Reportes MOP DGA

---

## 1. RESUMEN EJECUTIVO

El objetivo de este proyecto es transformar el script actual de automatización con Selenium, utilizado para descargar y organizar reportes Excel desde el portal SNIA MOP DGA, en una **aplicación web accesible para usuarios no técnicos** desde cualquier navegador, sin necesidad de instalación de software adicional.

La solución propuesta se basa en un **backend en Python con Flask** y una interfaz web con **templates HTML + Bootstrap**, permitiendo a los usuarios seleccionar una lista predefinida de pozos y un periodo de fechas, lanzar la descarga y **visualizar el estado en tiempo real** de la ejecución.

La lógica actual de negocio (descarga, renombrado y movimiento de archivos a la estructura de carpetas del cliente) se reutiliza, encapsulándola en un servicio web ejecutado en un **servidor en la nube**. El usuario final resolverá el CAPTCHA requerido por el portal MOP directamente desde la interfaz web mediante un navegador remoto embebido, sin necesidad de conocimientos técnicos.

Los archivos descargados se organizan automáticamente en la estructura de carpetas de OneDrive de la empresa, manteniendo la lógica de organización existente basada en códigos de obra y periodos.

---

## 2. OBJETIVO DEL SISTEMA

### 2.1 Objetivo Principal

Facilitar a usuarios no técnicos la descarga y organización de reportes de mediciones desde el portal SNIA MOP DGA, mediante una interfaz web simple que oculte la complejidad técnica del proceso actual.

### 2.2 Objetivos Específicos

- Eliminar la necesidad de editar archivos de configuración o ejecutar scripts manualmente.
- Estandarizar el flujo de descarga y renombrado de archivos Excel.
- Mostrar de forma clara el **progreso y estado** de la descarga actual (sin mantener un historial complejo).
- Permitir el acceso a la herramienta desde **múltiples usuarios** vía navegador web, sin necesidad de login ni instalación de software.
- Facilitar la resolución del CAPTCHA del portal MOP directamente desde la interfaz web, sin requerir acceso técnico al servidor.

---

## 3. ALCANCE Y SUPUESTOS

### 3.1 Alcance Funcional

- Selección de una **lista predefinida de pozos** (ej.: P12, P17, P22).
- Selección de **periodo de fechas** (inicio y fin).
- Inicio del proceso de descarga automatizada.
- Visualización del **avance y estado** de la descarga actual por pozo.
- Organización automática de los archivos descargados en la estructura de carpetas de OneDrive de la empresa.
- Resolución del CAPTCHA del portal MOP directamente desde la interfaz web mediante navegador remoto embebido.

### 3.2 Fuera de Alcance (Versión 1)

- Gestión de usuarios o autenticación (no hay login).
- Administración de listas de pozos por parte del usuario final (las listas P12/P17/P22 son definidas por el área técnica).
- Historial de ejecuciones a largo plazo (solo se muestra el estado de la **ejecución actual**).
- Resolución automática del CAPTCHA (se mantiene resolución humana, pero facilitada desde la interfaz web).

### 3.3 Supuestos

- El servidor en la nube dispone de entorno gráfico o mecanismo adecuado para ejecutar Chrome/Selenium y exponer la sesión de navegador al usuario final mediante un navegador remoto embebido (por ejemplo, mediante tecnologías como noVNC, Guacamole o similar).
- El **usuario final no técnico**, accediendo desde su navegador web, puede visualizar la página del portal SNIA MOP y **resolver el CAPTCHA directamente** cuando la aplicación se lo solicite, sin necesidad de acceso técnico al servidor.
- La estructura de carpetas destino en OneDrive ya existe o puede configurarse a partir de la lógica actual (`BASE_DEST_DIRS_REL`, `SHARED_ROOT_NAME`, etc.).
- El servidor en la nube tiene acceso configurado a OneDrive de la empresa (mediante sincronización local de OneDrive o API de Microsoft Graph, según la estrategia técnica elegida).
- Los archivos descargados se procesan y organizan en el servidor antes de ser movidos a OneDrive.

---

## 4. FLUJOS DE USUARIO

### 4.1 Flujo Principal: "Nueva Descarga"

**Actor**: Usuario no técnico.

**Pasos**:

1. El usuario accede a la URL de la aplicación web desde su navegador (ej.: `https://servidor-empresa.com/mop-descargas`).

2. La página principal muestra un formulario con:
   - Selector de **lista de pozos** (P12, P17, P22).
   - Campos de **fecha desde** y **fecha hasta**.
   - Botón **"Iniciar descarga"**.

3. El usuario selecciona la lista y el periodo y pulsa **"Iniciar descarga"**.

4. El sistema valida que:
   - No exista otra ejecución en curso.
   - Las fechas sean válidas.

5. El sistema crea una **ejecución de descarga** y lanza el proceso de automatización con Selenium en el servidor.

6. Se redirige al usuario a la pantalla de **"Estado de la descarga actual"**.

### 4.2 Flujo: "Estado de la Descarga Actual"

**Actor**: Cualquier usuario que accede mientras hay una ejecución en curso.

**Pasos**:

1. Si hay una descarga en curso, cualquier usuario que entre a la aplicación ve directamente la pantalla de **estado**.

2. La pantalla muestra:
   - **Resumen**: Lista seleccionada, periodo, hora de inicio.
   - **Instrucciones sobre CAPTCHA**: Mensaje explicando que se abrirá un navegador remoto embebido donde el usuario debe resolver el CAPTCHA del portal MOP.
   - **Navegador remoto embebido**: Ventana integrada en la página web que muestra la sesión de Chrome ejecutándose en el servidor, permitiendo al usuario interactuar directamente con el portal MOP para resolver el CAPTCHA.
   - **Barra de progreso**: Porcentaje completado y "X de N pozos procesados".
   - **Tabla de detalle**: Estado por pozo con:
     - Pendiente.
     - En proceso.
     - Completado y movido a carpeta OneDrive.
     - Error (no encontrado en MOP, carpeta destino inexistente, timeout de descarga, etc.).

3. El usuario resuelve el CAPTCHA directamente en el navegador remoto embebido.

4. Una vez resuelto el CAPTCHA, el proceso continúa automáticamente para todos los pozos.

5. Al finalizar el proceso, la pantalla muestra:
   - Mensaje de éxito si todos los pozos fueron procesados correctamente.
   - O bien mensaje de finalización con advertencias, en caso de errores parciales.

### 4.3 Flujo: "Ejecución Ya en Curso"

**Actor**: Usuario que intenta iniciar una nueva descarga mientras hay otra activa.

**Pasos**:

1. El usuario intenta iniciar una nueva descarga mientras ya hay una ejecución activa.

2. El sistema muestra un mensaje indicando que existe una descarga en curso.

3. Se ofrece un botón para **ver el estado de la descarga actual**.

4. De esta forma se evita lanzar procesos concurrentes que compitan por el navegador y las descargas.

---

## 5. MAQUETAS DE INTERFAZ DE USUARIO

### 5.1 Pantalla "Inicio / Nueva Descarga"

**Objetivo**: Permitir que un usuario no técnico pueda lanzar una descarga sin confundirse.

**Elementos principales**:

- **Header**:
  - Título: **"Descarga de reportes MOP – Telemetría"**
  - Texto pequeño: "Herramienta para descargar y organizar automáticamente los reportes Excel desde el portal SNIA MOP."

- **Bloque principal (formulario)**:
  - **Campo 1: Lista de pozos**
    - Etiqueta: "Lista de pozos".
    - Selector desplegable:
      - `P12 - Pozos de cliente X`
      - `P17 - Pozos de cliente Y`
      - `P22 - Pozos de cliente Z`
    - Texto de ayuda: "Las listas están predefinidas por el área técnica."

  - **Campo 2: Periodo**
    - Dos date-pickers (o inputs de fecha con máscara):
      - "Desde" (ej: 01-01-2025).
      - "Hasta" (ej: 31-01-2025).
    - Texto de ayuda corto: "El periodo se usa para buscar las mediciones en el portal MOP."

  - **Botón principal**:
    - Botón grande centrado: **"Iniciar descarga"**.
    - Debajo, una nota:
      - "Se abrirá un navegador remoto integrado en esta página para que resuelvas el CAPTCHA. Luego la descarga continuará automáticamente."

- **Bloque secundario (si hay ejecución en curso)**:
  - Una tarjeta visible solo si `estado == en_curso`:
    - Título: "Descarga en curso".
    - Texto: "Hay una descarga activa. Puedes ver su avance aquí."
    - Botón: **"Ver estado de la descarga actual"**.

### 5.2 Pantalla "Estado de la Descarga Actual"

**Objetivo**: Mostrar de forma clara el avance y facilitar la resolución del CAPTCHA.

**Elementos principales**:

- **Header**:
  - Título: "Estado de la descarga actual".
  - Subtítulo: "No cierres esta página mientras la descarga esté en curso."

- **Resumen de la ejecución**:
  - "Lista: P12"
  - "Periodo: 01-01-2025 a 31-01-2025"
  - "Hora de inicio: 10:32"

- **Sección CAPTCHA con Navegador Remoto Embebido**:
  - Bloque informativo tipo alerta:
    - Título: "Paso obligatorio: CAPTCHA del MOP"
    - Texto:
      - "A continuación verás el portal SNIA MOP en un navegador remoto integrado."
      - "Resuelve el CAPTCHA directamente en la ventana de abajo."
      - "Cuando termines, la descarga continuará automáticamente para todos los pozos."
  - **Ventana de navegador remoto embebido**:
    - Área grande (ej: 80% del ancho de la pantalla, altura ajustable) que muestra la sesión de Chrome ejecutándose en el servidor.
    - El usuario puede interactuar con esta ventana como si fuera un navegador normal: hacer clic, escribir, resolver el CAPTCHA.
    - La ventana se actualiza en tiempo real mostrando el progreso de la automatización.

- **Progreso global**:
  - Barra de progreso:
    - "Procesando 3 de 12 pozos".
  - Texto debajo:
    - "Este proceso puede tomar varios minutos dependiendo de la cantidad de pozos y la velocidad del portal MOP."

- **Tabla de detalle por pozo**:
  - Columnas:
    - Código OB.
    - Estado.
    - Mensaje.
  - Ejemplos de filas:
    - `OB-0302-127 | Completado | Archivo guardado en OneDrive/.../CASUB-216/2025/02. Reporte Febrero OB-0302-127.xls`
    - `OB-0302-418 | Error | No se encontró carpeta destino; archivo quedó en la carpeta de descargas del servidor.`
    - `OB-0302-999 | Pendiente | A la espera de turno para descarga.`

- **Estado final**:
  - Cuando termina:
    - Mensaje verde si todos OK:
      - "La descarga ha finalizado correctamente para los 12 pozos."
    - Mensaje amarillo si hubo errores:
      - "La descarga ha finalizado con advertencias. Revisa la columna 'Estado' para más detalle."
    - (Opcional) Botón: "Descargar log técnico" (archivo .txt).

---

## 6. ARQUITECTURA TÉCNICA PROPUESTA

### 6.1 Componentes Principales

#### 6.1.1 Backend (Flask)

- **Responsabilidades**:
  - Proporcionar rutas web para las pantallas principales:
    - Ruta `/` para la pantalla de "Nueva descarga".
    - Ruta `/estado` para la pantalla de "Estado de la descarga actual".
  - Exponer endpoints internos para:
    - Iniciar una nueva ejecución de descarga (`POST /api/iniciar-descarga`).
    - Consultar el estado actual (`GET /api/estado-actual`), devolviendo JSON para actualización en tiempo real.
  - Renderizar templates HTML con **Bootstrap** para un diseño limpio y responsive.

#### 6.1.2 Motor de Automatización (Selenium + Lógica Actual)

- **Responsabilidades**:
  - Reutilizar el código ya desarrollado:
    - Manejo de Chrome y Selenium.
    - Navegación al portal MOP DGA.
    - Espera y verificación de resolución de CAPTCHA.
    - Descarga de archivos Excel, renombrado y movimiento a carpetas destino.
  - Ejecutarse en el servidor, con Chrome corriendo en modo headful (con interfaz gráfica) para permitir la visualización remota.
  - Encapsularse en una función o clase que:
    - Recibe parámetros de periodo y lista de pozos.
    - Reporta el avance y los estados individuales de cada pozo a un "gestor de ejecuciones".

#### 6.1.3 Servidor de Navegador Remoto (noVNC / Guacamole / Similar)

- **Responsabilidades**:
  - Exponer la sesión gráfica de Chrome ejecutándose en el servidor mediante un protocolo de escritorio remoto (VNC/WebRTC).
  - Integrarse en la interfaz web mediante un componente embebido (iframe o widget) que permita al usuario interactuar con el navegador remoto directamente desde su navegador.
  - Garantizar que el usuario pueda resolver el CAPTCHA sin necesidad de acceso técnico al servidor.

#### 6.1.4 Gestor de Ejecuciones (Job Manager)

- **Responsabilidades**:
  - Mantener información de la **ejecución actual**:
    - Parámetros (lista, fechas).
    - Progreso global (N total, N procesados).
    - Estado por pozo (OK / error / pendiente).
  - En una primera versión, puede operar en **memoria** (en el proceso de la aplicación) sin necesidad de una base de datos compleja, dado que no se requiere historial persistente.
  - Si se requiere robustez adicional (por ejemplo, recuperación ante caídas del servidor), puede migrarse a una base de datos simple (SQLite o PostgreSQL).

#### 6.1.5 Integración con OneDrive

- **Responsabilidades**:
  - Mover los archivos descargados desde la carpeta temporal del servidor a la estructura de carpetas de OneDrive de la empresa.
  - Opciones técnicas:
    - **Opción A**: OneDrive Sync instalado en el servidor, moviendo archivos a la carpeta sincronizada localmente.
    - **Opción B**: Microsoft Graph API para subir archivos directamente a OneDrive.
  - La elección dependerá de la configuración de seguridad y acceso de la empresa.

### 6.2 Flujo Técnico de Ejecución

1. Usuario accede a la aplicación web desde su navegador.
2. Usuario completa el formulario y pulsa "Iniciar descarga".
3. Flask recibe la solicitud y crea una nueva ejecución en el Job Manager.
4. Flask lanza el proceso de automatización Selenium en un hilo o proceso separado.
5. Selenium abre Chrome en el servidor (modo headful) y navega al portal MOP.
6. El servidor de navegador remoto expone la sesión de Chrome al usuario mediante VNC/WebRTC.
7. El usuario ve el navegador remoto embebido en la página web y resuelve el CAPTCHA.
8. Selenium detecta que el CAPTCHA fue resuelto y continúa con la automatización.
9. Para cada pozo:
   - Selenium busca la obra, navega a "Mediciones", completa fechas y exporta a Excel.
   - El archivo se descarga en el servidor.
   - Se renombra según el formato estándar.
   - Se mueve a la estructura de carpetas de OneDrive.
   - El Job Manager actualiza el estado de ese pozo.
10. Flask expone el estado actualizado mediante el endpoint `/api/estado-actual`.
11. La interfaz web actualiza la vista en tiempo real (mediante polling o WebSockets, según la implementación elegida).

### 6.3 Despliegue en Servidor en la Nube

- La aplicación Flask se desplegará en un **servidor en la nube** (Windows o Linux) con:
  - Python + dependencias (Flask, Selenium, etc.).
  - Navegador Chrome (u otro compatible) y driver correspondiente.
  - Servidor VNC o similar para exponer la sesión gráfica del navegador.
  - Acceso configurado a OneDrive de la empresa (mediante sincronización local o API).
- El servidor actuará como **punto central** al que se conectan los usuarios vía navegador.
- No se requiere instalación de software en los PCs de los usuarios finales.

---

## 7. PLAN DE IMPLEMENTACIÓN (ALTO NIVEL)

### Fase 1: Diseño Detallado y Preparación del Entorno

- Validar con el cliente los flujos y maquetas propuestas.
- Preparar entorno en la nube (servidor, instalación de dependencias, configuración básica de Selenium y Chrome).
- Configurar acceso a OneDrive (sincronización local o API).
- Evaluar e instalar solución de navegador remoto (noVNC, Guacamole u otra).

### Fase 2: Construcción de la Aplicación Flask

- Definir estructura del proyecto (rutas, templates, estáticos).
- Implementar la pantalla "Nueva descarga" y la pantalla "Estado de la descarga actual" (sin lógica todavía).
- Integrar Bootstrap para el diseño responsive.

### Fase 3: Integración con el Motor de Automatización

- Encapsular el script actual en una función/servicio reutilizable.
- Integrar el disparo de la ejecución desde Flask.
- Implementar el reporte de estado al "Job Manager".
- Configurar el servidor de navegador remoto para exponer la sesión de Chrome.

### Fase 4: Integración con OneDrive

- Implementar la lógica de movimiento de archivos a OneDrive (según la opción técnica elegida).
- Validar que la estructura de carpetas se mantiene correctamente.

### Fase 5: Pruebas y Ajustes

- Pruebas end-to-end con las listas P5, P12, P17, P22.
- Validar la experiencia del usuario con el navegador remoto embebido.
- Ajustes de mensajes, tiempos de espera y manejo de errores.
- Documentación básica de uso para el usuario final.

---

## 8. CONSIDERACIONES TÉCNICAS ADICIONALES

### 8.1 Seguridad

- La aplicación no requiere autenticación en V1, pero debe considerarse para futuras versiones si se requiere control de acceso.
- El acceso al servidor de navegador remoto debe estar protegido (por ejemplo, mediante tokens o autenticación básica).

### 8.2 Rendimiento

- El proceso de descarga puede ser lento dependiendo de la cantidad de pozos y la velocidad del portal MOP.
- Se recomienda implementar timeouts adecuados y manejo de errores robusto.
- La actualización del estado en tiempo real puede realizarse mediante polling (cada X segundos) o WebSockets para una experiencia más fluida.

### 8.3 Escalabilidad

- En V1, solo se permite una ejecución concurrente para evitar conflictos con el navegador y las descargas.
- Si en el futuro se requiere soportar múltiples ejecuciones simultáneas, será necesario implementar un sistema de colas (por ejemplo, Celery) y múltiples instancias de navegadores.

---

## 9. CONCLUSIÓN

Esta propuesta transforma el script actual de automatización en una solución web accesible para usuarios no técnicos, manteniendo la lógica de negocio existente y mejorando significativamente la experiencia de usuario mediante una interfaz web intuitiva y un mecanismo de navegador remoto embebido para la resolución del CAPTCHA.

La solución es pragmática, reutiliza el código ya desarrollado y puede implementarse de forma incremental, permitiendo validar cada fase antes de avanzar a la siguiente.

---

**Versión del documento**: 1.0  
**Fecha**: Diciembre 2025

