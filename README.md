# TIR+ — Calculadora de Tasa Interna de Retorno

Aplicación académica para resolver ejercicios de VAN y TIR ingresando
manualmente flujos de caja por periodo. El cálculo se ejecuta localmente en
Python y no requiere una API, una clave de IA ni el envío de datos a un modelo.

## Funcionalidades

- TIR de un proyecto, incluyendo la búsqueda de raíces reales múltiples.
- Desarrollo de la ecuación del VAN y pasos de resolución.
- Cálculo del VAN a una TMAR opcional y evaluación de conveniencia.
- Comparación incremental de dos o más alternativas con una TMAR.
- Gráficos de los flujos y de la curva VAN/tasa.
- Periodos y alternativas añadibles desde la interfaz, sin un máximo fijo de proyectos.
- Asistentes para registrar una inversión, repetir ingresos/costos en un rango de periodos
  y sumar un valor de salvamento o venta al periodo final.
- Gráficos dibujados en el navegador, sin CDN ni conexión a internet durante el uso.

El periodo 0 suele ser una inversión negativa. Los ingresos se ingresan positivos
y los costos negativos. El asistente de flujos repetidos puede reemplazar el flujo
de un rango o sumarse a los valores existentes cuando coinciden varios conceptos
en un periodo. El asistente de salvamento suma el valor ingresado al último periodo.
La tabla siempre muestra el flujo final que usará el motor. También se puede editar
cualquier celda directamente. Las tasas se interpretan en la unidad de los periodos
(por ejemplo, periodos mensuales producen una TIR mensual).
El selector permite indicar años o meses: al trabajar con meses, la TIR también
se muestra como tasa efectiva anual equivalente y la TMAR ingresada como anual
se convierte a su equivalente mensual. Si solo se conoce una TMAR por periodo,
selecciona «Otra / no especificada» para ingresarla directamente.

La aplicación no interpreta enunciados, imágenes ni fórmulas simbólicas: esos
datos deben traducirse a flujos numéricos. Para inversiones, beneficios uniformes
y salvamento se pueden usar los asistentes, sin sumar esos conceptos fuera de la
aplicación. Si el enunciado requiere cálculos financieros previos no implementados
(por ejemplo, determinar el importe de una cuota o de impuestos), se debe calcular
ese importe o ingresarlo como un flujo de periodo; el motor resuelve VAN/TIR y la
comparación incremental localmente.

## Requisitos

- Python 3.11 o superior.
- No se necesita conexión a internet para ejecutar la aplicación ni ver los gráficos.

## Instalación y ejecución

### Windows (PowerShell)

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abre <http://localhost:5000> para usar la aplicación.

## Uso

1. Selecciona TIR individual o comparación incremental. En modo incremental
   aparecen dos alternativas; usa «Agregar alternativa» para añadir más.
2. Usa el asistente de inversión para escribir el monto positivo; la aplicación
   lo registra negativo en el periodo 0.
3. Para un beneficio o costo repetido, especifica los periodos inicial y final
   y el monto por periodo. Usa «Reemplazar» para llenar el rango o «Sumar» cuando
   deseas combinarlo con un flujo ya ingresado.
4. Si hay salvamento o venta, escribe su valor en el asistente correspondiente.
   Se suma al flujo del último periodo; no lo vuelvas a incluir en la tabla.
5. Ingresa directamente en la tabla los flujos que varían entre periodos. Usa
   «Agregar periodo» o «Quitar último periodo» para ajustar la duración. Todas
   las alternativas mantienen el mismo número de periodos.
6. Introduce la TMAR como porcentaje (por ejemplo, `13` para 13%). Es obligatoria
   para el análisis incremental. Con periodos en meses se interpreta como tasa
   anual y se convierte automáticamente a mensual.
7. Pulsa «Resolver ejercicio» para consultar los pasos, el resultado y los
   gráficos.

## Ejemplo

Para una inversión de 1000, un beneficio de 1000 en el periodo 1 y otro de 250
en el periodo 2, aplica una inversión inicial de `1000` y registra los flujos
restantes en la tabla. La solución es aproximadamente `20.71 %` por periodo.
Si la TMAR es 10 %, el VAN a esa TMAR permite evaluar la conveniencia.

## Pruebas

```bash
python -m unittest discover -s tests
```

## Despliegue

La aplicación no requiere variables de entorno ni claves de proveedores externos.
El archivo `.python-version` fija Python 3.12 para mantener compatibilidad con
NumPy 1.26.4.

### Render — opción recomendada para un despliegue gratuito

El repositorio incluye `render.yaml` con el plan gratuito, el comando de
instalación y el comando de inicio.

1. Sube el proyecto a un repositorio de GitHub. Comprueba que `render.yaml`,
   `.python-version` y `requirements.txt` estén en la raíz.
2. Crea una cuenta en Render y conecta GitHub.
3. En el Dashboard selecciona **New → Blueprint** y elige este repositorio y
   la rama que quieras desplegar.
4. Render leerá `render.yaml`. Revisa que el servicio `tir-calculadora` muestre
   el plan **Free** y confirma la aplicación del Blueprint.
5. Espera a que el despliegue termine y abre la URL `.onrender.com` que Render
   muestra para el servicio.
6. Comprueba la página principal y visita `/api/salud`; debe responder
   `{"estado":"ok"}`.

Si el nombre `tir-calculadora` ya está ocupado en Render, cambia `name` en
`render.yaml`, sube el cambio y vuelve a aplicar el Blueprint. También puedes
crear un **Web Service** manualmente usando:

- Root Directory: `.`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Instance Type: **Free**

Los servicios gratuitos de Render se duermen después de 15 minutos sin tráfico
y el siguiente acceso puede tardar alrededor de un minuto en iniciar. El sistema
de archivos del servicio no es persistente; esta aplicación no guarda ejercicios
ni necesita una base de datos. El plan gratuito tiene límites de uso que Render
puede actualizar.

### Vercel

El proyecto ya incluye `vercel.json`, `api/index.py` y `.python-version`. La
configuración enruta la aplicación Flask a una función Python y sirve los
archivos de `static/`.

1. Sube el proyecto a GitHub, incluyendo `vercel.json`, `api/index.py`,
   `templates/`, `static/`, `requirements.txt` y `.python-version`.
2. Inicia sesión en Vercel y selecciona **Add New → Project**.
3. Importa el repositorio de GitHub y confirma que **Root Directory** sea la
   raíz del repositorio.
4. Deja que Vercel use `vercel.json`; no establezcas un Output Directory ni
   reemplaces la configuración de builds/rutas del proyecto.
5. Comprueba que el framework sea **Other** si Vercel solicita elegir uno.
   No agregues variables de entorno: la aplicación no las necesita.
6. Pulsa **Deploy**. Cuando termine, abre la URL que Vercel asigna y prueba
   también `/api/salud`.

Cada `push` a la rama conectada genera un nuevo despliegue. También puedes
importar el repositorio desde la CLI de Vercel. Si la página carga sin estilos,
revisa los logs y confirma que el directorio raíz y el `vercel.json` incluidos
en el despliegue son los de este proyecto.

El plan Hobby de Vercel aparece actualmente como $0/mes en su [página de
precios](https://vercel.com/pricing); revisa allí las condiciones y límites
vigentes. Vercel ejecuta Flask como una función serverless, mientras que Render
mantiene un servicio web que puede dormir cuando está inactivo. Para este
proyecto, Render suele ser el camino más directo porque el repositorio ya
contiene un Blueprint gratuito configurado.
