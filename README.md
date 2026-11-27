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
- Periodos y alternativas añadibles desde la interfaz.

Los flujos deben ingresarse como montos netos por periodo. Cuando un problema
incluya costos, ingresos, gradientes, impuestos o valor de salvamento, calcula
el flujo neto de cada periodo y suma los conceptos que coincidan en ese periodo
antes de ingresarlos. El periodo 0 suele ser una inversión negativa. Las tasas
se interpretan en la unidad de los periodos proporcionados (por ejemplo,
periodos mensuales producen una TIR mensual).

La aplicación no interpreta enunciados, imágenes ni fórmulas simbólicas: esos
datos deben traducirse a flujos numéricos en la tabla. El cálculo de VAN/TIR y
la comparación entre alternativas sí se hacen en el servidor local.

## Requisitos

- Python 3.11 o superior.
- Para mostrar gráficos, conexión a internet para cargar Chart.js desde CDN.
  La resolución numérica no depende de la conexión ni de ese servicio.

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

1. Selecciona TIR individual o comparación incremental.
2. Introduce el flujo neto para cada periodo, empezando en el periodo 0.
   Usa «Agregar periodo» cuando el ejercicio tenga más periodos.
3. Si corresponde, introduce la TMAR como porcentaje (por ejemplo, `13` para
   13%). El análisis incremental requiere una TMAR.
4. En modo incremental, agrega una alternativa por proyecto y usa periodos
   consistentes. Completa los flujos faltantes con cero cuando una alternativa
   dure menos periodos.
5. Pulsa «Resolver ejercicio» para consultar los pasos, el resultado y los
   gráficos.

## Ejemplo

Para los flujos `-1000`, `1000`, `250` en los periodos 0, 1 y 2, respectivamente,
la solución es aproximadamente `20.71 %` por periodo. Si la TMAR es 10 %, el
VAN a esa TMAR permite evaluar la conveniencia de la inversión.

## Pruebas

```bash
python -m unittest discover -s tests
```

## Despliegue

La aplicación es compatible con los archivos de despliegue incluidos para
Render, Vercel y Gunicorn. No se requieren variables de entorno ni claves de
proveedores externos.
