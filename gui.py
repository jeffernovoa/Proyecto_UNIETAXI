# gui.py
"""
Interfaz gráfica de UNIETAXI (Tkinter).
- Mapa con clientes (origen/destino) y taxis (libres/ocupados).
- Panel de estado y acciones (solicitar taxi, seguimiento, cierre, reporte).
- Pestaña de viajes activos (lista con ETA, progreso, costo, placa, conductor).
- Botón de detalle de viaje seleccionado (popup con información completa).
- Indicadores contables y pagos acumulados por taxi (incluye rating).
- Pestañas de afiliaciones (con filtros) y reportes de calidad.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
from utils import to_canvas_coords

MAP_WIDTH = 900
MAP_HEIGHT = 560
PADDING = 20

def iniciar_gui(sistema, clientes, taxis, afiliador, reportes):
    # Ventana base
    root = tk.Tk()
    root.title("UNIETAXI - Simulación completa")
    root.geometry("1300x760")

    # Layout principal
    mainframe = ttk.Frame(root, padding=8)
    mainframe.pack(fill="both", expand=True)
    mainframe.columnconfigure(0, weight=2)
    mainframe.columnconfigure(1, weight=3)
    mainframe.rowconfigure(0, weight=1)

    # Canvas (mapa)
    canvas = tk.Canvas(mainframe, width=MAP_WIDTH, height=MAP_HEIGHT, bg="white")
    canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    # Notebook (panel derecho)
    notebook = ttk.Notebook(mainframe)
    notebook.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

    # Tab: Estado y acciones
    tab_estado = ttk.Frame(notebook)
    notebook.add(tab_estado, text="Estado y acciones")
    info_var = tk.StringVar(value="Sistema iniciado.")
    ttk.Label(tab_estado, textvariable=info_var, anchor="w").pack(fill="x", pady=5)

    # Botones principales
    btn_solicitar = ttk.Button(tab_estado, text="Generar solicitud de taxi (cliente aleatorio)")
    btn_seguimiento = ttk.Button(tab_estado, text="Ejecutar seguimiento calidad (5 servicios)")
    btn_cerrar = ttk.Button(tab_estado, text="Cerrar contabilidad ahora")
    btn_reporte_mensual = ttk.Button(tab_estado, text="Generar reporte mensual")
    btn_solicitar.pack(fill="x", pady=4)
    btn_seguimiento.pack(fill="x", pady=4)
    btn_cerrar.pack(fill="x", pady=4)
    btn_reporte_mensual.pack(fill="x", pady=4)

    # Tab: Viajes activos
    tab_viajes = ttk.Frame(notebook)
    notebook.add(tab_viajes, text="Viajes activos")
    cols = ("viaje_id", "cliente", "taxi", "eta", "progreso", "costo", "placa", "conductor")
    tree_viajes = ttk.Treeview(tab_viajes, columns=cols, show="headings", height=14)
    for c in cols:
        tree_viajes.heading(c, text=c.capitalize())
        tree_viajes.column(c, width=120, anchor="center")
    tree_viajes.pack(fill="both", expand=True, pady=5)

    # Botón de detalle del viaje seleccionado (popup)
    btn_detalle = ttk.Button(tab_viajes, text="Ver detalle del viaje seleccionado")
    btn_detalle.pack(fill="x", pady=4)

    # Panel contable (ganancias y pagos por taxi)
    frame_contab = ttk.LabelFrame(tab_viajes, text="Indicadores contables")
    frame_contab.pack(fill="x", pady=6)
    lbl_ganancia = ttk.Label(frame_contab, text="Ganancia empresa: €0.00")
    lbl_ganancia.pack(side="left", padx=5)
    cols_pagos = ("taxi_id", "pago_acumulado", "rating")
    tree_pagos = ttk.Treeview(frame_contab, columns=cols_pagos, show="headings", height=6)
    for c in cols_pagos:
        tree_pagos.heading(c, text=c.capitalize())
        tree_pagos.column(c, width=120, anchor="center")
    tree_pagos.pack(fill="x", pady=4)

    # Tab: Afiliaciones
    tab_afiliaciones = ttk.Frame(notebook)
    notebook.add(tab_afiliaciones, text="Afiliaciones")
    cols_a = ("tipo", "id", "estado", "motivo")
    tree_afiliaciones = ttk.Treeview(tab_afiliaciones, columns=cols_a, show="headings", height=15)
    for c in cols_a:
        tree_afiliaciones.heading(c, text=c.capitalize())
        tree_afiliaciones.column(c, width=140, anchor="center")
    tree_afiliaciones.pack(fill="both", expand=True, pady=5)

    # Filtros de afiliación
    frame_filtros = ttk.Frame(tab_afiliaciones)
    frame_filtros.pack(fill="x", pady=5)
    estado_var = tk.StringVar(value="todos")
    ttk.Label(frame_filtros, text="Filtro estado:").pack(side="left", padx=5)
    ttk.Combobox(frame_filtros, values=["todos", "admitido", "rechazado"], textvariable=estado_var, width=12).pack(side="left")
    ttk.Button(frame_filtros, text="Aplicar filtro", command=lambda: refrescar_afiliaciones()).pack(side="left", padx=5)

    # Tab: Reportes de calidad
    tab_calidad = ttk.Frame(notebook)
    notebook.add(tab_calidad, text="Reportes de calidad")
    cols_q = ("entidad", "id", "calificacion_promedio", "viajes")
    tree_calidad = ttk.Treeview(tab_calidad, columns=cols_q, show="headings", height=15)
    for c in cols_q:
        tree_calidad.heading(c, text=c.capitalize())
        tree_calidad.column(c, width=160, anchor="center")
    tree_calidad.pack(fill="both", expand=True, pady=5)

    # Dibujo del mapa
    def draw_grid():
        """Dibuja una cuadrícula ligera en el canvas para referencia visual."""
        for i in range(10):
            canvas.create_line(PADDING, PADDING + i * (MAP_HEIGHT - 2 * PADDING) / 9,
                               MAP_WIDTH - PADDING, PADDING + i * (MAP_HEIGHT - 2 * PADDING) / 9,
                               fill="#f0f0f0")
            canvas.create_line(PADDING + i * (MAP_WIDTH - 2 * PADDING) / 9, PADDING,
                               PADDING + i * (MAP_WIDTH - 2 * PADDING) / 9, MAP_HEIGHT - PADDING,
                               fill="#f0f0f0")

    def draw_entities():
        """Dibuja clientes y taxis; muestra coordenadas origen→destino por cliente."""
        canvas.delete("all")
        draw_grid()

        # Clientes: origen (color por estado) y destino azul
        for cliente in clientes:
            ox, oy = to_canvas_coords(*cliente.origen, MAP_WIDTH, MAP_HEIGHT, PADDING)
            dx, dy = to_canvas_coords(*cliente.destino, MAP_WIDTH, MAP_HEIGHT, PADDING)
            color = "purple" if cliente.en_viaje else ("green" if cliente.solicitud_enviada else "gray")
            canvas.create_oval(ox - 6, oy - 6, ox + 6, oy + 6, fill=color, outline="")
            canvas.create_oval(dx - 5, dy - 5, dx + 5, dy + 5, fill="blue", outline="")
            canvas.create_text(ox + 10, oy - 12, text=f"C{cliente.id_cliente} ({cliente.origen}→{cliente.destino})", fill="#333", anchor="w")

        # Taxis: triángulos; naranja si ocupados, amarillo si libres
        for taxi in taxis:
            tx, ty = to_canvas_coords(*taxi.ubicacion, MAP_WIDTH, MAP_HEIGHT, PADDING)
            points = [tx, ty - 9, tx - 9, ty + 9, tx + 9, ty + 9]
            color = "orange" if taxi.ocupado else "yellow"
            canvas.create_polygon(points, fill=color, outline="#444")
            canvas.create_text(tx + 12, ty - 12, text=f"T{taxi.id_taxi} ({taxi.calificacion:.1f})", fill="#333", anchor="w")

        # Info de estado global
        info_var.set(f"Solicitudes en cola: {sistema.num_solicitudes()} | Viajes activos: {sistema.viajes_activos()} | Ganancia empresa: €{sistema.ganancia_empresa:.2f}")

    def refrescar_viajes():
        """Rellena tabla de viajes activos y actualiza indicadores contables/pagos."""
        tree_viajes.delete(*tree_viajes.get_children())
        activos = sistema.listar_viajes_activos()
        for v in activos:
            viaje_id = f"{v['cliente_id']}-{v['taxi_id']}"
            eta = sistema.calcular_eta(v)
            progreso = f"{int(v.get('progreso', 0) * 100)}%"
            costo = f"€{v['costo_estimado']:.2f}"
            tree_viajes.insert("", "end", values=(
                viaje_id, v['cliente_id'], v['taxi_id'], f"{eta:.1f}s", progreso, costo, v['placa_taxi'], v['conductor']
            ))

        tree_pagos.delete(*tree_pagos.get_children())
        lbl_ganancia.config(text=f"Ganancia empresa: €{sistema.ganancia_empresa:.2f}")
        for tid, monto in sistema.ganancias_por_taxi.items():
            prom, n = sistema.rating_taxi.get(int(tid), (0.0, 0))
            tree_pagos.insert("", "end", values=(tid, f"€{monto:.2f}", f"{prom:.2f} ({n})"))

    def refrescar_afiliaciones():
        """Actualiza tabla de afiliaciones con filtro de estado."""
        tree_afiliaciones.delete(*tree_afiliaciones.get_children())
        filtro = estado_var.get()
        for c in afiliador.registro_clientes:
            if filtro != "todos" and c["estado"] != filtro:
                continue
            tree_afiliaciones.insert("", "end", values=("cliente", c["id"], c["estado"], c["motivo"]))
        for t in afiliador.registro_taxis:
            if filtro != "todos" and t["estado"] != filtro:
                continue
            tree_afiliaciones.insert("", "end", values=("taxi", t["id"], t["estado"], t["motivo"]))

    def refrescar_calidad():
        """Actualiza tabla de reportes de calidad (promedios y cantidad)."""
        tree_calidad.delete(*tree_calidad.get_children())
        por_taxi = sistema.agregacion_calidad_por_taxi()
        for taxi_id, (prom, cant) in por_taxi.items():
            tree_calidad.insert("", "end", values=("taxi", taxi_id, f"{prom:.2f}", cant))
        por_cliente = sistema.agregacion_calidad_por_cliente()
        for cliente_id, (prom, cant) in por_cliente.items():
            tree_calidad.insert("", "end", values=("cliente", cliente_id, f"{prom:.2f}", cant))

    def tick():
        """Bucle de refresco periódico del mapa y viajes activos."""
        draw_entities()
        refrescar_viajes()
        root.after(500, tick)

    def solicitar_cliente_aleatorio():
        """Genera una solicitud para un cliente aleatorio admitido que aún no haya solicitado."""
        candidatos = [c for c in clientes if c.admitido and not c.solicitud_enviada]
        if not candidatos:
            messagebox.showinfo("UNIETAXI", "Todos los clientes admitidos ya enviaron solicitud.")
            return
        c = random.choice(candidatos)
        c.empujar_solicitud()
        messagebox.showinfo("UNIETAXI", f"Solicitud del cliente {c.id_cliente} enviada.")
        refrescar_viajes()

    def cerrar_contabilidad():
        """Ejecuta el cierre contable manual (persistencia contabilidad)."""
        sistema.cierre_contable()
        messagebox.showinfo("UNIETAXI", "Cierre contable ejecutado y guardado.")
        refrescar_viajes()

    def seguimiento_aleatorio():
        """Marca hasta 5 viajes finalizados como auditados."""
        sistema.seguimiento_calidad()
        messagebox.showinfo("UNIETAXI", "Seguimiento de 5 servicios finalizados ejecutado.")
        refrescar_calidad()

    def generar_reporte_mensual():
        """Genera reporte mensual (docs/reporte_mensual.md)."""
        reportes.generar_reporte_mensual()
        messagebox.showinfo("UNIETAXI", "Reporte mensual generado en docs/reporte_mensual.md")

    def ver_detalle_viaje():
        """Muestra un popup con detalles del viaje seleccionado en la tabla."""
        sel = tree_viajes.selection()
        if not sel:
            messagebox.showinfo("UNIETAXI", "Selecciona un viaje primero.")
            return
        item = tree_viajes.item(sel[0])
        vals = item["values"]
        viaje_id, cliente_id, taxi_id, eta, progreso, costo, placa, conductor = vals
        detalle = (
            f"Viaje {viaje_id}\n"
            f"Cliente: {cliente_id}\n"
            f"Taxi: {taxi_id}\n"
            f"Placa: {placa}\n"
            f"Conductor: {conductor}\n"
            f"ETA: {eta}\n"
            f"Progreso: {progreso}\n"
            f"Costo estimado: {costo}"
        )
        messagebox.showinfo("Detalle del viaje", detalle)

    # Conectar botones
    btn_solicitar.configure(command=solicitar_cliente_aleatorio)
    btn_cerrar.configure(command=cerrar_contabilidad)
    btn_seguimiento.configure(command=seguimiento_aleatorio)
    btn_reporte_mensual.configure(command=generar_reporte_mensual)
    btn_detalle.configure(command=ver_detalle_viaje)

    # Primer refresco
    refrescar_afiliaciones()
    refrescar_calidad()
    tick()
    root.mainloop()
