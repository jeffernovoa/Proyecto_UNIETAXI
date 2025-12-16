# gui.py
"""
Interfaz gráfica Tkinter
- Mapa con taxis y clientes: origen/destino, color por estado.
- Panel de viajes activos con ETA en tiempo real y progreso.
- Panel de afiliaciones (admitidos/rechazados y motivos).
- Botones: generar solicitud, seguimiento de calidad, cierre contable manual.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
from utils import to_canvas_coords

MAP_WIDTH = 900
MAP_HEIGHT = 560
PADDING = 20

def iniciar_gui(sistema, clientes, taxis, afiliador, reportes):
    root = tk.Tk()
    root.title("UNIETAXI - Simulación completa")

    # Layout principal
    root.geometry("1200x720")
    mainframe = ttk.Frame(root, padding=8)
    mainframe.pack(fill="both", expand=True)

    # Canvas mapa
    canvas = tk.Canvas(mainframe, width=MAP_WIDTH, height=MAP_HEIGHT, bg="white")
    canvas.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)
    mainframe.columnconfigure(0, weight=1)
    mainframe.rowconfigure(0, weight=1)

    # Panel derecho - Tabs
    notebook = ttk.Notebook(mainframe)
    notebook.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    mainframe.columnconfigure(1, weight=1)

    # Tab: Estado y acciones
    tab_estado = ttk.Frame(notebook)
    notebook.add(tab_estado, text="Estado y acciones")

    info_var = tk.StringVar(value="Sistema iniciado.")
    ttk.Label(tab_estado, textvariable=info_var, anchor="w").pack(fill="x", pady=5)

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

    cols = ("viaje_id", "cliente", "taxi", "eta", "progreso", "costo")
    tree_viajes = ttk.Treeview(tab_viajes, columns=cols, show="headings", height=15)
    for c in cols:
        tree_viajes.heading(c, text=c.capitalize())
        tree_viajes.column(c, width=120, anchor="center")
    tree_viajes.pack(fill="both", expand=True, pady=5)

    # Tab: Afiliaciones
    tab_afiliaciones = ttk.Frame(notebook)
    notebook.add(tab_afiliaciones, text="Afiliaciones")

    cols_a = ("tipo", "id", "estado", "motivo")
    tree_afiliaciones = ttk.Treeview(tab_afiliaciones, columns=cols_a, show="headings", height=15)
    for c in cols_a:
        tree_afiliaciones.heading(c, text=c.capitalize())
        tree_afiliaciones.column(c, width=140, anchor="center")
    tree_afiliaciones.pack(fill="both", expand=True, pady=5)

    # Tab: Reportes calidad
    tab_calidad = ttk.Frame(notebook)
    notebook.add(tab_calidad, text="Reportes de calidad")

    cols_q = ("entidad", "id", "calificacion_promedio", "viajes")
    tree_calidad = ttk.Treeview(tab_calidad, columns=cols_q, show="headings", height=15)
    for c in cols_q:
        tree_calidad.heading(c, text=c.capitalize())
        tree_calidad.column(c, width=160, anchor="center")
    tree_calidad.pack(fill="both", expand=True, pady=5)

    # Botones de filtro/refresh
    frame_actions = ttk.Frame(tab_estado)
    frame_actions.pack(fill="x", pady=6)
    ttk.Button(frame_actions, text="Refrescar paneles", command=lambda: (refrescar_afiliaciones(), refrescar_calidad())).pack(side="left")

    # Mapa: funciones de dibujo
    def draw_grid():
        for i in range(10):
            canvas.create_line(PADDING, PADDING + i * (MAP_HEIGHT - 2 * PADDING) / 9,
                               MAP_WIDTH - PADDING, PADDING + i * (MAP_HEIGHT - 2 * PADDING) / 9,
                               fill="#f0f0f0")
            canvas.create_line(PADDING + i * (MAP_WIDTH - 2 * PADDING) / 9, PADDING,
                               PADDING + i * (MAP_WIDTH - 2 * PADDING) / 9, MAP_HEIGHT - PADDING,
                               fill="#f0f0f0")

    def draw_entities():
        canvas.delete("all")
        draw_grid()

        # Clientes
        for cliente in clientes:
            ox, oy = to_canvas_coords(*cliente.origen, MAP_WIDTH, MAP_HEIGHT, PADDING)
            dx, dy = to_canvas_coords(*cliente.destino, MAP_WIDTH, MAP_HEIGHT, PADDING)
            color = "purple" if cliente.en_viaje else ("green" if cliente.solicitud_enviada else "gray")
            canvas.create_oval(ox - 6, oy - 6, ox + 6, oy + 6, fill=color, outline="")
            canvas.create_oval(dx - 5, dy - 5, dx + 5, dy + 5, fill="blue", outline="")
            canvas.create_text(ox + 10, oy - 12, text=f"C{cliente.id_cliente}", fill="#333", anchor="w")

        # Taxis
        for taxi in taxis:
            tx, ty = to_canvas_coords(*taxi.ubicacion, MAP_WIDTH, MAP_HEIGHT, PADDING)
            points = [tx, ty - 9, tx - 9, ty + 9, tx + 9, ty + 9]
            color = "orange" if taxi.ocupado else "yellow"
            canvas.create_polygon(points, fill=color, outline="#444")
            canvas.create_text(tx + 12, ty - 12, text=f"T{taxi.id_taxi}", fill="#333", anchor="w")

        # Info del sistema
        info_var.set(f"Solicitudes en cola: {sistema.num_solicitudes()} | Viajes activos: {sistema.viajes_activos()} | Ganancia empresa: €{sistema.ganancia_empresa:.2f}")

    def refrescar_viajes():
        tree_viajes.delete(*tree_viajes.get_children())
        activos = sistema.listar_viajes_activos()
        for v in activos:
            viaje_id = f"{v['cliente_id']}-{v['taxi_id']}"
            eta = sistema.calcular_eta(v)
            progreso = f"{int(v.get('progreso', 0) * 100)}%"
            costo = f"€{v['costo_estimado']:.2f}"
            tree_viajes.insert("", "end", values=(viaje_id, v['cliente_id'], v['taxi_id'], f"{eta:.1f}s", progreso, costo))

    def refrescar_afiliaciones():
        tree_afiliaciones.delete(*tree_afiliaciones.get_children())
        # Clientes
        for c in afiliador.registro_clientes:
            tree_afiliaciones.insert("", "end", values=("cliente", c["id"], c["estado"], c["motivo"]))
        # Taxis
        for t in afiliador.registro_taxis:
            tree_afiliaciones.insert("", "end", values=("taxi", t["id"], t["estado"], t["motivo"]))

    def refrescar_calidad():
        tree_calidad.delete(*tree_calidad.get_children())
        # Agregación por taxis
        por_taxi = sistema.agregacion_calidad_por_taxi()
        for taxi_id, (prom, cant) in por_taxi.items():
            tree_calidad.insert("", "end", values=("taxi", taxi_id, f"{prom:.2f}", cant))
        # Agregación por clientes
        por_cliente = sistema.agregacion_calidad_por_cliente()
        for cliente_id, (prom, cant) in por_cliente.items():
            tree_calidad.insert("", "end", values=("cliente", cliente_id, f"{prom:.2f}", cant))

    def tick():
        draw_entities()
        refrescar_viajes()
        root.after(500, tick)

    def solicitar_cliente_aleatorio():
        candidatos = [c for c in clientes if not c.solicitud_enviada]
        if not candidatos:
            messagebox.showinfo("UNIETAXI", "Todos los clientes ya enviaron solicitud.")
            return
        c = random.choice(candidatos)
        c.empujar_solicitud()
        # Al asignar, el sistema incluye datos de taxi y ETA en el viaje
        messagebox.showinfo("UNIETAXI", f"Solicitud del cliente {c.id_cliente} enviada.")

    def cerrar_contabilidad():
        sistema.cierre_contable()
        messagebox.showinfo("UNIETAXI", "Cierre contable ejecutado y guardado.")

    def seguimiento_aleatorio():
        sistema.seguimiento_calidad()
        messagebox.showinfo("UNIETAXI", "Seguimiento de 5 servicios finalizados ejecutado.")

    def generar_reporte_mensual():
        reportes.generar_reporte_mensual()
        messagebox.showinfo("UNIETAXI", "Reporte mensual generado en docs/reporte_mensual.md")

    btn_solicitar.configure(command=solicitar_cliente_aleatorio)
    btn_cerrar.configure(command=cerrar_contabilidad)
    btn_seguimiento.configure(command=seguimiento_aleatorio)
    btn_reporte_mensual.configure(command=generar_reporte_mensual)

    refrescar_afiliaciones()
    refrescar_calidad()
    tick()
    root.mainloop()
