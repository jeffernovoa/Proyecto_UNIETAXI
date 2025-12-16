# reportes.py
"""
Generación de reportes:
- Mensual: ganancias empresa y por taxi, conteo de viajes, calificaciones promedio.
- Persiste en docs/reporte_mensual.md y data/contabilidad.json.
"""

import os
import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")
DOCS_DIR = Path("docs")

class Reportes:
    def __init__(self, sistema):
        self.sistema = sistema
        DOCS_DIR.mkdir(exist_ok=True)

    def generar_reporte_mensual(self):
        # Cargar contabilidad
        contabilidad = {}
        fcont = DATA_DIR / "contabilidad.json"
        if fcont.exists():
            with open(fcont, "r", encoding="utf-8") as f:
                contabilidad = json.load(f)
        # Agregaciones
        por_taxi = self.sistema.agregacion_calidad_por_taxi()
        por_cliente = self.sistema.agregacion_calidad_por_cliente()
        viajes_total = 0
        ganancias_empresa = contabilidad.get("ganancia_empresa", 0.0)
        ganancias_por_taxi = contabilidad.get("ganancias_por_taxi", {})

        # Viajes
        fviajes = DATA_DIR / "viajes.json"
        viajes = []
        if fviajes.exists():
            with open(fviajes, "r", encoding="utf-8") as f:
                viajes = json.load(f)
        viajes_total = len([v for v in viajes if v.get("estado") == "finalizado"])

        # Generar markdown
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"# Reporte mensual UNIETAXI",
            f"- Fecha de generación: {ts}",
            f"- Viajes finalizados en el mes: {viajes_total}",
            f"- Ganancia empresa: €{ganancias_empresa:.2f}",
            f"## Ganancias por taxi",
        ]
        for tid, monto in ganancias_por_taxi.items():
            lines.append(f"- Taxi {tid}: €{monto:.2f}")
        lines.append("## Calificación promedio por taxi")
        for tid, (prom, cant) in por_taxi.items():
            lines.append(f"- Taxi {tid}: {prom:.2f} ({cant} viajes)")
        lines.append("## Calificación promedio por cliente")
        for cid, (prom, cant) in por_cliente.items():
            lines.append(f"- Cliente {cid}: {prom:.2f} ({cant} viajes)")

        with open(DOCS_DIR / "reporte_mensual.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
