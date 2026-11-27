// ============================================================
// app.js — manual cash flow entry and local charts for TIR+
// ============================================================

const coloresGrafico = ["#2F6FED", "#C23B3B", "#1F8A5F", "#B5690B", "#7353BA", "#0E7490"];
let ultimoResultado = null;
let proyectos = [nuevoProyecto("Proyecto A", 2)];

const tabButtons = document.querySelectorAll(".tab-btn");
const tabPanels = document.querySelectorAll(".tab-panel");
const tipoAnalisis = document.getElementById("tipo-analisis");
const unidadPeriodo = document.getElementById("unidad-periodo");
const inputTmar = document.getElementById("input-tmar");
const listaProyectos = document.getElementById("proyectos-entrada");
const btnAgregarProyecto = document.getElementById("btn-agregar-proyecto");
const btnAgregarPeriodo = document.getElementById("btn-agregar-periodo");
const btnQuitarPeriodo = document.getElementById("btn-quitar-periodo");
const btnResolver = document.getElementById("btn-resolver");
const errorEntrada = document.getElementById("analizar-error");
const contenedorDatos = document.getElementById("datos-extraidos");
const contenedorSolucion = document.getElementById("solucion-detallada");

function nuevoProyecto(nombre, cantidadPeriodos) {
  return {
    nombre,
    flujos: Array(cantidadPeriodos).fill(""),
    inversion: "",
    salvamento: "",
    salvamentoAplicado: 0,
    periodoDesde: "1",
    periodoHasta: "1",
    montoRepetido: "",
    modoRango: "reemplazar",
  };
}

