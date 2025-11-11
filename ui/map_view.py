# ui/map_view.py  (solo se muestran las partes relevantes)
from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from collections import Counter

class MapView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fig = Figure(figsize=(5, 5))
        self.canvas = FigureCanvas(self.fig)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def draw(self, G, memberships, const_colors, overlay_edges=None):
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

        # --- Overlay de ruta (Paso 2) ---
        if overlay_edges:
            for (u, v) in overlay_edges:
                if u in G.G.nodes and v in G.G.nodes:
                    x1, y1 = G.G.nodes[u]["x"], G.G.nodes[u]["y"]
                    x2, y2 = G.G.nodes[v]["x"], G.G.nodes[v]["y"]
                    if None not in (x1, y1, x2, y2):
                        ax.plot([x1, x2], [y1, y2], linewidth=2.8, color="#2ca02c", alpha=0.9)

        ax.set_xlim(0, 200)
        ax.set_ylim(0, 200)
        ax.set_xlabel("um")
        ax.set_ylabel("um")
        ax.set_title("Mapa de Constelaciones")
        self.canvas.draw()
