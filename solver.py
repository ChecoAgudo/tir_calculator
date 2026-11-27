# -*- coding: utf-8 -*-
"""
solver.py
Motor matemático-financiero para la Calculadora de TIR.

Teoría implementada (Unidad 7 - Análisis de la Tasa de Rendimiento,
M.Sc. Emir Vargas):

    VAN(i) = sum_{t=0}^{n} CF_t / (1 + i)^t

    La TIR es el valor de i que hace VAN(i) = 0.

Para encontrar la TIR de forma EXACTA (no solo una raíz, sino TODAS las
posibles, tal como exige el libro para inversiones "mixtas"/complejas),
se reformula la ecuación como un polinomio:

    Sea x = (1 + i). Multiplicando VAN(i) = 0 por x^n:

        CF_0 * x^n + CF_1 * x^(n-1) + ... + CF_n * x^0 = 0

    Es decir, los coeficientes del polinomio (de mayor a menor grado)
    son exactamente los flujos de caja en su orden original.
    Para n = 2 esto es una ecuación cuadrática clásica
    (a*x^2 + b*x + c = 0), que es precisamente lo que pide el
    ejercicio 7 del práctico ("Calcule la TIR del proyecto A usando la
    ecuación cuadrática").

Se usan raíces reales positivas de x (x > 0, porque 1+i debe ser > 0)
para obtener i = x - 1. Si existe más de una raíz válida, el proyecto
tiene TIR múltiple (inversión no simple / mixta).
"""
from __future__ import annotations
import numpy as np
import numpy_financial as npf


# --------------------------------------------------------------------------
# Utilidades de formato
# --------------------------------------------------------------------------

def fmt_money(x: float) -> str:
    return f"${x:,.2f}"


def fmt_pct(x: float) -> str:
    return f"{x * 100:,.2f} %"


# --------------------------------------------------------------------------
# VAN (Valor Actual Neto)
# --------------------------------------------------------------------------

def van(cashflows: list[float], rate: float) -> float:
    """Valor Actual Neto de un flujo de caja a una tasa dada."""
    return float(sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows)))


def pasos_van(cashflows: list[float], rate: float) -> list[dict]:
    """Desarrollo paso a paso del cálculo de VAN (para mostrar en la UI)."""
    pasos = []
    terminos = []
    for t, cf in enumerate(cashflows):
        valor_actual = cf / (1 + rate) ** t
        terminos.append(valor_actual)
        pasos.append({
            "titulo": f"Periodo {t}",
            "contenido": (
                f"VA_{t} = {fmt_money(cf)} / (1 + {rate:.4f})^{t} "
                f"= {fmt_money(valor_actual)}"
            ),
        })
    total = sum(terminos)
    pasos.append({
        "titulo": "Suma de valores actuales",
        "contenido": f"VAN({fmt_pct(rate)}) = {fmt_money(total)}",
    })
    return pasos


# --------------------------------------------------------------------------
# Regla de signos de Descartes y clasificación del proyecto
# --------------------------------------------------------------------------

def descartes_cambios_signo(cashflows: list[float]) -> int:
    """Cuenta los cambios de signo en la secuencia de flujos (ignorando ceros)."""
    no_cero = [cf for cf in cashflows if cf != 0]
    cambios = 0
    for a, b in zip(no_cero, no_cero[1:]):
        if (a > 0) != (b > 0):
            cambios += 1
    return cambios


def clasificar_inversion(cashflows: list[float]) -> dict:
    """
    Clasifica el proyecto como 'simple/pura' (un solo cambio de signo:
    siempre tiene una única TIR real positiva) o 'mixta/compleja'
    (más de un cambio de signo: pueden existir 0, 1 o varias TIR,
    según la regla de signos de Descartes).
    """
    cambios = descartes_cambios_signo(cashflows)
    if cambios <= 1:
        tipo = "simple (pura)"
        explicacion = (
            "Un solo cambio de signo (inversión seguida solo de ingresos): "
            "por la regla de los signos de Descartes existe exactamente "
            "una raíz real positiva, es decir, una única TIR económica "
            "válida."
        )
    else:
        tipo = "mixta (no simple / compleja)"
        explicacion = (
            f"Hay {cambios} cambios de signo en el flujo de caja. "
            f"Por la regla de los signos de Descartes, el número de raíces "
            f"reales positivas es {cambios}, {cambios - 2}, {cambios - 4}... "
            f"(siempre bajando de 2 en 2), por lo que el proyecto puede "
            f"tener múltiples valores de TIR."
        )
    return {
        "cambios_signo": cambios,
        "tipo": tipo,
        "explicacion": explicacion,
        "max_raices_posibles": cambios,
    }


