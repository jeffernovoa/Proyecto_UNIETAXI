# sistema_atencion.py
"""
Núcleo del sistema de atención:
- Cola de solicitudes, matching por distancia con desempate por calificación.
- Asignación de viaje con datos del taxi (placa, conductor) y ETA inicial.
- Finalización del viaje, contabilidad (20% empresa) y liberación del taxi.
- Seguimiento de calidad (5 aleatorios).
- Cierre contable y persistencia en JSON.
- Agregación de calificaciones por taxi y por cliente.
"""

import threading
import time
import random
import json
from queue import Queue
from pathlib import Path
from utils import distancia_euclidiana, calcular_costo_viaje, to_eta, ensure_data_files

DATA_DIR = Path("data")

class SistemaAtencion:
    def __init__(self):
        # Recursos compartidos
        self.solicitudes = Queue()  # Clientes esperando servicio
        self.taxis_disponibles = []  # Lista de objetos Taxi
        self.lock_taxis = threading.Lock()
        self.lock_contabilidad = threading.Lock()
        self.lock_viajes = threading.Lock()
        self.viajes = []  # Registro de viajes (activos/finalizados)
        self.ganancias_por_taxi = {}  # taxi_id -> monto acumulado
        self.ganancia_empresa = 0.0
        self.radio_busqueda = 0.2
        self.max_seguimientos_diarios = 5

        ensure_data_files()

    # Gestión de taxis
    def registrar_taxi_disponible(self, taxi):
        with self.lock_taxis:
            if taxi not in self.taxis_disponibles:
                self.taxis_disponibles.append(taxi)

    def desregistrar_taxi_disponible(self, taxi):
        with self.lock_taxis:
            if taxi in self.taxis_disponibles:
                self.taxis_disponibles.remove(taxi)

    def num_solicitudes(self):
        return self.solicitudes.qsize()

    def viajes_activos(self):
        with self.lock_viajes:
            return len([v for v in self.viajes if v.get("estado") == "activo"])

    def listar_viajes_activos(self):
        with self.lock_viajes:
            return [v for v in self.viajes if v.get("estado") == "activo"]

    # Clientes
    def recibir_solicitud(self, cliente):
        self.solicitudes.put(cliente)

    # Matching cliente-taxi
    def procesar_solicitudes(self):
        while not self.solicitudes.empty():
            cliente = self.solicitudes.get()
            taxi_asignado = self.seleccionar_taxi_cliente(cliente)
            if taxi_asignado:
                self.asignar_viaje(cliente, taxi_asignado)
                cliente.solicitud_enviada = True
            else:
                # Reintento posterior
                self.solicitudes.put(cliente)
                break

    def seleccionar_taxi_cliente(self, cliente):
        candidatos = []
        with self.lock_taxis:
            for taxi in self.taxis_disponibles:
                if taxi.ocupado:
                    continue
                d = distancia_euclidiana(taxi.ubicacion, cliente.origen)
                if d <= self.radio_busqueda:
                    candidatos.append((d, taxi))
        if not candidatos:
            return None
        candidatos.sort(key=lambda dt: (dt[0], -dt[1].calificacion))
        return candidatos[0][1]

    def asignar_viaje(self, cliente, taxi):
        taxi.ocupado = True
        self.desregistrar_taxi_disponible(taxi)

        costo = calcular_costo_viaje(cliente.origen, cliente.destino)
        eta_pickup = to_eta(taxi.ubicacion, cliente.origen, velocidad=0.2)  # segundos estimados
        viaje = {
            "cliente_id": cliente.id_cliente,
            "taxi_id": taxi.id_taxi,
            "origen": cliente.origen,
            "destino": cliente.destino,
            "estado": "activo",
            "inicio_ts": time.time(),
            "costo_estimado": costo,
            "calificacion_cliente": None,
            "placa_taxi": taxi.placa,
            "conductor": taxi.nombre_conductor,
            "eta_pickup": eta_pickup,
            "progreso": 0.0
        }
        with self.lock_viajes:
            self.viajes.append(viaje)

        taxi.asignar_servicio(cliente)

    def actualizar_progreso(self, taxi, progreso):
        # Progreso [0,1] del viaje del taxi actual
        with self.lock_viajes:
            for v in self.viajes:
                if v["estado"] == "activo" and v["taxi_id"] == taxi.id_taxi and taxi.cliente_actual and v["cliente_id"] == taxi.cliente_actual.id_cliente:
                    v["progreso"] = max(0.0, min(1.0, progreso))
                    break

    def calcular_eta(self, viaje):
        """
        ETA simple:
        - Si el viaje activo con progreso p: ETA = (1-p)*T_total aprox.
        - Usamos distancia origen->destino y velocidad media del taxi en servicio (0.24).
        """
        dist_total = distancia_euclidiana(viaje["origen"], viaje["destino"])
        t_total = dist_total / 0.24
        p = viaje.get("progreso", 0.0)
        return max(0.0, (1.0 - p) * t_total)

    def finalizar_viaje(self, taxi, cliente, calificacion):
        costo = calcular_costo_viaje(cliente.origen, cliente.destino)
        comision_empresa = costo * 0.20
        pago_taxista = costo - comision_empresa

        with self.lock_contabilidad:
            self.ganancia_empresa += comision_empresa
            self.ganancias_por_taxi[taxi.id_taxi] = self.ganancias_por_taxi.get(taxi.id_taxi, 0.0) + pago_taxista
            self.persistir_contabilidad()

        with self.lock_viajes:
            for v in self.viajes:
                if v["cliente_id"] == cliente.id_cliente and v["taxi_id"] == taxi.id_taxi and v["estado"] == "activo":
                    v["estado"] = "finalizado"
                    v["fin_ts"] = time.time()
                    v["calificacion_cliente"] = calificacion
                    break
            self.persistir_viajes()

        taxi.ocupado = False
        self.registrar_taxi_disponible(taxi)

    # Seguimiento aleatorio de 5 servicios
    def seguimiento_calidad(self):
        with self.lock_viajes:
            finalizados = [v for v in self.viajes if v.get("estado") == "finalizado"]
        if not finalizados:
            return
        seleccion = random.sample(finalizados, k=min(self.max_seguimientos_diarios, len(finalizados)))
        with self.lock_viajes:
            for v in seleccion:
                v["seguimiento_auditoria"] = True
            self.persistir_viajes()

    # Contabilidad y persistencia
    def cierre_contable(self):
        """Cierra contabilidad del día (simulado) y persiste a JSON."""
        with self.lock_contabilidad:
            # En sistema real: transferencias y liquidaciones
            self.persistir_contabilidad()

    def persistir_viajes(self):
        DATA_DIR.mkdir(exist_ok=True)
        with open(DATA_DIR / "viajes.json", "w", encoding="utf-8") as f:
            json.dump(self.viajes, f, ensure_ascii=False, indent=2)

    def persistir_contabilidad(self):
        DATA_DIR.mkdir(exist_ok=True)
        payload = {
            "ganancias_por_taxi": self.ganancias_por_taxi,
            "ganancia_empresa": self.ganancia_empresa,
            "ts": time.time()
        }
        with open(DATA_DIR / "contabilidad.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # Agregación de calidad
    def agregacion_calidad_por_taxi(self):
        res = {}
        with self.lock_viajes:
            for v in self.viajes:
                if v.get("estado") == "finalizado" and v.get("calificacion_cliente") is not None:
                    tid = v["taxi_id"]
                    prom, n = res.get(tid, (0.0, 0))
                    n2 = n + 1
                    prom2 = (prom * n + v["calificacion_cliente"]) / n2
                    res[tid] = (prom2, n2)
        return res

    def agregacion_calidad_por_cliente(self):
        res = {}
        with self.lock_viajes:
            for v in self.viajes:
                if v.get("estado") == "finalizado" and v.get("calificacion_cliente") is not None:
                    cid = v["cliente_id"]
                    prom, n = res.get(cid, (0.0, 0))
                    n2 = n + 1
                    prom2 = (prom * n + v["calificacion_cliente"]) / n2
                    res[cid] = (prom2, n2)
        return res
