# TIR+ — Calculadora Inteligente de Tasa Interna de Retorno

Proyecto de la materia **Sistemas Económicos** (Ing. de Sistemas, UMSS) —
Unidad 7, Análisis de la Tasa de Rendimiento.

Resuelve problemas de VAN/TIR (simples, mixtos y de análisis incremental
entre alternativas) a partir de **texto, una foto del enunciado o un
boceto dibujado a mano**. Ollama ejecuta un modelo de visión local que lee el problema y arma la
tabla de flujos de caja; todo el cálculo matemático (VAN, TIR, regla de
signos de Descartes, análisis incremental) lo hace Python puro con
NumPy/SciPy — así la IA nunca "inventa" un número final.

---

## 1. Arquitectura del proyecto

```
tir_calculator/
├── app.py                # Flask: rutas / API REST
├── solver.py              # Motor matemático: VAN, TIR, incremental, gráficos
├── ollama_service.py       # Integración con Ollama local (lee imagen/texto -> JSON)
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
`Imagen/Texto/Canvas → Ollama local (extrae flujos de caja en JSON) → el usuario
revisa/edita los montos → solver.py calcula VAN/TIR con NumPy/SciPy →
la interfaz muestra fundamento teórico + pasos + respuesta final + gráficos`.

---

## 2. Requisitos previos

1. **Python 3.11 o 3.12** instalado (`python3 --version` en una terminal).
2. **Visual Studio Code** con la extensión oficial **Python** (de Microsoft) instalada.
3. **Ollama para Windows** y espacio para descargar un modelo de visión de aproximadamente 3.2 GB.
4. Conexión a internet para instalar Ollama, descargar el modelo y cargar las fuentes/CDN del frontend.

---

## 3. Instalar Ollama y descargar el modelo

1. Descarga e instala Ollama desde **https://ollama.com/download/windows**.
2. Abre una terminal nueva de VS Code y descarga el modelo de visión:

   ```powershell
   ollama pull qwen2.5vl:3b
   ```

El modelo se ejecuta en tu computadora: no necesita API key, cuenta de proveedor,
tarjeta de crédito ni cobra por consulta. El tamaño descargado del modelo es
aproximadamente 3.2 GB. El rendimiento dependerá de la memoria y velocidad de tu PC.
Una vez instalado, puedes hacer más de 30 consultas; no hay una cuota por petición,
pero cada consulta consume recursos de tu computadora.

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

### Edita el archivo `.env` (opcional)

Ollama funciona con estos valores predeterminados, así que no necesitas una clave
ni modificar `.env`. Si deseas configurar el servidor o el modelo, usa:

```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5vl:3b
```

**Nunca subas el archivo `.env` a GitHub** (ya está excluido en `.gitignore`).

---

## 6. Ejecutar el proyecto localmente

Abre Ollama desde el menú Inicio y déjalo ejecutándose. Confirma que el modelo
está disponible con `ollama list`. Después, con el entorno virtual activado
(deberías ver `(venv)` al inicio de la línea de la terminal):

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
| No se pudo conectar con Ollama en `localhost:11434` | Ollama no está abierto | Abre Ollama desde el menú Inicio; si no está instalado, instálalo desde ollama.com |
| Ollama responde que no encuentra el modelo | El modelo no se descargó | Ejecuta `ollama pull qwen2.5vl:3b` y vuelve a probar |
| Ollama tarda mucho o Windows se queda sin memoria | El modelo es pesado para el equipo o la primera carga tarda | Cierra aplicaciones, prueba solo con texto o usa un equipo con más memoria |
| Error 422 "No se pudo interpretar la respuesta de la IA" | La imagen es borrosa o el enunciado es ambiguo | Prueba con mejor luz/enfoque, o edita los datos extraídos manualmente en la pestaña Solución |
| `OSError: [Errno 98] Address already in use` | El puerto 5000 ya está ocupado | Cierra el proceso anterior o cambia el puerto en la última línea de `app.py` (`port=5001`) |
| La página carga pero los gráficos no aparecen | Sin conexión a internet (Chart.js se carga desde un CDN) | Verifica tu conexión; el proyecto necesita acceso a `cdnjs.cloudflare.com` |

---

## 9. Uso local y despliegue

Esta versión usa Ollama en `localhost:11434`. Por eso funciona cuando Flask y
Ollama están ejecutándose en la misma computadora. Un despliegue en Render,
Vercel o PythonAnywhere no puede acceder al Ollama de tu PC usando `localhost`;
para publicar el sitio se necesitaría instalar y ejecutar el modelo en el mismo
servidor o conectar otra API alojada. Esa alternativa podría tener cuotas o
requerir facturación, así que no forma parte del modo local sin tarjeta.

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
- **¿Qué pasa si Ollama interpreta mal una imagen?** El usuario revisa y
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