# --------------------------------------------------------------------------
# TIR — todas las raíces reales (método del polinomio)
# --------------------------------------------------------------------------

def _raices_polinomio(cashflows: list[float]) -> list[float]:
    """
    Resuelve CF_0*x^n + CF_1*x^(n-1) + ... + CF_n = 0 y devuelve las
    tasas i = x - 1 correspondientes a raíces reales con x > 0.
    """
    coeffs = np.array(cashflows, dtype=float)
    # numpy.roots exige que el primer coeficiente no sea cero
    while len(coeffs) > 1 and coeffs[0] == 0:
        coeffs = coeffs[1:]
    raices = np.roots(coeffs)
    tasas = []
    for r in raices:
        if abs(r.imag) < 1e-6:  # raíz prácticamente real
            x = r.real
            if x > 1e-9:  # 1 + i debe ser positivo
                tasas.append(round(x - 1, 8))
    return sorted(set(tasas))


def encontrar_tir(cashflows: list[float]) -> dict:
    """
    Calcula TODAS las TIR reales válidas de un flujo de caja y arma el
    desarrollo paso a paso (incluida la fórmula cuadrática explícita
    cuando el proyecto dura 2 periodos, tal como exige el ejercicio 7).
    """
    n = len(cashflows) - 1
    clasificacion = clasificar_inversion(cashflows)
    tasas = _raices_polinomio(cashflows)

    pasos = []
    terminos_poly = " + ".join(
        f"({fmt_money(cf)})·x^{n - t}" for t, cf in enumerate(cashflows)
    )
    pasos.append({
        "titulo": "1. Plantear la ecuación de equilibrio (VAN = 0)",
        "contenido": (
            f"0 = " + " + ".join(
                f"{fmt_money(cf)}/(1+i)^{t}" for t, cf in enumerate(cashflows)
            )
        ),
    })
    pasos.append({
        "titulo": "2. Sustituir x = (1 + i) y multiplicar por x^n",
        "contenido": f"0 = {terminos_poly}",
    })

    if n == 2:
        a, b, c = cashflows[0], cashflows[1], cashflows[2]
        disc = b ** 2 - 4 * a * c
        pasos.append({
            "titulo": "3. Ecuación cuadrática (a·x² + b·x + c = 0)",
            "contenido": (
                f"a = {fmt_money(a)}, b = {fmt_money(b)}, c = {fmt_money(c)}  →  "
                f"Discriminante = b² − 4ac = {b ** 2:,.2f} − {4*a*c:,.2f} = {disc:,.4f}"
            ),
        })
        if disc >= 0:
            raiz = disc ** 0.5
            x1 = (-b + raiz) / (2 * a)
            x2 = (-b - raiz) / (2 * a)
            pasos.append({
                "titulo": "4. Fórmula general",
                "contenido": (
                    f"x = (−b ± √Δ) / (2a)  →  x₁ = {x1:,.6f} ,  x₂ = {x2:,.6f}"
                ),
            })
        else:
            pasos.append({
                "titulo": "4. Fórmula general",
                "contenido": "Δ < 0 → las raíces son complejas, no existe TIR real.",
            })
    else:
        pasos.append({
            "titulo": "3. Resolver el polinomio de grado n",
            "contenido": (
                f"Se resuelve numéricamente (equivalente al método de "
                f"ensayo y error descrito en el libro) con los coeficientes "
                f"{list(np.round(cashflows, 2))}."
            ),
        })

    if tasas:
        pasos.append({
            "titulo": "5. Filtrar raíces válidas (x = 1+i > 0)",
            "contenido": "Tasas candidatas: " + ", ".join(fmt_pct(t) for t in tasas),
        })
    else:
        pasos.append({
            "titulo": "5. Filtrar raíces válidas (x = 1+i > 0)",
            "contenido": "No se encontró ninguna raíz real positiva: el proyecto no tiene TIR real.",
        })

    return {
        "tir": tasas,                 # lista (puede tener 0, 1 o varias)
        "tir_principal": tasas[0] if tasas else None,
        "clasificacion": clasificacion,
        "pasos": pasos,
    }


def tir_numpy_financial(cashflows: list[float]) -> float | None:
    """TIR 'de referencia' usando numpy_financial (una sola raíz), útil
    para verificación cruzada rápida."""
    try:
        r = npf.irr(cashflows)
        return None if (r is None or np.isnan(r)) else float(r)
    except Exception:
        return None


# --------------------------------------------------------------------------
# Análisis incremental (selección entre alternativas mutuamente excluyentes)
# --------------------------------------------------------------------------

