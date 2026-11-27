// ============================================================
// app.js — ingreso manual y presentación de soluciones de TIR+
// ============================================================

let chartFlujo = null;
let chartVan = null;
let proyectos = [{ nombre: "Proyecto A", flujos: ["", ""] }];

const tabButtons = document.querySelectorAll(".tab-btn");
const tabPanels = document.querySelectorAll(".tab-panel");
const tipoAnalisis = document.getElementById("tipo-analisis");
const inputTmar = document.getElementById("input-tmar");
const listaProyectos = document.getElementById("proyectos-entrada");
const btnAgregarProyecto = document.getElementById("btn-agregar-proyecto");
const btnResolver = document.getElementById("btn-resolver");
const errorEntrada = document.getElementById("analizar-error");
const contenedorDatos = document.getElementById("datos-extraidos");
const contenedorSolucion = document.getElementById("solucion-detallada");

function irA(nombreTab) {
  tabButtons.forEach(b => b.classList.toggle("is-active", b.dataset.tab === nombreTab));
  tabPanels.forEach(p => p.classList.toggle("is-active", p.id === `tab-${nombreTab}`));
}

tabButtons.forEach(btn => btn.addEventListener("click", () => irA(btn.dataset.tab)));
document.getElementById("btn-comenzar").addEventListener("click", () => irA("resolucion"));

function escaparHtml(valor) {
  return String(valor).replace(/[&<>"']/g, caracter => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[caracter]);
}

function renderProyectos() {
  const periodos = proyectos[0].flujos.length;
  listaProyectos.innerHTML = proyectos.map((proyecto, indice) => `
    <article class="project-card" data-project="${indice}">
      <div class="project-heading">
        <label>
          <span>Nombre de la alternativa</span>
          <input type="text" data-project-name="${indice}" value="${escaparHtml(proyecto.nombre)}" maxlength="60">
        </label>
        ${indice > 0 ? `<button class="btn btn--ghost btn--remove" data-remove-project="${indice}" type="button">Quitar</button>` : ""}
      </div>
      <div class="table-scroll">
        <table class="datos-tabla">
          <thead><tr><th>Periodo</th>${Array.from({ length: periodos }, (_, periodo) =>
            `<th>${periodo === 0 ? "0 (inicial)" : periodo}</th>`).join("")}</tr></thead>
          <tbody><tr><th>Flujo neto</th>${proyecto.flujos.map((monto, periodo) => `
            <td><input type="number" step="any" data-project="${indice}" data-period="${periodo}"
              aria-label="${escaparHtml(proyecto.nombre)}, periodo ${periodo}"
              placeholder="${periodo === 0 ? "Ej. -1000" : "Ej. 500"}" value="${escaparHtml(monto)}"></td>
          `).join("")}</tr></tbody>
        </table>
      </div>
    </article>
  `).join("");
  btnAgregarProyecto.hidden = tipoAnalisis.value !== "incremental";
}

tipoAnalisis.addEventListener("change", () => {
  proyectos = proyectos.slice(0, 1);
  if (tipoAnalisis.value === "incremental") {
    proyectos.push({ nombre: "Proyecto B", flujos: proyectos[0].flujos.map(() => "") });
  }
  renderProyectos();
});

document.getElementById("btn-agregar-periodo").addEventListener("click", () => {
  proyectos.forEach(proyecto => proyecto.flujos.push(""));
  renderProyectos();
});

btnAgregarProyecto.addEventListener("click", () => {
  const letra = String.fromCharCode(65 + proyectos.length);
  proyectos.push({ nombre: `Proyecto ${letra}`, flujos: proyectos[0].flujos.map(() => "") });
  renderProyectos();
});

listaProyectos.addEventListener("input", evento => {
  const campoNombre = evento.target.closest("[data-project-name]");
  if (campoNombre) {
    proyectos[Number(campoNombre.dataset.projectName)].nombre = campoNombre.value;
    return;
  }
  const campoFlujo = evento.target.closest("[data-project][data-period]");
  if (campoFlujo) {
    proyectos[Number(campoFlujo.dataset.project)].flujos[Number(campoFlujo.dataset.period)] = campoFlujo.value;
  }
});

listaProyectos.addEventListener("click", evento => {
  const boton = evento.target.closest("[data-remove-project]");
  if (!boton) return;
  proyectos.splice(Number(boton.dataset.removeProject), 1);
  renderProyectos();
});

function mostrarError(elemento, mensaje) {
  elemento.textContent = mensaje;
  elemento.hidden = false;
}

function obtenerDatosEntrada() {
  const proyectosNormalizados = proyectos.map((proyecto, indice) => {
    const nombre = proyecto.nombre.trim() || `Proyecto ${indice + 1}`;
    const flujos = proyecto.flujos.map((monto, periodo) => {
      if (String(monto).trim() === "") {
        throw new Error(`Ingresa el flujo del periodo ${periodo} en ${nombre}.`);
      }
      const valor = Number(monto);
      if (!Number.isFinite(valor)) {
        throw new Error(`El flujo del periodo ${periodo} en ${nombre} no es válido.`);
      }
      return valor;
    });
    return { nombre, flujos };
  });

  const tmarTexto = inputTmar.value.trim();
  const tmar = tmarTexto === "" ? null : Number(tmarTexto) / 100;
  if (tmar !== null && !Number.isFinite(tmar)) {
    throw new Error("Ingresa un porcentaje TMAR válido.");
  }

  return {
    tipo_analisis: tipoAnalisis.value,
    tmar,
    proyectos: proyectosNormalizados,
  };
}

btnResolver.addEventListener("click", async () => {
  errorEntrada.hidden = true;
  let datos;
  try {
    datos = obtenerDatosEntrada();
  } catch (error) {
    mostrarError(errorEntrada, error.message);
    return;
  }

  btnResolver.disabled = true;
  btnResolver.textContent = "Resolviendo...";
  try {
    const respuesta = await fetch("/api/resolver", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos),
    });
    const resultado = await respuesta.json();
    if (!respuesta.ok) {
      mostrarError(errorEntrada, resultado.error || "No se pudo resolver el ejercicio.");
      return;
    }

    renderDatos(datos);
    renderSolucion(resultado);
    renderGraficos(resultado);
    irA("solucion");
  } catch (error) {
    mostrarError(errorEntrada, `Error de conexión con el servidor: ${error.message}`);
  } finally {
    btnResolver.disabled = false;
    btnResolver.textContent = "Resolver ejercicio";
  }
});

