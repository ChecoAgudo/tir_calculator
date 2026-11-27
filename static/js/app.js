// ============================================================
// app.js — lógica del frontend de TIR+
// ============================================================

// ---------- Estado global ----------
let ultimoAnalisis = null;   // JSON devuelto por /api/analizar (editable)
let chartFlujo = null;
let chartVan = null;

// ============================================================
// 1. Navegación por pestañas
// ============================================================
const tabButtons = document.querySelectorAll(".tab-btn");
const tabPanels = document.querySelectorAll(".tab-panel");

function irA(nombreTab) {
  tabButtons.forEach(b => b.classList.toggle("is-active", b.dataset.tab === nombreTab));
  tabPanels.forEach(p => p.classList.toggle("is-active", p.id === `tab-${nombreTab}`));
}

tabButtons.forEach(btn => btn.addEventListener("click", () => irA(btn.dataset.tab)));
document.getElementById("btn-comenzar").addEventListener("click", () => irA("resolucion"));

// ============================================================
// 2. Subida de imagen (preview)
// ============================================================
const inputImagen = document.getElementById("input-imagen");
const previewImagen = document.getElementById("preview-imagen");
const fileDropLabel = document.getElementById("file-drop-label");

inputImagen.addEventListener("change", () => {
  const archivo = inputImagen.files[0];
  if (!archivo) return;
  fileDropLabel.textContent = archivo.name;
  const lector = new FileReader();
  lector.onload = e => {
    previewImagen.src = e.target.result;
    previewImagen.hidden = false;
  };
  lector.readAsDataURL(archivo);
});

// ============================================================
// 3. Canvas de entrada manuscrita
// ============================================================
const canvas = document.getElementById("canvas-dibujo");
const ctx = canvas.getContext("2d");
let dibujando = false;

function posicionRelativa(evt) {
  const rect = canvas.getBoundingClientRect();
  const escalaX = canvas.width / rect.width;
  const escalaY = canvas.height / rect.height;
  const punto = evt.touches ? evt.touches[0] : evt;
  return {
    x: (punto.clientX - rect.left) * escalaX,
    y: (punto.clientY - rect.top) * escalaY,
  };
}

function iniciarTrazo(evt) {
  dibujando = true;
  const { x, y } = posicionRelativa(evt);
  ctx.beginPath();
  ctx.moveTo(x, y);
  evt.preventDefault();
}
function continuarTrazo(evt) {
  if (!dibujando) return;
  const { x, y } = posicionRelativa(evt);
  ctx.lineWidth = 2;
  ctx.lineCap = "round";
  ctx.strokeStyle = "#0B1F3A";
  ctx.lineTo(x, y);
  ctx.stroke();
  evt.preventDefault();
}
function terminarTrazo() { dibujando = false; }

["mousedown", "touchstart"].forEach(ev => canvas.addEventListener(ev, iniciarTrazo));
["mousemove", "touchmove"].forEach(ev => canvas.addEventListener(ev, continuarTrazo));
["mouseup", "mouseleave", "touchend"].forEach(ev => canvas.addEventListener(ev, terminarTrazo));

document.getElementById("btn-limpiar-canvas").addEventListener("click", () => {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
});

function canvasTieneDibujo() {
  const datos = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  for (let i = 3; i < datos.length; i += 4) {
    if (datos[i] !== 0) return true;
  }
  return false;
}

// ============================================================
// 4. Analizar problema (texto + imagen y/o canvas -> Gemini)
// ============================================================
const btnAnalizar = document.getElementById("btn-analizar");
const analizarError = document.getElementById("analizar-error");

btnAnalizar.addEventListener("click", async () => {
  analizarError.hidden = true;
  const texto = document.getElementById("input-texto").value.trim();
  const archivoImagen = inputImagen.files[0];
  const hayDibujo = canvasTieneDibujo();

  if (!texto && !archivoImagen && !hayDibujo) {
    mostrarError(analizarError, "Escribe un enunciado, sube una imagen o dibuja el problema antes de analizar.");
    return;
  }

  btnAnalizar.disabled = true;
  btnAnalizar.textContent = "Analizando con IA...";

  try {
    const formData = new FormData();
    if (texto) formData.append("texto", texto);

    if (archivoImagen) {
      formData.append("imagen", archivoImagen);
    } else if (hayDibujo) {
      const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/png"));
      formData.append("imagen", blob, "boceto.png");
    }

    const resp = await fetch("/api/analizar", { method: "POST", body: formData });
    const datos = await resp.json();

    if (!resp.ok) {
      mostrarError(analizarError, datos.error || "No se pudo analizar el problema.");
      return;
    }

    ultimoAnalisis = datos;
    renderDatosExtraidos(datos);
    irA("solucion");
  } catch (err) {
    mostrarError(analizarError, "Error de conexión con el servidor: " + err.message);
  } finally {
    btnAnalizar.disabled = false;
    btnAnalizar.textContent = "Analizar problema con IA";
  }
});

function mostrarError(el, mensaje) {
  el.textContent = mensaje;
  el.hidden = false;
}

// ============================================================
// 5. Mostrar datos extraídos (editables) antes de resolver
// ============================================================
const contenedorDatos = document.getElementById("datos-extraidos");
const filaResolver = document.getElementById("fila-resolver");

