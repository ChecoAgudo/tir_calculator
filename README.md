# TIR+ — Calculadora Inteligente de Tasa Interna de Retorno

Proyecto de la materia **Sistemas Económicos** (Ing. de Sistemas, UMSS) —
Unidad 7, Análisis de la Tasa de Rendimiento.

Resuelve problemas de VAN/TIR (simples, mixtos y de análisis incremental
entre alternativas) a partir de **texto, una foto del enunciado o un
boceto dibujado a mano**. Groq lee el problema y arma la
tabla de flujos de caja; todo el cálculo matemático (VAN, TIR, regla de
signos de Descartes, análisis incremental) lo hace Python puro con
NumPy/SciPy — así la IA nunca "inventa" un número final.

---

## 1. Arquitectura del proyecto

```
tir_calculator/
├── app.py                # Flask: rutas / API REST
├── solver.py              # Motor matemático: VAN, TIR, incremental, gráficos
├── groq_service.py          # Integración con Groq (lee imagen/texto -> JSON)
├── config.py               # Lee variables de entorno (.env)
├── requirements.txt
├── .env.example             # Plantilla de variables de entorno
├── templates/index.html      # Interfaz (Inicio / Resolución / Solución / Gráficos)
├── static/css/style.css       # Paleta azul / blanco / azul marino
├── static/js/app.js            # Pestañas, canvas manuscrito, llamadas a la API, Chart.js
├── api/index.py                  # Adaptador para desplegar en Vercel
├── vercel.json, render.yaml, Procfile   # Archivos de despliegue
```

**Flujo de datos:**
`Imagen/Texto/Canvas → Groq (extrae flujos de caja en JSON) → el usuario
revisa/edita los montos → solver.py calcula VAN/TIR con NumPy/SciPy →
la interfaz muestra fundamento teórico + pasos + respuesta final + gráficos`.

---

## 2. Requisitos previos

1. **Python 3.11 o 3.12** instalado (`python3 --version` en una terminal).
2. **Visual Studio Code** con la extensión oficial **Python** (de Microsoft) instalada.
3. Una **API Key de Groq** creada en https://console.groq.com/keys.
4. Conexión a internet para Groq y para cargar las fuentes/CDN del frontend.

---

## 3. Obtener y configurar tu API Key de Groq

1. Entra a **https://console.groq.com/keys** y crea una API key.
2. Copia la clave y guárdala únicamente en el archivo `.env` local; no la pegues
   en el código, GitHub, capturas ni mensajes.