function renderDatos(datos) {
  const proyectosHtml = datos.proyectos.map(proyecto => `
    <h3>${escaparHtml(proyecto.nombre)}</h3>
    <div class="table-scroll"><table class="datos-tabla">
      <thead><tr><th>Periodo</th>${proyecto.flujos.map((_, periodo) =>
        `<th>${periodo}</th>`).join("")}</tr></thead>
      <tbody><tr><th>Flujo neto</th>${proyecto.flujos.map(monto =>
        `<td>${escaparHtml(monto)}</td>`).join("")}</tr></tbody>
    </table></div>
  `).join("");
  const tipo = datos.tipo_analisis === "incremental" ? "Análisis incremental" : "TIR individual";
  const tmar = datos.tmar === null ? "" : `<span class="badge">TMAR: ${(datos.tmar * 100).toFixed(2)} %</span>`;
  contenedorDatos.innerHTML = `<p><span class="badge">${tipo}</span> ${tmar}</p>${proyectosHtml}`;
}

function renderErrorSolucion(mensaje) {
  contenedorSolucion.textContent = mensaje;
}

function renderPasos(pasos) {
  return pasos.map(paso => `
    <div class="paso">
      <h4>${escaparHtml(paso.titulo)}</h4>
      <p>${escaparHtml(paso.contenido)}</p>
    </div>
  `).join("");
}

function renderSolucion(resultado) {
  let html = `<h3>Fundamento teórico</h3><p>${escaparHtml(resultado.fundamento_teorico)}</p>`;

  if (resultado.tipo_analisis === "incremental") {
    resultado.proyectos.forEach(proyecto => {
      const nombre = escaparHtml(proyecto.nombre);
      const tasas = proyecto.tir.length
        ? proyecto.tir.map(tasa => `${(tasa * 100).toFixed(2)}%`).join(", ")
        : "N/D";
      html += `<h3>${nombre}</h3>`;
      html += `<p><span class="badge ${proyecto.clasificacion.cambios_signo > 1 ? "badge--mixta" : ""}">`;
      html += `${escaparHtml(proyecto.clasificacion.tipo)}</span> TIR: ${tasas}; `;
      html += `VAN a TMAR: ${Number(proyecto.van_a_tmar).toFixed(2)}</p>`;
      html += `<h4>Desarrollo de ${nombre}</h4>${renderPasos(proyecto.pasos)}`;
    });
    html += "<h3>Desarrollo del análisis incremental</h3>";
    resultado.pasos_incremental.forEach(paso => {
      html += renderPasos([paso]);
      if (paso.detalle_van) html += renderPasos(paso.detalle_van);
    });
  } else {
    html += "<h3>Clasificación de la inversión</h3>";
    html += `<p><span class="badge ${resultado.clasificacion.cambios_signo > 1 ? "badge--mixta" : ""}">`;
    html += `${escaparHtml(resultado.clasificacion.tipo)}</span></p>`;
    html += `<p>${escaparHtml(resultado.clasificacion.explicacion)}</p>`;
    html += "<h3>Desarrollo paso a paso</h3>";
    html += renderPasos(resultado.pasos);
  }

  html += `<div class="respuesta-final">${escaparHtml(resultado.respuesta_final)}</div>`;
  contenedorSolucion.innerHTML = html;
}

function renderGraficos(resultado) {
  const empty = document.getElementById("graficos-empty");
  empty.hidden = false;

  if (typeof Chart === "undefined") {
    empty.textContent = "Los gráficos requieren conexión para cargar Chart.js. La solución numérica está disponible.";
    return;
  }
  empty.hidden = true;

  const proyecto = resultado.tipo_analisis === "incremental"
    ? resultado.proyectos[0]
    : resultado.graficos;
  const flujoCaja = resultado.tipo_analisis === "incremental"
    ? proyecto.grafico_flujo
    : proyecto.flujo_caja;
  const curvaVan = resultado.tipo_analisis === "incremental"
    ? proyecto.grafico_van
    : proyecto.curva_van;

  const ctxFlujo = document.getElementById("chart-flujo").getContext("2d");
  if (chartFlujo) chartFlujo.destroy();
  chartFlujo = new Chart(ctxFlujo, {
    type: "bar",
    data: {
      labels: flujoCaja.map(dato => `t${dato.periodo}`),
      datasets: [{
        label: "Monto",
        data: flujoCaja.map(dato => dato.monto),
        backgroundColor: flujoCaja.map(dato => dato.monto < 0 ? "#C23B3B" : "#2F6FED"),
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
      labels: curvaVan.map(dato => `${(dato.tasa * 100).toFixed(0)}%`),
      datasets: [{
        label: "VAN",
        data: curvaVan.map(dato => dato.van),
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

renderProyectos();
