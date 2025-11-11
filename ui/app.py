from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton
)

from core.io.json_loader import load_universe
from core.graph.space_graph import SpaceGraph
from ui.map_view import MapView
from ui.params_panel import ParamsPanel
from ui.star_editor import StarEditor
from ui.edge_manager import EdgeManager
from ui.audio_manager import get_audio_manager
from ui.report_dialog import ReportDialog
from core.reports.detailed_report import generate_detailed_report, format_report_for_display
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect
import os

# Reglas de simulación
from core.sim.rules import compute_route_step2
from core.sim.simulator import run_full_step3


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NASA Burro – Grafos")

        # --- Estado ---
        self.u = None
        self.G = None
        self._loading = False  # evita doble ejecución al abrir archivo

        # --- Vista del mapa ---
        self.view = MapView(self)

        # --- Panel lateral (parámetros) ---
        self.params = ParamsPanel(self)

        # --- Botones ---
        self.btn_load   = QPushButton("Cargar JSON")
        self.btn_edit   = QPushButton("Editar estrellas…")
        self.btn_edges  = QPushButton("Bloquear/habilitar vías…")
        self.btn_route2 = QPushButton("Punto 2")
        self.btn_route3 = QPushButton("Punto 3")

        # Estado inicial de botones
        for b in (self.btn_edit, self.btn_edges, self.btn_route2, self.btn_route3, self.params.btn_edit_stars):
            b.setEnabled(False)

        # Conexiones (una sola vez)
        self.btn_load.clicked.connect(self.on_load)
        self.btn_edit.clicked.connect(self.on_edit_stars)
        self.btn_edges.clicked.connect(self.on_manage_edges) 
        self.params.btn_edit_stars.clicked.connect(self.on_edit_stars)
        self.btn_route2.clicked.connect(self.on_route2)
        self.btn_route3.clicked.connect(self.on_route3)

        # --- Layout lateral ---
        side = QVBoxLayout()
        side.addWidget(self.btn_load)
        side.addWidget(self.btn_edit)
        side.addWidget(self.btn_edges) 
        side.addWidget(self.btn_route2)
        side.addWidget(self.btn_route3)
        side.addWidget(self.params)
        side.addStretch(1)

        # --- Layout central ---
        central = QWidget(self)
        lay = QHBoxLayout(central)
        lay.addWidget(self.view, 1)
        lay.addLayout(side)
        self.setCentralWidget(central)

    # -------------------------
    # Acciones
    # -------------------------
    def on_load(self):
        if self._loading:
            return
        self._loading = True
        try:
            path, _ = QFileDialog.getOpenFileName(
                self, "Abrir universo", filter="JSON (*.json)"
            )
            if not path:
                return

            # Carga y dibuja
            self.u = load_universe(path)      # convierte si hace falta
            self.G = SpaceGraph(self.u)
            const_colors = {c.id: c.color for c in self.u.constellations}
            self.view.draw(self.G, self.u.memberships, const_colors)

            # Habilita panel y botones
            self.params.set_from_universe(self.u)
            self.btn_edit.setEnabled(True)
            self.btn_edges.setEnabled(True)              
            self.btn_route2.setEnabled(True)
            self.btn_route3.setEnabled(True)
            self.params.btn_edit_stars.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self._loading = False

    def on_edit_stars(self):
        if not self.u:
            return
        dlg = StarEditor(self.u, self)
        if dlg.exec():
            # Redibuja por si cambió algo visual
            const_colors = {c.id: c.color for c in self.u.constellations}
            self.view.draw(self.G, self.u.memberships, const_colors)

    def on_manage_edges(self): 
        if not (self.u and self.G):
            return
        dlg = EdgeManager(self.G.G, self)  # pasa el networkx.Graph interno
        if dlg.exec():
            # Redibuja para ver cambios (las vías bloqueadas salen grises punteadas)
            const_colors = {c.id: c.color for c in self.u.constellations}
            self.view.draw(self.G, self.u.memberships, const_colors)

    def on_route2(self):
        if not (self.u and self.G):
            return
        p = self.params.read_params()
        res = compute_route_step2(
            self.G,
            origin_id=p["origin"],
            health_txt=p["health"],
            energy_pct=float(p["energy"]),
            hay_kg=float(p["hay_kg"]),
            life_ly=float(p["life_ly"]),
        )
        if res is None:
            QMessageBox.warning(self, "Ruta – Paso 2", "No se pudo calcular la ruta (resultado vacío).")
            return

        const_colors = {c.id: c.color for c in self.u.constellations}
        overlay = getattr(res, "edges", None) or []
        
        # Dibujar con animación y estrellas visitadas resaltadas
        self.view.draw(self.G, self.u.memberships, const_colors, 
                      overlay_edges=overlay, 
                      highlight_stars=res.visited,
                      animate=True)

        msg = (
            f"Visitas: {len(res.path)}\n"
            f"Recorrido: {' → '.join(map(str, res.path))}\n"
            f"Energía restante: {res.remaining_energy:.2f}%\n"
            f"Vida restante: {res.remaining_life:.2f} a-luz\n"
            f"Motivo de parada: {res.reason}"
        )
        QMessageBox.information(self, "Ruta – Paso 2", msg)
        

    def on_route3(self):
        if not (self.u and self.G):
            return
        p = self.params.read_params()
        # Ejecutar la simulación completa (genera RunLog con pasos detallados)
        log = run_full_step3(
            self.u, self.G,
            origin_id=p["origin"],
            health_txt=p["health"],
            energy_pct=float(p["energy"]),
            hay_kg=float(p["hay_kg"]),
            life_ly=float(p["life_ly"]),
        )

        # Verificar si el burro murió
        if getattr(log, 'died', False):
            audio_manager = get_audio_manager()
            audio_manager.play_death_sound()
            QMessageBox.warning(self, "¡Burro Muerto!",
                                "El burro ha muerto durante el viaje.\n"
                                "La simulación se ha detenido.\n\n"
                                "Motivo: " + getattr(log, 'stop_reason', getattr(log, 'reason', '')))

        const_colors = {c.id: c.color for c in self.u.constellations}

        # Obtener aristas y estrellas visitadas de manera compatible con RunLog/RouteResult
        overlay = None
        if hasattr(log, 'edges'):
            try:
                overlay = log.edges() if callable(log.edges) else log.edges
            except Exception:
                overlay = getattr(log, 'edges', [])
        else:
            overlay = getattr(log, 'edges', [])

        visited = getattr(log, 'visited_order', getattr(log, 'visited', []))

        # Dibujar con animación
        self.view.draw(self.G, self.u.memberships, const_colors,
                       overlay_edges=overlay,
                       highlight_stars=visited,
                       animate=True)

        # Generar reporte detallado usando el RunLog (contendrá pasos completos)
        report = generate_detailed_report(
            log,
            self.u,
            self.u.memberships,
            output_dir="reports"
        )

        # Mostrar reporte en diálogo
        dlg = ReportDialog(report, self)
        dlg.exec()

        # Preparar mensaje resumen
        recorrido = getattr(log, 'visited_order', getattr(log, 'path', []))
        energia_rest = getattr(log, 'final_energy', getattr(log, 'remaining_energy', 0.0))
        vida_rest = getattr(log, 'final_life', getattr(log, 'remaining_life', 0.0))
        pasto_rest = getattr(log, 'final_grass', getattr(log, 'hay_left', 0.0))
        motivo = getattr(log, 'stop_reason', getattr(log, 'reason', ''))

        msg = (
            f"Visitas: {len(recorrido)}\n"
            f"Recorrido: {' → '.join(map(str, recorrido))}\n"
            f"Energía restante: {energia_rest:.2f}%\n"
            f"Vida restante: {vida_rest:.2f} a-luz\n"
            f"Pasto restante: {pasto_rest:.2f} kg\n"
            f"Motivo de parada: {motivo}"
        )
        QMessageBox.information(self, "Ruta – Paso 3", msg)


def run():
    import sys
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1100, 750)
    w.show()
    sys.exit(app.exec())