3. El proyecto usa `qwen/qwen3.8-27b`, compatible con texto, imágenes y salida
   JSON según la [documentación de visión de Groq](https://console.groq.com/docs/vision).

> **Importante sobre el costo:** que la cuenta muestre créditos gratuitos no
> garantiza que cada modelo o cada consulta sea gratuita. La documentación
> actual de Groq lista precio por tokens para este modelo y lo marca como
> Preview. Revisa Usage, Limits y Billing en tu consola antes de usarlo; los
> créditos, límites y acceso dependen de tu cuenta.

---

## 4. Descomprimir y abrir el proyecto en VS Code

1. Descomprime el archivo `.zip` del proyecto en una carpeta, por ejemplo:
   `C:\Users\TuUsuario\Documents\tir_calculator` (Windows) o
   `~/Documents/tir_calculator` (Mac/Linux).
2. Abre **VS Code** → `Archivo > Abrir Carpeta...` → selecciona `tir_calculator`.
3. Abre una terminal integrada: menú **Terminal > Nueva Terminal** (o `Ctrl + ñ` / `` Ctrl+` ``).

---

## 5. Instalación paso a paso (entorno virtual + dependencias)

Ejecuta estos comandos **uno por uno** en la terminal integrada de VS Code:

### Windows (PowerShell)
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

> Si VS Code pregunta "¿Quieres usar este entorno (venv) para el proyecto?",
> responde **Sí** — así el intérprete de Python que usa VS Code coincide con
> el que tiene las dependencias instaladas. Si no te pregunta, selecciónalo
> manualmente: `Ctrl+Shift+P` → "Python: Select Interpreter" → elige el que
> dice `./venv/bin/python` (o `.\venv\Scripts\python.exe` en Windows).

### Edita el archivo `.env`

Abre el archivo `.env` que se acaba de crear y configura:

```
GROQ_API_KEY=tu_clave_real_de_groq
GROQ_MODEL=qwen/qwen3.8-27b
FLASK_SECRET_KEY=cualquier-texto-aleatorio-largo
```

Si ya existe `.env`, edítalo y reemplaza las variables antiguas por estas; no
copies ni publiques la clave en otro lugar. **Nunca subas `.env` a GitHub**
(está excluido en `.gitignore`).

---

## 6. Ejecutar el proyecto localmente

Con el entorno virtual activado (deberías ver `(venv)` al inicio de la línea de la terminal):

```bash
python app.py
```

Deberías ver algo como:

```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

Abre tu navegador en **http://localhost:5000** — ahí verás la interfaz de TIR+.

Para detener el servidor: `Ctrl + C` en la terminal.

---

## 7. Cómo probar que todo funciona (con los mismos ejercicios del libro)

1. Ve a la pestaña **Resolución**.
2. En el cuadro de texto pega, por ejemplo, el **ejercicio 7.a** de tu imagen:
   > "Proyecto A: periodo 0 = -1000, periodo 1 = 1000, periodo 2 = 250.
   > TMAR 10%. Calcule la TIR usando la ecuación cuadrática."
3. Clic en **"Analizar problema con IA"**. Pasarás automáticamente a la pestaña **Solución**,
   donde verás la tabla de flujos extraída (puedes corregir cualquier monto a mano).
4. Clic en **"Resolver con estos datos"**: deberías obtener **TIR ≈ 20.71 %**,
   clasificado como inversión **simple (pura)** (ya verificado contra el motor matemático).
5. Ve a la pestaña **Gráficos** para ver el diagrama de flujo de caja y la curva VAN vs. tasa.
6. Para el **ejercicio 2** de la práctica 08 (imagen "06.jpg"), el libro indica
   **0.88 % mensual** — el motor de este proyecto llega a ≈0.87-0.88 % mensual,
   consistente con el libro.

Si subes una **foto** en vez de texto, el flujo es el mismo: sube la imagen en
la tarjeta "2. Adjuntar imagen" y presiona "Analizar problema con IA". Lo
mismo con el **canvas**: dibuja el diagrama de flujo de caja y presiona el botón.

---

## 8. Solución de problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ModuleNotFoundError: No module named 'flask'` | El entorno virtual no está activado | Vuelve a correr `source venv/bin/activate` (o el de Windows) antes de `python app.py` |
| Error 422 "No se configuró GROQ_API_KEY" | Falta `.env` o la clave está vacía | Confirma el nombre `.env` y configura `GROQ_API_KEY`; reinicia Flask después de editarlo |
| Groq devuelve 401 | Clave incorrecta, revocada o no cargada | Crea/revisa la clave en Groq Console y confirma que no tenga espacios extra |
| Groq devuelve 403 o indica que el modelo no está disponible | El modelo no está habilitado para la cuenta | Revisa acceso al modelo y la configuración de tu cuenta en Groq Console |
| Groq devuelve 403 con `error code: 1010` | El filtro de tráfico de Groq/Cloudflare bloqueó la firma del cliente HTTP; no suele ser un error de clave | Usa la integración con el SDK oficial incluida en este proyecto; actualiza dependencias y reinicia. Si sigue, prueba sin VPN/proxy o consulta a soporte de Groq |
| Groq devuelve 429 | Se alcanzó un límite o la cuota/créditos disponibles | Revisa Usage, Limits y Billing; espera al reinicio del límite o utiliza un modelo habilitado |
| Error 422 "No se pudo interpretar la respuesta de la IA" | La imagen es borrosa o el enunciado es ambiguo | Prueba con mejor luz/enfoque, o edita los datos extraídos manualmente en la pestaña Solución |
| `OSError: [Errno 98] Address already in use` | El puerto 5000 ya está ocupado | Cierra el proceso anterior o cambia el puerto en la última línea de `app.py` (`port=5001`) |
| La página carga pero los gráficos no aparecen | Sin conexión a internet (Chart.js se carga desde un CDN) | Verifica tu conexión; el proyecto necesita acceso a `cdnjs.cloudflare.com` |

---

## 9. Desplegar en producción

### Opción recomendada: Render (más simple y estable para Flask)

1. Sube el proyecto a un repositorio de **GitHub** (crea el repo y haz `git push`).
2. Entra a **https://render.com** → **New + → Web Service** → conecta tu repositorio.
3. Render detectará automáticamente `render.yaml`. Si te pide confirmarlo manualmente:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. En la sección **Environment**, agrega las variables:
   - `GROQ_API_KEY` = tu clave real (configúrala como variable secreta)
   - `GROQ_MODEL` = `qwen/qwen3.8-27b`
5. Clic en **Create Web Service**. Render te dará una URL pública (`https://tir-calculadora.onrender.com`).

### Opción: PythonAnywhere

1. Crea una cuenta gratuita en **https://www.pythonanywhere.com**.
2. Sube el proyecto: pestaña **Files** → sube el `.zip` y descomprímelo
   (o usa `git clone` desde una consola Bash de PythonAnywhere).
3. Pestaña **Consoles → Bash**:
   ```bash
   cd tir_calculator
   mkvirtualenv --python=python3.11 tir-venv
   pip install -r requirements.txt
   ```
4. Pestaña **Web → Add a new web app → Manual configuration → Python 3.11**.
5. En **Virtualenv**, apunta a la ruta de `tir-venv` (ej. `/home/tu_usuario/.virtualenvs/tir-venv`).
6. Edita el archivo **WSGI configuration file** que te da PythonAnywhere y reemplázalo por:
   ```python
   import sys, os
   path = '/home/tu_usuario/tir_calculator'
   if path not in sys.path:
       sys.path.insert(0, path)
   os.environ['GROQ_API_KEY'] = 'tu_clave_real_de_groq'
   os.environ['GROQ_MODEL'] = 'qwen/qwen3.8-27b'
   from app import app as application
   ```
7. Clic en **Reload** en la pestaña Web. Tu app quedará en `https://tu_usuario.pythonanywhere.com`.

### Opción: Vercel (serverless — más limitada para este tipo de app)

Vercel ejecuta Python como **funciones serverless** (sin servidor persistente),
lo cual funciona para esta app porque cada request es independiente, pero con
límites de tiempo de ejecución más estrictos que Render/PythonAnywhere.

1. Instala la CLI: `npm install -g vercel`.
2. Desde la carpeta del proyecto: `vercel login` y luego `vercel`.
3. Sigue las instrucciones en pantalla (el archivo `vercel.json` ya está configurado
   para enrutar todo hacia `api/index.py`, que reexporta la app Flask).
4. Configura las variables de entorno en el dashboard de Vercel
   (**Settings → Environment Variables**): `GROQ_API_KEY`, `GROQ_MODEL`.
5. `vercel --prod` para publicar la versión final.

---

## 10. 🛡️ Notas para la defensa técnica

- **¿Por qué no se usa `numpy_financial.irr` como único método?** Porque solo
  devuelve una raíz; el libro exige detectar **TIR múltiple** en inversiones
  mixtas (ejercicio 7), así que `solver.py` resuelve el polinomio completo
  con `numpy.roots` y filtra raíces reales positivas.
- **¿Cómo se decide la mejor alternativa cuando el flujo incremental es
  mixto (varias TIR posibles)?** Comparar "la" TIR contra la TMAR deja de ser
  confiable ahí (el propio libro lo advierte en 7.4.1), así que la decisión
  se toma con el **signo del VAN evaluado en la TMAR**, que es matemáticamente
  equivalente y siempre válido.
- **¿Qué pasa si Groq interpreta mal una imagen?** El usuario revisa y
  corrige los montos extraídos en la pestaña "Solución" antes de resolver;
  la IA nunca hace el cálculo final, solo arma la tabla de flujos.
- **Casos borde manejados:** división por cero evitada en `(1+i)^t`, flujos
  sin raíz real positiva (`"no tiene TIR real"`), discriminante negativo en
  el caso cuadrático, y proyectos con distinto número de periodos (se
  rellenan con 0 antes del análisis incremental).

---

## 11. Posibles extensiones futuras

- Exportar la solución paso a paso a PDF.
- Guardar un historial de problemas resueltos (requeriría base de datos).
- Soporte para VAUE (Valor Anual Uniforme Equivalente) y TER (Tasa Externa de Retorno).
