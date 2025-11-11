from PySide6.QtWidgets import (
    QWidget, QGroupBox, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QVBoxLayout, QFormLayout, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt

_HEALTHS = ["Excelente", "Buena", "Mala", "Moribundo", "Muerto"]

class ParamsPanel(QWidget):
    """
    Panel con parámetros iniciales y botones de acciones previas al viaje.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Controles
        self.cb_origin = QComboBox()
        self.cb_health = QComboBox()
        self.cb_health.addItems(_HEALTHS)

        self.sp_energy = QSpinBox()
        self.sp_energy.setRange(1, 100)
        self.sp_energy.setSuffix(" %")

        self.sp_hay = QDoubleSpinBox()
        self.sp_hay.setDecimals(2)
        self.sp_hay.setRange(0, 10_000)
        self.sp_hay.setSuffix(" kg")

        self.sp_age = QDoubleSpinBox()
        self.sp_age.setDecimals(2)
        self.sp_age.setRange(0, 10_000)
        self.sp_age.setSuffix(" años")

        self.sp_life = QDoubleSpinBox()
        self.sp_life.setDecimals(2)
        self.sp_life.setRange(0, 1_000_000)
        self.sp_life.setSuffix(" a-luz")

        # Botones
        self.btn_edit_stars = QPushButton("Editar estrellas…")

        # Layout
        box = QGroupBox("Parámetros iniciales")
        form = QFormLayout(box)
        form.addRow("Origen:", self.cb_origin)
        form.addRow("Salud:", self.cb_health)
        form.addRow("Burroenergía:", self.sp_energy)
        form.addRow("Pasto en bodega:", self.sp_hay)
        form.addRow("Edad:", self.sp_age)
        form.addRow("Tiempo de vida:", self.sp_life)

        root = QVBoxLayout(self)
        root.addWidget(box)
        root.addWidget(self.btn_edit_stars, alignment=Qt.AlignTop)

        self.setDisabled(True)  # solo se habilita cuando hay universo cargado

    # --- API pública ---

    def set_from_universe(self, u):
        """
        Rellena el panel usando el universo cargado.
        - Llena estrellas de origen (solo las que tienen coords válidas).
        - Toma valores iniciales desde el JSON si existen.
        """
        self.cb_origin.clear()
        # u.stars puede ser lista de modelos o dicts
        def get(obj, name, default=None):
            return getattr(obj, name, default) if not isinstance(obj, dict) else obj.get(name, default)

        stars = [(str(get(s, "id")), get(s, "name", get(s, "id"))) for s in u.stars]
        # filtra las que tengan coordenadas válidas
        def has_xy(s):
            x = get(s, "x"); y = get(s, "y")
            return x is not None and y is not None
        stars_xy = [s for s in u.stars if has_xy(s)]
        ids_xy = [str(get(s, "id")) for s in stars_xy]

        for sid, name in stars:
            if sid in ids_xy:
                self.cb_origin.addItem(f"{sid} – {name}", sid)

        # valores globales (por si existen en el JSON cargado)
        energy0 = getattr(u, "burroenergiaInicial", None) or getattr(u, "burroEnergy", None)
        if energy0 is None:
            energy0 = 100
        self.sp_energy.setValue(int(energy0))

        health0 = getattr(u, "estadoSalud", None) or getattr(u, "health", None)
        if isinstance(health0, str) and health0 in _HEALTHS:
            self.cb_health.setCurrentText(health0)
        else:
            self.cb_health.setCurrentText("Excelente")

        hay0 = getattr(u, "pasto", None) or getattr(u, "hayKg", None) or 0
        self.sp_hay.setValue(float(hay0))

        start_age = getattr(u, "startAge", None)
        death_age = getattr(u, "deathAge", None)
        self.sp_age.setValue(float(start_age or 0))
        # si hay start/death, pre-calcula vida como diferencia
        life0 = None
        if start_age is not None and death_age is not None:
            try:
                life0 = float(death_age) - float(start_age)
            except Exception:
                life0 = None
        self.sp_life.setValue(float(life0 or 0))

        self.setDisabled(False)

    def read_params(self):
        """
        Devuelve un dict con los parámetros actuales.
        """
        return {
            "origin": self.cb_origin.currentData(),
            "health": self.cb_health.currentText(),
            "energy": self.sp_energy.value(),
            "hay_kg": self.sp_hay.value(),
            "age": self.sp_age.value(),
            "life_ly": self.sp_life.value(),
        }
