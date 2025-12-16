# utils.py
"""
Utilidades:
- Distancias, movimiento, costo, ETA.
- Conversión a coordenadas de canvas.
- Generación de entidades iniciales con filtro de afiliación.
- Persistencia básica y preparación de archivos JSON.
"""

import math
import random
import json
from pathlib import Path

DATA_DIR = Path("data")

def distancia_euclidiana(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def mover_hacia(origen, destino, paso=0.01):
    ox, oy = origen
    dx, dy = destino
    vecx = dx - ox
    vecy = dy - oy
    dist = math.sqrt(vecx**2 + vecy**2)
    if dist == 0:
        return origen
    ux, uy = vecx / dist, vecy / dist
    nx = ox + ux * paso
    ny = oy + uy * paso
    nx = min(1.0, max(0.0, nx))
    ny = min(1.0, max(0.0, ny))
    return (nx, ny)

def calcular_costo_viaje(origen, destino):
    dist = distancia_euclidiana(origen, destino)
    base = 3.0
    factor = 10.0
    return round(base + dist * factor, 2)

def rnd_coord():
    return (round(random.uniform(0.05, 0.95), 3), round(random.uniform(0.05, 0.95), 3))

def to_canvas_coords(x, y, width, height, pad):
    cx = pad + x * (width - 2 * pad)
    cy = pad + y * (height - 2 * pad)
    return cx, cy

def to_eta(origen, destino, velocidad=0.2):
    """ETA en segundos: distancia/velocidad (velocidad en unidades de mapa por segundo)."""
    dist = distancia_euclidiana(origen, destino)
    return dist / max(1e-6, velocidad)

def ensure_data_files():
    DATA_DIR.mkdir(exist_ok=True)
    for fname in ["clientes.json", "taxis.json", "viajes.json", "contabilidad.json"]:
        fpath = DATA_DIR / fname
        if not fpath.exists():
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump([] if "json" in fname and fname != "contabilidad.json" else {}, f)

def generar_taxis_iniciales(num_taxis, sistema, solo_admitidos=False):
    from taxi import Taxi
    # Cargar afiliaciones de taxis
    taxis_aff = []
    try:
        with open(DATA_DIR / "taxis.json", "r", encoding="utf-8") as f:
            taxis_aff = json.load(f)
    except Exception:
        taxis_aff = []

    taxis = []
    count = 0
    for i in range(1000):  # amplio para encontrar admitidos
        if count >= num_taxis:
            break
        ubic = rnd_coord()
        calif = round(random.uniform(4.0, 5.0), 2)
        # Si hay registro de afiliación, respétalo
        admitido = True
        nombre = None
        placa = None
        if taxis_aff:
            rec = random.choice(taxis_aff)
            admitido = (rec.get("estado") == "admitido")
            nombre = rec.get("conductor")
            placa = rec.get("placa")
        if solo_admitidos and not admitido:
            continue
        taxis.append(Taxi(count, sistema, ubicacion_inicial=ubic, calificacion=calif, nombre_conductor=nombre, placa=placa, admitido=admitido))
        count += 1
    return taxis

def generar_clientes_iniciales(num_clientes, sistema, solo_admitidos=False):
    from cliente import Cliente
    clientes_aff = []
    try:
        with open(DATA_DIR / "clientes.json", "r", encoding="utf-8") as f:
            clientes_aff = json.load(f)
    except Exception:
        clientes_aff = []

    clientes = []
    count = 0
    for i in range(1000):
        if count >= num_clientes:
            break
        orig = rnd_coord()
        dest = rnd_coord()
        admitido = True
        nombre = None
        if clientes_aff:
            rec = random.choice(clientes_aff)
            admitido = (rec.get("estado") == "admitido")
            nombre = rec.get("nombre")
        if solo_admitidos and not admitido:
            continue
        clientes.append(Cliente(count, sistema, origen=orig, destino=dest, nombre=nombre, admitido=admitido))
        count += 1
    return clientes
