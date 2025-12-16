# main.py
"""
Punto de entrada del sistema UNIETAXI.
- Inicializa el sistema de atención, afiliaciones y reportes.
- Genera clientes y taxis admitidos.
- Lanza hilos concurrentes para simular actividad.
- Programa cierre contable diario a las 12:00 pm.
- Programa reporte mensual automático.
- Inicia la interfaz gráfica (GUI).
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
    """
    Programa un hilo que ejecuta el cierre contable automáticamente cada día a las 12:00 pm.
    """
    def tiempo_hasta_mediodia():
        ahora = datetime.now()
        objetivo = ahora.replace(hour=12, minute=0, second=0, microsecond=0)
        if ahora >= objetivo:
            objetivo += timedelta(days=1)
        return (objetivo - ahora).total_seconds()

    def planificar():
        while True:
            time.sleep(tiempo_hasta_mediodia())
            sistema.cierre_contable_programado()
    threading.Thread(target=planificar, name="Scheduler-Cierre-12pm", daemon=True).start()

def main():
    # Inicialización de módulos principales
    sistema = SistemaAtencion()
    afiliador = Afiliador()
    reportes = Reportes(sistema)

    # Cargar base de datos de afiliaciones
    afiliador.cargar_base_datos()

    # Generar entidades admitidas
    taxis = generar_taxis_iniciales(num_taxis=12, sistema=sistema, solo_admitidos=True)
    clientes = generar_clientes_iniciales(num_clientes=18, sistema=sistema, solo_admitidos=True)

    # Lanzar hilos concurrentes
    for t in taxis:
        threading.Thread(target=t.run, name=f"Taxi-{t.id_taxi}", daemon=True).start()
    for c in clientes:
        threading.Thread(target=c.run, name=f"Cliente-{c.id_cliente}", daemon=True).start()

    # Programar cierre contable diario
    programar_cierre_diario(sistema)

    def programar_reporte_mensual():
        """
        Genera reporte mensual automáticamente el primer minuto de cada mes.
        """
        while True:
            ahora = datetime.now()
            if ahora.day == 1 and ahora.hour == 0 and ahora.minute == 1:
                reportes.generar_reporte_mensual()
                time.sleep(60)
            time.sleep(5)
    threading.Thread(target=programar_reporte_mensual, name="Scheduler-Reporte-Mensual", daemon=True).start()

    # Iniciar GUI
    iniciar_gui(sistema, clientes, taxis, afiliador, reportes)

if __name__ == "__main__":
    main()
