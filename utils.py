# utils.py
"""
Utilidades del sistema:
- Distancias euclidianas, movimiento incremental, costo de viaje, ETA aproximada.
- Conversión de coordenadas a canvas (mapa normalizado).
- Generación de entidades iniciales respetando afiliación (solo admitidos).
- Inicialización de archivos JSON si están vacíos (data/*).
"""

import math
import random
import json
from pathlib import Path

DATA_DIR = Path("data")

def distancia_euclidiana(p1, p2):
    """Distancia euclidiana en el plano normalizado (0..1)."""
    x1, y1 = p1
    x2, y2 = p2
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def mover_hacia(origen, destino, paso=0.01):
    """Desplaza un punto origen hacia destino en 'paso' unidades (clamp a [0,1])."""
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
    """Tarifa simple: base fija + distancia * factor."""
    dist = distancia_euclidiana(origen, destino)
    base = 3.0
    factor = 10.0
    return round(base + dist * factor, 2)

def rnd_coord():
    """Genera coordenadas aleatorias dentro de un margen del mapa."""
    return (round(random.uniform(0.05, 0.95), 3), round(random.uniform(0.05, 0.95), 3))

def to_canvas_coords(x, y, width, height, pad):
    """Convierte coordenadas normalizadas (0..1) a píxeles del canvas."""
    cx = pad + x * (width - 2 * pad)
    cy = pad + y * (height - 2 * pad)
    return cx, cy

def to_eta(origen, destino, velocidad=0.2):
    """ETA aproximado (segundos) usando distancia/velocidad."""
    dist = distancia_euclidiana(origen, destino)
    return dist / max(1e-6, velocidad)

def ensure_data_files():
    """
    Crea archivos JSON con contenido válido si están ausentes o vacíos.
    Evita errores de JSONDecode al iniciar el sistema.
    """
    DATA_DIR.mkdir(exist_ok=True)
    defaults = {
        "clientes.json": [],
        "taxis.json": [],
        "viajes.json": [],
        "contabilidad.json": {"ganancias_por_taxi": {}, "ganancia_empresa": 0.0, "ts": 0}
    }
    for fname, default in defaults.items():
        fpath = DATA_DIR / fname
        if not fpath.exists() or fpath.stat().st_size == 0:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(default, f)

def generar_taxis_iniciales(num_taxis, sistema, solo_admitidos=False):
    """
    Genera taxis iniciales apoyándose en data/taxis.json para respetar estados de afiliación.
    Si solo_admitidos=True, descarta registros rechazados.
    """
    from taxi import Taxi
    taxis_aff = []
    try:
        with open(DATA_DIR / "taxis.json", "r", encoding="utf-8") as f:
            taxis_aff = json.load(f)
    except Exception:
        taxis_aff = []

    taxis = []
    count = 0
    for _ in range(1000):  # margen amplio para encontrar suficientes admitidos
        if count >= num_taxis:
            break
        ubic = rnd_coord()
        calif = round(random.uniform(4.0, 5.0), 2)
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
    """
    Genera clientes iniciales apoyándose en data/clientes.json para respetar estados de afiliación.
    Si solo_admitidos=True, descarta registros rechazados.
    """
    from cliente import Cliente
    clientes_aff = []
    try:
        with open(DATA_DIR / "clientes.json", "r", encoding="utf-8") as f:
            clientes_aff = json.load(f)
    except Exception:
        clientes_aff = []

    clientes = []
    count = 0
    for _ in range(1000):
        if count >= num_clientes:
            break
        orig = rnd_coord()
        dest = rnd_coord()
        admitido = True
        nombre = None
        tarjeta = "4111-xxxx-0000"
        if clientes_aff:
            rec = random.choice(clientes_aff)
            admitido = (rec.get("estado") == "admitido")
            nombre = rec.get("nombre")
            tarjeta = rec.get("tarjeta", tarjeta)
        if solo_admitidos and not admitido:
            continue
        clientes.append(Cliente(count, sistema, origen=orig, destino=dest, nombre=nombre, tarjeta=tarjeta, admitido=admitido))
        count += 1
    return clientes
