# ui/star_editor.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt

def _get(obj, name, default=None):
    return obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)

def _ensure_research(obj):
    """
    Devuelve el objeto 'research' (dict o modelo) y dos helpers:
    r_get(key, default), r_set(key, value)
    """
    if isinstance(obj, dict):
        r = obj.setdefault("research", {}) or {}
        def r_get(k, d=None): return r.get(k, d)
        def r_set(k, v): r.__setitem__(k, v)
        return r, r_get, r_set

    # Modelo pydantic
    r = getattr(obj, "research", None)
    if r is None:
        # crea un contenedor simple si viniera sin research
        class _R: pass
        r = _R()
        setattr(obj, "research", r)

    def r_get(k, d=None): return getattr(r, k, d)
    def r_set(k, v): setattr(r, k, v)
    return r, r_get, r_set


class StarEditor(QDialog):
    COLS = ["id", "nombre", "X tiempo/kg", "Y gasto/X", "Δvida (a-luz)"]

    def __init__(self, universe, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar estrellas")
        self.u = universe

        self.tbl = QTableWidget(0, len(self.COLS))
        self.tbl.setHorizontalHeaderLabels(self.COLS)
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self.tbl.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked
        )

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_ok = QPushButton("Guardar cambios")

        btns = QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)

        lay = QVBoxLayout(self)
        lay.addWidget(self.tbl)
        lay.addLayout(btns)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self._apply_and_accept)

        self._load()

    def _load(self):
        stars = self.u.stars
        self.tbl.setRowCount(len(stars))
        for row, s in enumerate(stars):
            sid = str(_get(s, "id"))
            name = _get(s, "name", sid)

            _, r_get, _ = _ensure_research(s)
            x = r_get("x_time_per_kg", 1.0) or 1.0
            y = r_get("invest_energy_per_x", 0.0) or 0.0
            dlife = r_get("disease_life_delta", 0.0) or 0.0

            for col, val in enumerate([sid, name, x, y, dlife]):
                item = QTableWidgetItem(str(val))
                if col in (0, 1):
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                else:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tbl.setItem(row, col, item)

    def _apply_and_accept(self):
        stars = self.u.stars
        for row, s in enumerate(stars):
            _, _, r_set = _ensure_research(s)

            def to_f(col):
                try:
                    return float(self.tbl.item(row, col).text())
                except Exception:
                    return 0.0

            r_set("x_time_per_kg", to_f(2) or 1.0)
            r_set("invest_energy_per_x", to_f(3) or 0.0)
            r_set("disease_life_delta", to_f(4) or 0.0)

        QMessageBox.information(self, "OK", "Cambios aplicados al universo en memoria.")
        self.accept()