function irA(nombreTab) {
  tabButtons.forEach(b => b.classList.toggle("is-active", b.dataset.tab === nombreTab));
  tabPanels.forEach(p => p.classList.toggle("is-active", p.id === `tab-${nombreTab}`));
  if (nombreTab === "graficos" && ultimoResultado) renderGraficos(ultimoResultado);
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

function numeroActual(valor) {
  return String(valor).trim() === "" ? 0 : Number(valor);
}

function renderProyectos() {
  const cantidadPeriodos = proyectos[0].flujos.length;
  const asistentesAbiertos = new Set(
    Array.from(listaProyectos.querySelectorAll("details[data-project-assistant][open]"))
      .map(details => Number(details.dataset.projectAssistant)),
  );
  const unidad = unidadPeriodo.value === "anios"
    ? "años"
    : unidadPeriodo.value === "meses" ? "meses" : "periodos";
  listaProyectos.innerHTML = proyectos.map((proyecto, indice) => `
    <article class="project-card" data-project-card="${indice}">
      <div class="project-heading">
        <label>
          <span>Nombre de la alternativa</span>
          <input type="text" data-project-name="${indice}" value="${escaparHtml(proyecto.nombre)}" maxlength="60">
        </label>
        ${proyectos.length > 2 && indice > 0
          ? `<button class="btn btn--ghost btn--remove" data-remove-project="${indice}" type="button">Eliminar alternativa</button>`
          : ""}
      </div>

      <details class="project-assistants" data-project-assistant="${indice}"
        ${asistentesAbiertos.has(indice) || proyecto.asistentesAbiertos ? "open" : ""}>
        <summary>Asistentes para ingresar datos del enunciado</summary>
        <div class="assistant-grid">
          <section class="assistant-card">
            <h4>Inversión inicial</h4>
            <p>Escribe el monto positivo; se registrará como salida negativa en el periodo 0.</p>
            <label>Inversión <input type="number" step="any" data-investment="${indice}"
              value="${escaparHtml(proyecto.inversion)}" placeholder="Ej. 570000"></label>
            <button class="btn btn--ghost" type="button" data-apply-investment="${indice}">Aplicar inversión</button>
          </section>

          <section class="assistant-card">
            <h4>Flujo que se repite</h4>
            <p>Usa un monto positivo para ingresos y negativo para costos. Los periodos se amplían automáticamente.</p>
            <div class="assistant-fields">
              <label>Desde el periodo<input type="number" min="1" step="1" data-range-start="${indice}"
                value="${escaparHtml(proyecto.periodoDesde)}"></label>
              <label>Hasta el periodo<input type="number" min="1" step="1" data-range-end="${indice}"
                value="${escaparHtml(proyecto.periodoHasta)}"></label>
              <label>Monto por periodo<input type="number" step="any" data-range-amount="${indice}"
                value="${escaparHtml(proyecto.montoRepetido)}" placeholder="Ej. 25000"></label>
              <label>Cómo aplicar
                <select data-range-mode="${indice}">
                  <option value="reemplazar" ${proyecto.modoRango === "reemplazar" ? "selected" : ""}>Reemplazar el flujo base</option>
                  <option value="sumar" ${proyecto.modoRango === "sumar" ? "selected" : ""}>Sumar al flujo existente</option>
                </select>
              </label>
            </div>
            <button class="btn btn--ghost" type="button" data-apply-range="${indice}">Aplicar monto al rango</button>
          </section>

          <section class="assistant-card">
            <h4>Salvamento o venta final</h4>
            <p>Se suma al último periodo. No vuelvas a incluirlo en el monto del flujo de ese periodo.</p>
            <label>Valor final <input type="number" step="any" data-salvage="${indice}"
              value="${escaparHtml(proyecto.salvamento)}" placeholder="Ej. 800000"></label>
            <button class="btn btn--ghost" type="button" data-apply-salvage="${indice}">Sumar al último periodo</button>
          </section>
        </div>
      </details>

      <div class="table-scroll">
        <table class="datos-tabla">
          <thead><tr><th>Flujo neto por periodo</th>${Array.from({ length: cantidadPeriodos }, (_, periodo) =>
            `<th>${periodo === 0 ? "0 (inicial)" : periodo}</th>`).join("")}</tr></thead>
          <tbody><tr><th>Ingreso (+) / costo (-)</th>${proyecto.flujos.map((monto, periodo) => `
            <td><input type="number" step="any" data-project="${indice}" data-period="${periodo}"
              aria-label="${escaparHtml(proyecto.nombre)}, periodo ${periodo}"
              placeholder="${periodo === 0 ? "Ej. -570000" : "Ej. 25000"}"
              value="${escaparHtml(monto)}"></td>
          `).join("")}</tr></tbody>
        </table>
      </div>
    </article>
  `).join("");

  const ultimoPeriodo = cantidadPeriodos - 1;
  document.getElementById("periodos-resumen").textContent =
    `${cantidadPeriodos} periodos: desde el 0 hasta el ${ultimoPeriodo}. ` +
    `Cada paso representa ${unidad}, según el enunciado.`;
  btnAgregarProyecto.hidden = tipoAnalisis.value !== "incremental";
  btnQuitarPeriodo.disabled = cantidadPeriodos <= 2;
}

function extenderProyecto(proyecto) {
  const ultimo = proyecto.flujos.length - 1;
  const flujoBase = numeroActual(proyecto.flujos[ultimo]) - proyecto.salvamentoAplicado;
  proyecto.flujos[ultimo] = flujoBase === 0 ? "" : flujoBase;
  proyecto.flujos.push(proyecto.salvamentoAplicado || "");
}

function agregarPeriodo() {
  proyectos.forEach(extenderProyecto);
  renderProyectos();
}

function quitarPeriodo() {
  if (proyectos[0].flujos.length <= 2) return;
  proyectos.forEach(proyecto => {
    const ultimo = proyecto.flujos.length - 1;
    proyecto.flujos.pop();
    const nuevoUltimo = proyecto.flujos.length - 1;
    proyecto.flujos[nuevoUltimo] = numeroActual(proyecto.flujos[nuevoUltimo]) +
      proyecto.salvamentoAplicado;
    if (proyecto.flujos[nuevoUltimo] === 0) proyecto.flujos[nuevoUltimo] = "";
  });
  renderProyectos();
}

btnAgregarPeriodo.addEventListener("click", agregarPeriodo);
btnQuitarPeriodo.addEventListener("click", quitarPeriodo);

tipoAnalisis.addEventListener("change", () => {
  proyectos = proyectos.slice(0, 1);
  if (tipoAnalisis.value === "incremental") {
    proyectos.push(nuevoProyecto("Proyecto B", proyectos[0].flujos.length));
  }
  renderProyectos();
});

function actualizarAyudaTmar() {
  const ayuda = document.getElementById("tmar-hint");
  ayuda.textContent = unidadPeriodo.value === "meses"
    ? "anual; se convierte a mensual"
    : unidadPeriodo.value === "anios"
      ? "escribe la tasa anual"
      : "escribe la tasa por periodo";
  renderProyectos();
}

unidadPeriodo.addEventListener("change", actualizarAyudaTmar);

btnAgregarProyecto.addEventListener("click", () => {
  proyectos.push(nuevoProyecto(`Proyecto ${proyectos.length + 1}`, proyectos[0].flujos.length));
  renderProyectos();
});

listaProyectos.addEventListener("input", evento => {
  const objetivo = evento.target;
  if (objetivo.matches("[data-project-name]")) {
    proyectos[Number(objetivo.dataset.projectName)].nombre = objetivo.value;
    return;
  }
  if (objetivo.matches("[data-project][data-period]")) {
    const proyecto = proyectos[Number(objetivo.dataset.project)];
    proyecto.flujos[Number(objetivo.dataset.period)] = objetivo.value;
    if (Number(objetivo.dataset.period) === proyecto.flujos.length - 1) {
      proyecto.salvamentoAplicado = 0;
    }
    return;
  }
  const propiedades = [
    ["data-investment", "inversion"],
    ["data-salvage", "salvamento"],
    ["data-range-start", "periodoDesde"],
    ["data-range-end", "periodoHasta"],
    ["data-range-amount", "montoRepetido"],
  ];
  for (const [atributo, propiedad] of propiedades) {
    if (objetivo.matches(`[${atributo}]`)) {
      proyectos[Number(objetivo.getAttribute(atributo))][propiedad] = objetivo.value;
      return;
    }
  }
});

listaProyectos.addEventListener("change", evento => {
  const objetivo = evento.target;
  if (objetivo.matches("[data-range-mode]")) {
    proyectos[Number(objetivo.dataset.rangeMode)].modoRango = objetivo.value;
  }
});

function mostrarError(elemento, mensaje) {
  elemento.textContent = mensaje;
  elemento.hidden = false;
}

function leerMonto(valor, etiqueta) {
  if (String(valor).trim() === "") throw new Error(`Ingresa el monto para ${etiqueta}.`);
  const monto = Number(valor);
  if (!Number.isFinite(monto)) throw new Error(`El monto para ${etiqueta} no es válido.`);
  return monto;
}

function aplicarAsistente(evento) {
  const boton = evento.target.closest("[data-apply-investment], [data-apply-range], [data-apply-salvage]");
  if (!boton) return;
  errorEntrada.hidden = true;
  const indice = Number(
    boton.dataset.applyInvestment ?? boton.dataset.applyRange ?? boton.dataset.applySalvage,
  );
  const proyecto = proyectos[indice];

  try {
    if (boton.hasAttribute("data-apply-investment")) {
      proyecto.flujos[0] = -Math.abs(leerMonto(proyecto.inversion, "la inversión inicial"));
    } else if (boton.hasAttribute("data-apply-salvage")) {
      const salvamento = leerMonto(proyecto.salvamento, "el valor de salvamento o venta");
      const ultimo = proyecto.flujos.length - 1;
      proyecto.flujos[ultimo] = numeroActual(proyecto.flujos[ultimo]) -
        proyecto.salvamentoAplicado + salvamento;
      proyecto.salvamentoAplicado = salvamento;
    } else {
      const desde = Number(proyecto.periodoDesde);
      const hasta = Number(proyecto.periodoHasta);
      const monto = leerMonto(proyecto.montoRepetido, "el flujo que se repite");
      if (!Number.isInteger(desde) || desde < 1 ||
          !Number.isInteger(hasta) || hasta < desde) {
        throw new Error("Indica un rango válido: el periodo inicial debe ser 1 o mayor y no superar el final.");
      }

      while (proyectos[0].flujos.length <= hasta) agregarPeriodoSinRenderizar();
      for (let periodo = desde; periodo <= hasta; periodo++) {
        const actual = numeroActual(proyecto.flujos[periodo]);
        if (proyecto.modoRango === "sumar") {
          proyecto.flujos[periodo] = actual + monto;
        } else {
          const salvamentoAlFinal = periodo === proyecto.flujos.length - 1
            ? proyecto.salvamentoAplicado
            : 0;
          proyecto.flujos[periodo] = monto + salvamentoAlFinal;
        }
      }
    }
    renderProyectos();
  } catch (error) {
    mostrarError(errorEntrada, error.message);
  }
}

function agregarPeriodoSinRenderizar() {
  proyectos.forEach(extenderProyecto);
}

listaProyectos.addEventListener("click", evento => {
  const botonEliminar = evento.target.closest("[data-remove-project]");
  if (botonEliminar) {
    proyectos.splice(Number(botonEliminar.dataset.removeProject), 1);
    renderProyectos();
    return;
  }
  aplicarAsistente(evento);
});

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
  const tmarIngresada = tmarTexto === "" ? null : Number(tmarTexto) / 100;
  if (tmarIngresada !== null && !Number.isFinite(tmarIngresada)) {
    throw new Error("Ingresa un porcentaje TMAR válido.");
  }
  if (tmarIngresada !== null && tmarIngresada <= -1) {
    throw new Error("La TMAR debe ser mayor que -100 %.");
  }
  const tmar = tmarIngresada === null
    ? null
    : unidadPeriodo.value === "meses"
      ? (1 + tmarIngresada) ** (1 / 12) - 1
      : tmarIngresada;

  return {
    tipo_analisis: tipoAnalisis.value,
    unidad_periodo: unidadPeriodo.value,
    tmar,
    tmar_ingresada: tmarIngresada,
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

    ultimoResultado = resultado;
    renderDatos(datos);
    renderSolucion(resultado, datos);
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
  const unidad = datos.unidad_periodo === "anios"
    ? "años"
    : datos.unidad_periodo === "meses" ? "meses" : "periodos";
  let tmar = "";
  if (datos.tmar !== null) {
    const referencia = datos.unidad_periodo === "otro"
      ? `${(datos.tmar * 100).toFixed(2)} % por periodo`
      : `${(datos.tmar_ingresada * 100).toFixed(2)} % anual`;
    const aplicada = datos.unidad_periodo === "meses"
      ? `; aplicada como ${(datos.tmar * 100).toFixed(4)} % mensual`
      : "";
    tmar = `<span class="badge">TMAR: ${referencia}${aplicada}</span>`;
  }
  contenedorDatos.innerHTML =
    `<p><span class="badge">${tipo}</span> <span class="badge">Periodos: ${unidad}</span> ${tmar}</p>${proyectosHtml}`;
}

function renderPasos(pasos) {
  return pasos.map(paso => `
    <div class="paso">
      <h4>${escaparHtml(paso.titulo)}</h4>
      <p>${escaparHtml(paso.contenido)}</p>
    </div>
  `).join("");
}

function describirTasa(tasa, unidad) {
  const porcentaje = `${(tasa * 100).toFixed(2)} %`;
  if (unidad === "meses") {
    const anual = ((1 + tasa) ** 12 - 1) * 100;
    return `${porcentaje} mensual (equivale a ${anual.toFixed(2)} % efectivo anual)`;
  }
  return unidad === "anios" ? `${porcentaje} anual` : `${porcentaje} por periodo`;
}

function renderSolucion(resultado, datos) {
  let html = `<h3>Fundamento teórico</h3><p>${escaparHtml(resultado.fundamento_teorico)}</p>`;

  if (resultado.tipo_analisis === "incremental") {
    resultado.proyectos.forEach(proyecto => {
      const nombre = escaparHtml(proyecto.nombre);
      const tasas = proyecto.tir.length
        ? proyecto.tir.map(tasa => describirTasa(tasa, datos.unidad_periodo)).join("; ")
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
    if (datos.unidad_periodo === "meses" && resultado.tir.length) {
      html += `<p class="entry-note"><strong>Equivalencia efectiva anual:</strong> ${resultado.tir
        .map(tasa => describirTasa(tasa, datos.unidad_periodo)).join("; ")}.</p>`;
    }
  }

  html += `<div class="respuesta-final">${escaparHtml(resultado.respuesta_final)}</div>`;
  contenedorSolucion.innerHTML = html;
}

function prepararCanvas(canvas) {
  const rectangulo = canvas.getBoundingClientRect();
  if (!rectangulo.width) return null;
  const escala = window.devicePixelRatio || 1;
  const alto = 320;
  canvas.width = Math.round(rectangulo.width * escala);
  canvas.height = Math.round(alto * escala);
  const contexto = canvas.getContext("2d");
  contexto.setTransform(escala, 0, 0, escala, 0, 0);
  contexto.clearRect(0, 0, rectangulo.width, alto);
  contexto.font = "12px system-ui, sans-serif";
  contexto.fillStyle = "#4C5A70";
  contexto.strokeStyle = "#DCE4F0";
  return { contexto, ancho: rectangulo.width, alto };
}

function formatoCompacto(valor) {
  return new Intl.NumberFormat("es", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(valor);
}

function dibujarEjes(contexto, ancho, alto, minimo, maximo, margen) {
  const { izquierda, derecha, arriba, abajo } = margen;
  const altoGrafico = alto - arriba - abajo;
  const anchoGrafico = ancho - izquierda - derecha;
  const rango = maximo - minimo || 1;
  contexto.textAlign = "right";
  contexto.textBaseline = "middle";
  for (let i = 0; i <= 4; i++) {
    const valor = maximo - (rango * i / 4);
    const y = arriba + altoGrafico * i / 4;
    contexto.beginPath();
    contexto.moveTo(izquierda, y);
    contexto.lineTo(ancho - derecha, y);
    contexto.stroke();
    contexto.fillText(formatoCompacto(valor), izquierda - 8, y);
  }
  contexto.beginPath();
  contexto.moveTo(izquierda, arriba);
  contexto.lineTo(izquierda, alto - abajo);
  contexto.lineTo(ancho - derecha, alto - abajo);
  contexto.stroke();
  return {
    izquierda,
    arriba,
    anchoGrafico,
    altoGrafico,
    y: valor => arriba + (maximo - valor) / rango * altoGrafico,
  };
}

function distribucionLeyenda(cantidad, ancho) {
  const columnas = Math.max(1, Math.floor((ancho - 76) / 150));
  const filas = Math.ceil(cantidad / columnas);
  return { columnas, filas, alto: filas * 16 + 14 };
}

function dibujarFlujos(canvas, series) {
  const lienzo = prepararCanvas(canvas);
  if (!lienzo) return;
  const { contexto, ancho, alto } = lienzo;
  const valores = series.flatMap(serie => serie.datos.map(dato => dato.monto));
  const minimo = Math.min(0, ...valores);
  const maximo = Math.max(0, ...valores);
  const leyenda = distribucionLeyenda(series.length, ancho);
  const margen = { izquierda: 62, derecha: 14, arriba: Math.max(34, leyenda.alto), abajo: 42 };
  const ejes = dibujarEjes(contexto, ancho, alto, minimo, maximo, margen);
  const periodos = Math.max(...series.map(serie => serie.datos.length));
  const anchoGrupo = ejes.anchoGrafico / periodos;
  const anchoBarra = Math.max(2, Math.min(28, anchoGrupo * 0.72 / series.length));
  const yCero = ejes.y(0);

  series.forEach((serie, indiceSerie) => {
    contexto.fillStyle = coloresGrafico[indiceSerie % coloresGrafico.length];
    serie.datos.forEach((dato, indicePeriodo) => {
      const xCentro = ejes.izquierda + anchoGrupo * (indicePeriodo + 0.5);
      const x = xCentro + (indiceSerie - (series.length - 1) / 2) * anchoBarra - anchoBarra / 2;
      const yValor = ejes.y(dato.monto);
      contexto.fillRect(x, Math.min(yCero, yValor), anchoBarra, Math.max(1, Math.abs(yCero - yValor)));
    });
  });

  contexto.textAlign = "center";
  contexto.textBaseline = "top";
  const saltoEtiqueta = Math.max(1, Math.ceil(periodos / 10));
  for (let periodo = 0; periodo < periodos; periodo += saltoEtiqueta) {
    const x = ejes.izquierda + anchoGrupo * (periodo + 0.5);
    contexto.fillText(`t${periodo}`, x, alto - margen.abajo + 8);
  }
  dibujarLeyenda(contexto, series.map((serie, i) => ({
    nombre: serie.nombre,
    color: coloresGrafico[i % coloresGrafico.length],
  })), ancho, leyenda.columnas);
}

function dibujarCurvas(canvas, series) {
  const lienzo = prepararCanvas(canvas);
  if (!lienzo) return;
  const { contexto, ancho, alto } = lienzo;
  const valores = series.flatMap(serie => serie.datos.map(dato => dato.van));
  let minimo = Math.min(0, ...valores);
  let maximo = Math.max(0, ...valores);
  if (minimo === maximo) {
    minimo -= 1;
    maximo += 1;
  }
  const leyenda = distribucionLeyenda(series.length, ancho);
  const margen = { izquierda: 62, derecha: 14, arriba: Math.max(42, leyenda.alto), abajo: 42 };
  const ejes = dibujarEjes(contexto, ancho, alto, minimo, maximo, margen);
  const puntos = Math.max(...series.map(serie => serie.datos.length));
  const anchoGrupo = ejes.anchoGrafico / Math.max(1, puntos - 1);

  series.forEach((serie, indice) => {
    contexto.strokeStyle = coloresGrafico[indice % coloresGrafico.length];
    contexto.lineWidth = 2;
    contexto.beginPath();
    serie.datos.forEach((dato, punto) => {
      const x = ejes.izquierda + anchoGrupo * punto;
      const y = ejes.y(dato.van);
      if (punto === 0) contexto.moveTo(x, y);
      else contexto.lineTo(x, y);
    });
    contexto.stroke();
  });

  contexto.fillStyle = "#4C5A70";
  contexto.textAlign = "center";
  contexto.textBaseline = "top";
  const tasas = series[0].datos;
  const saltoEtiqueta = Math.max(1, Math.ceil(tasas.length / 8));
  for (let i = 0; i < tasas.length; i += saltoEtiqueta) {
    const x = ejes.izquierda + anchoGrupo * i;
    contexto.fillText(`${(tasas[i].tasa * 100).toFixed(0)}%`, x, alto - margen.abajo + 8);
  }
  dibujarLeyenda(contexto, series.map((serie, i) => ({
    nombre: serie.nombre,
    color: coloresGrafico[i % coloresGrafico.length],
  })), ancho, leyenda.columnas);
}

function dibujarLeyenda(contexto, elementos, ancho, columnas) {
  contexto.font = "12px system-ui, sans-serif";
  contexto.textAlign = "left";
  contexto.textBaseline = "middle";
  elementos.forEach((elemento, indice) => {
    const columna = indice % columnas;
    const fila = Math.floor(indice / columnas);
    const x = 68 + columna * (ancho - 78) / columnas;
    const y = 12 + fila * 16;
    contexto.fillStyle = elemento.color;
    contexto.fillRect(x, y - 5, 10, 10);
    contexto.fillStyle = "#4C5A70";
    const nombre = elemento.nombre.length > 18
      ? `${elemento.nombre.slice(0, 16)}…`
      : elemento.nombre;
    contexto.fillText(nombre, x + 15, y);
  });
}

function renderGraficos(resultado) {
  const vacio = document.getElementById("graficos-empty");
  vacio.hidden = true;
  const datosProyectos = resultado.tipo_analisis === "incremental"
    ? resultado.proyectos
    : [{
        nombre: resultado.proyecto.nombre,
        grafico_flujo: resultado.graficos.flujo_caja,
        grafico_van: resultado.graficos.curva_van,
      }];
  const seriesFlujos = datosProyectos.map(proyecto => ({
    nombre: proyecto.nombre,
    datos: proyecto.grafico_flujo,
  }));
  const seriesVan = datosProyectos.map(proyecto => ({
    nombre: proyecto.nombre,
    datos: proyecto.grafico_van,
  }));
  dibujarFlujos(document.getElementById("chart-flujo"), seriesFlujos);
  dibujarCurvas(document.getElementById("chart-van"), seriesVan);
}

window.addEventListener("resize", () => {
  if (ultimoResultado && document.getElementById("tab-graficos").classList.contains("is-active")) {
    renderGraficos(ultimoResultado);
  }
});

renderProyectos();
