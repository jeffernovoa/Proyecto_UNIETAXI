# main.py
"""
Punto de entrada del sistema UNIETAXI.
- Inicializa sistema, afiliaciones simuladas, entidades y GUI.
- Programa cierre contable a las 12:00 pm reales.
"""

import threading
import time
from datetime import datetime, timedelta
from sistema_atencion import SistemaAtencion
from cliente import Cliente
from taxi import Taxi
from gui import iniciar_gui
from utils import generar_clientes_iniciales, generar_taxis_iniciales
from afiliacion import Afiliador
from reportes import Reportes

def programar_cierre_diario(sistema):
    """Programa el cierre contable para las 12:00 pm hora local cada día."""
    def tiempo_hasta_mediodia():
        ahora = datetime.now()
        objetivo = ahora.replace(hour=12, minute=0, second=0, microsecond=0)
        if ahora >= objetivo:
            objetivo += timedelta(days=1)
        return (objetivo - ahora).total_seconds()

    def planificar():
        # Espera hasta las 12:00 y ejecuta cierre
        time.sleep(tiempo_hasta_mediodia())
        sistema.cierre_contable()
        # Reprograma para el siguiente día
        planificar()

    threading.Thread(target=planificar, name="Scheduler-Cierre-12pm", daemon=True).start()

def main():
    sistema = SistemaAtencion()
    afiliador = Afiliador()
    reportes = Reportes(sistema)

    # Simular afiliaciones (datos válidos/invalidos)
    afiliador.cargar_base_datos()
    afiliador.afiliar_clientes_sistema(sistema)
    afiliador.afiliar_taxis_sistema(sistema)

    # Generar entidades de simulación (solo admitidos)
    taxis = generar_taxis_iniciales(num_taxis=12, sistema=sistema, solo_admitidos=True)
    clientes = generar_clientes_iniciales(num_clientes=18, sistema=sistema, solo_admitidos=True)

    # Lanzar hilos de taxis
    for t in taxis:
        threading.Thread(target=t.run, name=f"Taxi-{t.id_taxi}", daemon=True).start()

    # Lanzar hilos de clientes
    for c in clientes:
        threading.Thread(target=c.run, name=f"Cliente-{c.id_cliente}", daemon=True).start()

    # Programar cierre contable diario a las 12:00 pm
    programar_cierre_diario(sistema)

    # Generación de reporte mensual al cerrar el mes (hilo simple que vigila fin de mes)
    def programar_reporte_mensual():
        # Genera reporte el primer minuto del mes
        while True:
            ahora = datetime.now()
            if ahora.day == 1 and ahora.hour == 0 and ahora.minute == 1:
                reportes.generar_reporte_mensual()
                time.sleep(60)  # Evita múltiples ejecuciones en el mismo minuto
            time.sleep(5)

    threading.Thread(target=programar_reporte_mensual, name="Scheduler-Reporte-Mensual", daemon=True).start()

    # Iniciar GUI
    iniciar_gui(sistema, clientes, taxis, afiliador, reportes)

if __name__ == "__main__":
    main()