def _pad(flujo: list[float], largo: int) -> list[float]:
    return flujo + [0.0] * (largo - len(flujo))


def analisis_incremental(proyectos: list[dict], tmar: float) -> dict:
    """
    proyectos: [{"nombre": "A", "flujos": [...]}, ...]
    Implementa el método clásico de ingeniería económica:
      1. Ordenar los proyectos por inversión inicial (de menor a mayor).
      2. El de menor inversión se acepta como "base" si su propia TIR >= TMAR;
         si no, se descarta y se prueba con el siguiente.
      3. Para cada proyecto siguiente, se calcula el flujo incremental
         (mayor − base) y su TIR. Si TIR_incremental >= TMAR, el proyecto
         de mayor inversión se vuelve la nueva base; si no, se mantiene la base.
      4. Al final, la base es la alternativa económicamente preferida.
    """
    largo = max(len(p["flujos"]) for p in proyectos)
    ordenados = sorted(proyectos, key=lambda p: abs(p["flujos"][0]))

    pasos = []
    base = None
    for proy in ordenados:
        flujo = _pad(proy["flujos"], largo)
        resultado = encontrar_tir(flujo)
        tir_propia = resultado["tir_principal"]

        if base is None:
            aceptado = tir_propia is not None and tir_propia >= tmar
            pasos.append({
                "titulo": f"Evaluar {proy['nombre']} de forma individual",
                "contenido": (
                    f"TIR({proy['nombre']}) = "
                    f"{fmt_pct(tir_propia) if tir_propia is not None else 'N/D'} "
                    f"{'≥' if aceptado else '<'} TMAR ({fmt_pct(tmar)}) → "
                    f"{'se acepta como base' if aceptado else 'se descarta'}."
                ),
            })
            if aceptado:
                base = {"nombre": proy["nombre"], "flujos": flujo}
            continue

        incremento = [b - a for a, b in zip(base["flujos"], flujo)]
        res_inc = encontrar_tir(incremento)
        tasas_inc = res_inc["tir"]
        # Prueba robusta: el signo del VAN incremental a la TMAR SIEMPRE es
        # válido (incluso cuando hay TIR múltiple / inversión mixta, donde
        # comparar "la" TIR con la TMAR puede ser ambiguo o engañoso, tal
        # como advierte el libro en 7.4.1).
        van_inc = van(incremento, tmar)
        gana_mayor = van_inc > 0

        if res_inc["clasificacion"]["cambios_signo"] > 1:
            nota_tir = (
                f"(inversión incremental MIXTA: raíces candidatas de TIR = "
                f"{[fmt_pct(t) for t in tasas_inc] if tasas_inc else 'ninguna real'}; "
                f"por eso la decisión se toma con el signo del VAN a la TMAR, "
                f"no comparando directamente una sola TIR)"
            )
        else:
            nota_tir = (
                f"TIR_incremental = "
                f"{fmt_pct(tasas_inc[0]) if tasas_inc else 'N/D'} "
                f"{'≥' if gana_mayor else '<'} TMAR ({fmt_pct(tmar)})"
            )

        pasos.append({
            "titulo": f"Incremental: {proy['nombre']} vs. {base['nombre']}",
            "contenido": (
                f"ΔFlujo = {proy['nombre']} − {base['nombre']} = "
                f"{[round(v, 2) for v in incremento]}  →  "
                f"VAN_incremental({fmt_pct(tmar)}) = {fmt_money(van_inc)}  "
                f"{nota_tir}  →  "
                f"{'la inversión adicional se justifica, ' + proy['nombre'] + ' pasa a ser la base' if gana_mayor else base['nombre'] + ' se mantiene como mejor opción'}."
            ),
        })
        if gana_mayor:
            base = {"nombre": proy["nombre"], "flujos": flujo}

    return {
        "pasos": pasos,
        "mejor_proyecto": base["nombre"] if base else "Ninguno (no invertir)",
    }


# --------------------------------------------------------------------------
# Datos para gráficos (Chart.js los dibuja en el frontend)
# --------------------------------------------------------------------------

def curva_van(cashflows: list[float], tasa_min=-0.5, tasa_max=1.0, paso=0.01) -> list[dict]:
    puntos = []
    tasa = tasa_min
    while tasa <= tasa_max + 1e-9:
        puntos.append({"tasa": round(tasa, 4), "van": round(van(cashflows, tasa), 2)})
        tasa += paso
    return puntos


def datos_flujo_caja(cashflows: list[float]) -> list[dict]:
    return [{"periodo": t, "monto": cf} for t, cf in enumerate(cashflows)]
