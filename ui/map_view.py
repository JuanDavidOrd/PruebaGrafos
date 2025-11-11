from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
from collections import Counter
from PySide6.QtCore import QTimer
from typing import List, Tuple, Optional

class MapView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fig = Figure(figsize=(5, 5))
        self.canvas = FigureCanvas(self.fig)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        self.animation_data = None
        self.current_step = 0

    def draw(self, G, memberships, const_colors, overlay_edges=None, highlight_stars=None, animate=False):
        """
        Dibuja el mapa con opciones de animación.
        
        Args:
            G: SpaceGraph
            memberships: list de memberships
            const_colors: dict de colores por constelación
            overlay_edges: lista de aristas a resaltar
            highlight_stars: lista de estrellas a resaltar (visitadas)
            animate: si True, anima la ruta
        """
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        # --- Aristas base ---
        for u, v, d in G.G.edges(data=True):
            x1, y1 = G.G.nodes[u]["x"], G.G.nodes[u]["y"]
            x2, y2 = G.G.nodes[v]["x"], G.G.nodes[v]["y"]
            if x1 is None or y1 is None or x2 is None or y2 is None:
                continue
            if d.get("blocked", False):
                ax.plot([x1, x2], [y1, y2], linestyle="--", alpha=0.3, color="gray")
            else:
                ax.plot([x1, x2], [y1, y2], alpha=0.5, color="black")

        # --- Resaltado multi-constelación ---
        count = Counter([m.starId for m in memberships])
        multi = {sid for sid, c in count.items() if c > 1}

        # --- Nodos ---
        for nid, n in G.G.nodes(data=True):
            x, y = n.get("x"), n.get("y")
            if x is None or y is None:
                continue

            if nid in multi:
                color = "#d62728"  # rojo
            else:
                const_ids = [m.constellationId for m in memberships if m.starId == nid]
                color = const_colors.get(const_ids[0], "blue") if const_ids else "blue"

            ax.scatter([x], [y], s=40, c=color)
            ax.text(x + 1, y + 1, str(nid), fontsize=8, color="black")

        # --- Overlay de ruta con resaltado de estrellas visitadas ---
        if highlight_stars:
            for star_id in highlight_stars:
                if star_id in G.G.nodes:
                    x, y = G.G.nodes[star_id]["x"], G.G.nodes[star_id]["y"]
                    if x is not None and y is not None:
                        # Dibujar un círculo grande alrededor de la estrella visitada
                        circle = Circle((x, y), 3, color="yellow", alpha=0.6, fill=True)
                        ax.add_patch(circle)

        # --- Overlay de ruta (Paso 2/3) con animación opcional ---
        if overlay_edges:
            edge_count = len(overlay_edges)
            for idx, (u, v) in enumerate(overlay_edges):
                if u in G.G.nodes and v in G.G.nodes:
                    x1, y1 = G.G.nodes[u]["x"], G.G.nodes[u]["y"]
                    x2, y2 = G.G.nodes[v]["x"], G.G.nodes[v]["y"]
                    if None not in (x1, y1, x2, y2):
                        # Si animate es True, mostrar con degradado de color
                        if animate:
                            # Degradado de color: azul -> verde -> rojo
                            intensity = idx / max(1, edge_count - 1) if edge_count > 1 else 0
                            if intensity < 0.5:
                                # Azul a verde
                                r = 0
                                g = intensity * 2
                                b = 1 - (intensity * 2)
                            else:
                                # Verde a rojo
                                r = (intensity - 0.5) * 2
                                g = 1 - ((intensity - 0.5) * 2)
                                b = 0
                            color = (r, g, b)
                            linewidth = 2.0 + (intensity * 2.0)
                        else:
                            color = "#2ca02c"
                            linewidth = 2.8
                        
                        ax.plot([x1, x2], [y1, y2], linewidth=linewidth, color=color, alpha=0.9)

        ax.set_xlim(0, 200)
        ax.set_ylim(0, 200)
        ax.set_xlabel("um")
        ax.set_ylabel("um")
        ax.set_title("Mapa de Constelaciones")
        self.canvas.draw()
