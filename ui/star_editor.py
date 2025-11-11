from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from types import SimpleNamespace

COLS = ["id", "nombre", "X tiempo/kg", "Y gasto/X", "Δvida (a-luz)"]

def _get(obj, name, default=None):
    return obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)

def _ensure_research(obj):
    """
    Devuelve (research_obj, r_get, r_set) donde:
    - research_obj: el dict o modelo research asociado a obj (creado si no existía)
    """
    if isinstance(obj, dict):
        r = obj.setdefault("research", {}) or {}
        def r_get(k, d=None): return r.get(k, d)
        def r_set(k, v): r.__setitem__(k, v)
        return r, r_get, r_set

    # Modelo/objeto
    r = getattr(obj, "research", None)
    if r is None:
        r = SimpleNamespace(x_time_per_kg=1.0, invest_energy_per_x=0.0, disease_life_delta=0.0)
        setattr(obj, "research", r)

    def r_get(k, d=None): return getattr(r, k, d)
    def r_set(k, v): setattr(r, k, v)
    return r, r_get, r_set

def _to_float(text, default=0.0):
    if text is None:
        return default
    t = str(text).strip().replace(",", ".")
    try:
        return float(t)
    except Exception:
        return default

class StarEditor(QDialog):
    def __init__(self, universe, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar estrellas")
        self.u = universe

        self.tbl = QTableWidget(0, len(COLS))
        self.tbl.setHorizontalHeaderLabels(COLS)
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self.tbl.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        self.tbl.verticalHeader().setVisible(False)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_ok = QPushButton("Guardar cambios")

        btns = QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)

        root = QVBoxLayout(self)
        root.addWidget(self.tbl)
        root.addLayout(btns)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self._apply_and_accept)

        self._load()

    def _load(self):
        stars = self.u.stars
        self.tbl.setRowCount(len(stars))

        for row, s in enumerate(stars):
            sid  = str(_get(s, "id"))
            name = _get(s, "name", sid)

            _, r_get, _ = _ensure_research(s)
            x     = r_get("x_time_per_kg", 1.0) or 1.0
            y     = r_get("invest_energy_per_x", 0.0) or 0.0
            dlife = r_get("disease_life_delta", 0.0) or 0.0

            data = [sid, name, f"{float(x):.2f}", f"{float(y):.2f}", f"{float(dlife):.2f}"]
            for col, val in enumerate(data):
                item = QTableWidgetItem(str(val))
                if col in (0, 1):
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                else:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tbl.setItem(row, col, item)

        self.tbl.resizeColumnsToContents()

    def _apply_and_accept(self):
        stars = self.u.stars

        for row, s in enumerate(stars):
            _, _, r_set = _ensure_research(s)

            # lee con tolerancia a None
            x_txt  = self.tbl.item(row, 2).text() if self.tbl.item(row, 2) else "1"
            y_txt  = self.tbl.item(row, 3).text() if self.tbl.item(row, 3) else "0"
            dv_txt = self.tbl.item(row, 4).text() if self.tbl.item(row, 4) else "0"

            x  = _to_float(x_txt, 1.0)
            y  = _to_float(y_txt, 0.0)
            dv = _to_float(dv_txt, 0.0)

            # validaciones y límites
            if x <= 0:
                x = 0.01  # evita divisiones por cero
            if y < 0:
                y = 0.0   # gasto negativo no tiene sentido

            r_set("x_time_per_kg", x)
            r_set("invest_energy_per_x", y)
            r_set("disease_life_delta", dv)

            # vuelve a formatear en la tabla (opcional)
            self.tbl.item(row, 2).setText(f"{x:.2f}")
            self.tbl.item(row, 3).setText(f"{y:.2f}")
            self.tbl.item(row, 4).setText(f"{dv:.2f}")

        QMessageBox.information(self, "OK", "Cambios aplicados al universo en memoria.")
        self.accept()