function renderDatosExtraidos(datos) {
  const tmarManual = document.getElementById("input-tmar").value;
  const tmar = datos.tmar ?? (tmarManual ? parseFloat(tmarManual) / 100 : null);

  let html = `<p><strong>Resumen:</strong> ${datos.enunciado_resumen || "—"}</p>`;
  html += `<p><span class="badge">${datos.tipo_analisis === "incremental" ? "Análisis incremental" : "Análisis simple"}</span>`;
  if (tmar !== null) html += ` <span class="badge">TMAR: ${(tmar * 100).toFixed(2)} %</span>`;
  html += `</p>`;

  datos.proyectos.forEach((proy, idxProy) => {
    html += `<h3>Proyecto ${proy.nombre}</h3>`;
    html += `<table class="datos-tabla"><thead><tr><th>Periodo</th><th>Monto</th></tr></thead><tbody>`;
    proy.flujos.forEach((monto, t) => {
      html += `<tr><td>${t}</td><td><input type="number" step="0.01" data-proy="${idxProy}" data-t="${t}" value="${monto}"></td></tr>`;
    });
    html += `</tbody></table>`;
  });

  contenedorDatos.innerHTML = html;
  filaResolver.hidden = false;

  // sincroniza ediciones manuales con el objeto ultimoAnalisis
  contenedorDatos.querySelectorAll("input[data-proy]").forEach(inp => {
    inp.addEventListener("change", () => {
      const p = parseInt(inp.dataset.proy, 10);
      const t = parseInt(inp.dataset.t, 10);
      ultimoAnalisis.proyectos[p].flujos[t] = parseFloat(inp.value) || 0;
    });
  });

  if (tmar !== null) ultimoAnalisis.tmar = tmar;
}

// ============================================================
// 6. Resolver (llama a /api/resolver con los datos confirmados)
// ============================================================
document.getElementById("btn-resolver").addEventListener("click", async () => {
  if (!ultimoAnalisis) return;
  const btn = document.getElementById("btn-resolver");
  btn.disabled = true;
  btn.textContent = "Resolviendo...";

  try {
    const resp = await fetch("/api/resolver", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(ultimoAnalisis),
    });
    const resultado = await resp.json();

    if (!resp.ok) {
      renderErrorSolucion(resultado.error || "No se pudo resolver el problema.");
      return;
    }

    renderSolucion(resultado);
    renderGraficos(resultado);
  } catch (err) {
    renderErrorSolucion("Error de conexión: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Resolver con estos datos";
  }
});

const contenedorSolucion = document.getElementById("solucion-detallada");

function renderErrorSolucion(mensaje) {
  contenedorSolucion.innerHTML = `<p class="error-msg" style="margin:0">${mensaje}</p>`;
}

function renderSolucion(resultado) {
  let html = `<h3>Fundamento teórico</h3><p>${resultado.fundamento_teorico}</p>`;

  if (resultado.tipo_analisis === "incremental") {
    resultado.proyectos.forEach(p => {
      html += `<h3>Proyecto ${p.nombre}</h3>`;
      html += `<p><span class="badge ${p.clasificacion.cambios_signo > 1 ? 'badge--mixta' : ''}">${p.clasificacion.tipo}</span> `;
      html += `TIR: ${p.tir.length ? p.tir.map(t => (t * 100).toFixed(2) + "%").join(", ") : "N/D"}</p>`;
    });
    html += `<h3>Desarrollo del análisis incremental</h3>`;
    resultado.pasos_incremental.forEach(paso => {
      html += `<div class="paso"><h4>${paso.titulo}</h4><p>${paso.contenido}</p></div>`;
    });
  } else {
    html += `<h3>Clasificación de la inversión</h3>`;
    html += `<p><span class="badge ${resultado.clasificacion.cambios_signo > 1 ? 'badge--mixta' : ''}">${resultado.clasificacion.tipo}</span></p>`;
    html += `<p>${resultado.clasificacion.explicacion}</p>`;
    html += `<h3>Desarrollo paso a paso</h3>`;
    resultado.pasos.forEach(paso => {
      html += `<div class="paso"><h4>${paso.titulo}</h4><p>${paso.contenido}</p></div>`;
    });
  }

  html += `<div class="respuesta-final">${resultado.respuesta_final}</div>`;
  contenedorSolucion.innerHTML = html;
}

// ============================================================
// 7. Gráficos (Chart.js)
// ============================================================
function renderGraficos(resultado) {
  document.getElementById("graficos-empty").hidden = true;

  let flujoCaja, curvaVan;
  if (resultado.tipo_analisis === "incremental") {
    flujoCaja = resultado.proyectos[0].grafico_flujo;
    curvaVan = resultado.proyectos[0].grafico_van;
  } else {
    flujoCaja = resultado.graficos.flujo_caja;
    curvaVan = resultado.graficos.curva_van;
  }

  const ctxFlujo = document.getElementById("chart-flujo").getContext("2d");
  if (chartFlujo) chartFlujo.destroy();
  chartFlujo = new Chart(ctxFlujo, {
    type: "bar",
    data: {
      labels: flujoCaja.map(d => `t${d.periodo}`),
      datasets: [{
        label: "Monto",
        data: flujoCaja.map(d => d.monto),
        backgroundColor: flujoCaja.map(d => d.monto < 0 ? "#C23B3B" : "#2F6FED"),
        borderRadius: 4,
      }],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });

  const ctxVan = document.getElementById("chart-van").getContext("2d");
  if (chartVan) chartVan.destroy();
  chartVan = new Chart(ctxVan, {
    type: "line",
    data: {
      labels: curvaVan.map(d => (d.tasa * 100).toFixed(0) + "%"),
      datasets: [{
        label: "VAN",
        data: curvaVan.map(d => d.van),
        borderColor: "#2F6FED",
        backgroundColor: "rgba(47,111,237,0.12)",
        fill: true,
        pointRadius: 0,
        tension: 0.15,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { x: { ticks: { maxTicksLimit: 10 } } },
    },
  });
}
