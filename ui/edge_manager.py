# ui/edge_manager.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QAbstractItemView
)
from PySide6.QtCore import Qt

class EdgeManager(QDialog):
    """
    Dialogo para listar y (des)bloquear aristas del grafo.
    """
    COLS = ["u", "v", "distancia (a-luz)", "bloqueada"]

    def __init__(self, G, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bloquear / habilitar vías")
        self.G = G  # networkx Graph

        self.tbl = QTableWidget(0, len(self.COLS))
        self.tbl.setHorizontalHeaderLabels(self.COLS)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tbl.horizontalHeader().setStretchLastSection(True)

        self.btn_toggle = QPushButton("Alternar bloqueo")
        self.btn_block  = QPushButton("Bloquear")
        self.btn_open   = QPushButton("Habilitar")
        self.btn_close  = QPushButton("Cerrar")

        btns = QHBoxLayout()
        btns.addWidget(self.btn_toggle)
        btns.addWidget(self.btn_block)
        btns.addWidget(self.btn_open)
        btns.addStretch(1)
        btns.addWidget(self.btn_close)

        lay = QVBoxLayout(self)
        lay.addWidget(self.tbl)
        lay.addLayout(btns)

        self.btn_toggle.clicked.connect(self.on_toggle)
        self.btn_block.clicked.connect(lambda: self._set_selected(True))
        self.btn_open.clicked.connect(lambda: self._set_selected(False))
        self.btn_close.clicked.connect(self.accept)

        self._load()

    def _load(self):
        edges = list(self.G.edges(data=True))
        self.tbl.setRowCount(len(edges))
        for row, (u, v, d) in enumerate(edges):
            u_item = QTableWidgetItem(str(u))
            v_item = QTableWidgetItem(str(v))
            dist   = float(d.get("distance", 0.0))
            dist_item = QTableWidgetItem(f"{dist:.2f}")
            dist_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            blocked = bool(d.get("blocked", False))
            blk_item = QTableWidgetItem("Sí" if blocked else "No")
            blk_item.setTextAlignment(Qt.AlignCenter)

            self.tbl.setItem(row, 0, u_item)
            self.tbl.setItem(row, 1, v_item)
            self.tbl.setItem(row, 2, dist_item)
            self.tbl.setItem(row, 3, blk_item)

        self.tbl.resizeColumnToContents(0)
        self.tbl.resizeColumnToContents(1)
        self.tbl.resizeColumnToContents(2)

    def _rows(self):
        return [i.row() for i in self.tbl.selectionModel().selectedRows()]

    def _set_selected(self, new_blocked: bool):
        for row in self._rows():
            u = self.tbl.item(row, 0).text()
            v = self.tbl.item(row, 1).text()
            if self.G.has_edge(u, v):
                self.G[u][v]["blocked"] = bool(new_blocked)
            self.tbl.item(row, 3).setText("Sí" if new_blocked else "No")

    def on_toggle(self):
        for row in self._rows():
            u = self.tbl.item(row, 0).text()
            v = self.tbl.item(row, 1).text()
            if self.G.has_edge(u, v):
                cur = bool(self.G[u][v].get("blocked", False))
                self.G[u][v]["blocked"] = not cur
                self.tbl.item(row, 3).setText("Sí" if not cur else "No")
