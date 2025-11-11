"""
Diálogo para mostrar el reporte detallado del viaje.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QTabWidget, QTableWidget, QTableWidgetItem, QLabel, QWidget
)
from PySide6.QtCore import Qt
from typing import Dict, List


class ReportDialog(QDialog):
    """Diálogo que muestra el reporte completo del viaje"""
    
    def __init__(self, report: Dict, parent=None):
        super().__init__(parent)
        self.report = report
        self.setWindowTitle("Reporte de Viaje - Equipo Científico NASA")
        self.setGeometry(100, 100, 1000, 700)
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        
        # Tabs
        tabs = QTabWidget()
        
        # Tab 1: Resumen Ejecutivo
        tab_summary = self.create_summary_tab()
        tabs.addTab(tab_summary, "Resumen Ejecutivo")
        
        # Tab 2: Estrellas Visitadas
        tab_stars = self.create_stars_tab()
        tabs.addTab(tab_stars, "Estrellas Visitadas")
        
        # Tab 3: Detalles de Pasos
        tab_steps = self.create_steps_tab()
        tabs.addTab(tab_steps, "Detalles de Pasos")
        
        layout.addWidget(tabs)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
    
    def create_summary_tab(self) -> QWidget:
        """Crea la pestaña de resumen ejecutivo"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        # Formato del resumen
        lines = ["<h2>REPORTE DE VIAJE - EQUIPO CIENTÍFICO NASA</h2>", ""]
        summary = self.report.get("summary", {})
        
        for key, value in summary.items():
            lines.append(f"<b>{key}:</b> {value}<br>")
        
        html_text = "<br>".join(lines)
        text_edit.setHtml(html_text)
        
        layout.addWidget(text_edit)
        return widget
    
    def create_stars_tab(self) -> QWidget:
        """Crea la pestaña de estrellas visitadas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tabla de estrellas
        table = QTableWidget()
        stars = self.report.get("stars", [])
        
        if stars:
            table.setRowCount(len(stars))
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels([
                "Orden", "Estrella", "Constelación", "Color", "Pasto (kg)", "Tiempo (hrs)"
            ])
            
            for row, star in enumerate(stars):
                table.setItem(row, 0, QTableWidgetItem(str(star["Orden"])))
                table.setItem(row, 1, QTableWidgetItem(star["ID Estrella"]))
                table.setItem(row, 2, QTableWidgetItem(star["Constelación"]))
                table.setItem(row, 3, QTableWidgetItem(star["Color"]))
                table.setItem(row, 4, QTableWidgetItem(str(star["Pasto Consumido (kg)"])))
                table.setItem(row, 5, QTableWidgetItem(str(star["Tiempo Investigación (hrs)"])))
            
            # Autoajustar columnas al contenido
            table.resizeColumnsToContents()
            # Permitir scroll si es necesario
            table.setColumnWidth(2, 120)  # Ampliar columna de constelación
        else:
            table.setColumnCount(1)
            table.setItem(0, 0, QTableWidgetItem("(Sin datos)"))
        
        layout.addWidget(table)
        return widget
    
    def create_steps_tab(self) -> QWidget:
        """Crea la pestaña de detalles de pasos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tabla de pasos
        table = QTableWidget()
        steps = self.report.get("steps", [])
        
        if steps:
            table.setRowCount(len(steps))
            table.setColumnCount(9)
            table.setHorizontalHeaderLabels([
                "De", "Hacia", "Distancia", "Energía (antes)", "Energía (después)",
                "Pasto (antes)", "Pasto (después)", "Vida (antes)", "Vida (después)"
            ])
            
            for row, step in enumerate(steps):
                table.setItem(row, 0, QTableWidgetItem(str(step.get("from_star", ""))))
                table.setItem(row, 1, QTableWidgetItem(str(step.get("to_star", ""))))
                table.setItem(row, 2, QTableWidgetItem(f"{float(step.get('distance', 0.0)):.2f}"))
                table.setItem(row, 3, QTableWidgetItem(f"{float(step.get('energy_before', 0.0)):.2f}"))
                table.setItem(row, 4, QTableWidgetItem(f"{float(step.get('energy_after', 0.0)):.2f}"))
                table.setItem(row, 5, QTableWidgetItem(f"{float(step.get('grass_before', 0.0)):.2f}"))
                table.setItem(row, 6, QTableWidgetItem(f"{float(step.get('grass_after', 0.0)):.2f}"))
                table.setItem(row, 7, QTableWidgetItem(f"{float(step.get('life_before', 0.0)):.2f}"))
                table.setItem(row, 8, QTableWidgetItem(f"{float(step.get('life_after', 0.0)):.2f}"))
            
            # Autoajustar columnas al contenido
            table.resizeColumnsToContents()
        else:
            table.setColumnCount(1)
            table.setItem(0, 0, QTableWidgetItem("(Sin datos)"))
        
        layout.addWidget(table)
        return widget
