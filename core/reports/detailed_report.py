"""
Generador de reportes detallados de la simulación del burro.
"""
from pathlib import Path
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from core.sim.simulator import RunLog


def generate_detailed_report(
    log: Any,
    universe,
    memberships: List,
    output_dir: str | Path = "reports"
) -> Dict:
    """
    Genera un reporte detallado de la simulación.

    Soporta tanto `RunLog` como el `RouteResult` retornado por las heurísticas.
    Si no hay información granular de pasos (caso RouteResult), se generan filas mínimas.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Construir un mapa de star_id -> constellation_id
    star_to_constellation = {}
    for m in memberships:
        star_to_constellation[m.starId] = m.constellationId

    # Normalizar entrada: RunLog (con pasos) o RouteResult (sin pasos)
    if hasattr(log, "to_rows"):
        # RunLog completo
        steps_rows = log.to_rows()
        visited_seq = list(getattr(log, "visited_order", [])) or list(getattr(log, "visited", []))
        initial_energy = getattr(log, "initial_energy", 0.0)
        initial_hay = getattr(log, "initial_grass", getattr(log, "initial_hay", 0.0))
        total_time = getattr(log, "total_time_invested", 0.0)
        final_grass = getattr(log, "final_grass", getattr(log, "hay_left", 0.0))
        died_flag = getattr(log, "died", False)
        final_energy = getattr(log, "final_energy", 0.0)
        final_life = getattr(log, "final_life", 0.0)
    else:
        # RouteResult mínimo
        rr = log
        steps_rows = []
        path = list(getattr(rr, "path", []))
        for idx, frm in enumerate(path):
            to = path[idx + 1] if idx + 1 < len(path) else ""
            steps_rows.append({
                "from_star": frm,
                "to_star": to,
                "distance": 0.0,
                "energy_before": 0.0,
                "energy_after": 0.0,
                "grass_before": 0.0,
                "grass_after": 0.0,
                "life_before": 0.0,
                "life_after": 0.0,
            })
        visited_seq = list(getattr(rr, "visited", [])) or path
        initial_energy = getattr(rr, "initial_energy", 0.0)
        initial_hay = getattr(rr, "initial_hay", 0.0)
        total_time = getattr(rr, "total_time_invested", 0.0) if hasattr(rr, "total_time_invested") else 0.0
        final_grass = getattr(rr, "hay_left", 0.0)
        died_flag = getattr(rr, "died", False)
        final_energy = getattr(rr, "remaining_energy", 0.0)
        final_life = getattr(rr, "remaining_life", 0.0)

    # Reporte de estrellas visitadas
    stars_report = []
    for i, star_id in enumerate(visited_seq, 1):
        constellation_id = star_to_constellation.get(star_id, "Desconocida")
        constellation_color = "Sin color"
        for const in getattr(universe, "constellations", []):
            if const.id == constellation_id:
                constellation_color = getattr(const, "color", "Sin color")
                break

        # Buscar información de consumo y tiempo en las filas de pasos
        grass_consumed = 0.0
        time_invested = 0.0
        
        # Buscar todas las filas donde esta estrella es origen (estancia)
        for step in steps_rows:
            if str(step.get("from_star")) == str(star_id):
                try:
                    grass_before = float(step.get("grass_before", 0.0))
                    grass_after = float(step.get("grass_after", 0.0))
                    grass_consumed = max(0.0, grass_before - grass_after)
                except Exception:
                    grass_consumed = 0.0
                break

        stars_report.append({
            "Orden": i,
            "ID Estrella": star_id,
            "Constelación": constellation_id,
            "Color": constellation_color,
            "Pasto Consumido (kg)": f"{grass_consumed:.2f}",
            "Tiempo Investigación (hrs)": f"{time_invested:.2f}",
        })

    # Crear DataFrame y exportar
    df_stars = pd.DataFrame(stars_report)
    df_stars.to_csv(Path(output_dir) / "estrellas_visitadas.csv", index=False)
    df_stars.to_json(Path(output_dir) / "estrellas_visitadas.json", orient="records", force_ascii=False)

    # Reporte de pasos
    df_steps = pd.DataFrame(steps_rows)
    df_steps.to_csv(Path(output_dir) / "pasos_completos.csv", index=False)
    df_steps.to_json(Path(output_dir) / "pasos_completos.json", orient="records", force_ascii=False)

    # Resumen ejecutivo
    try:
        total_distance = sum(float(s.get("distance", 0.0)) for s in steps_rows)
    except Exception:
        total_distance = 0.0
    try:
        total_grass_consumed = float(initial_hay) - float(final_grass)
    except Exception:
        total_grass_consumed = 0.0

    summary = {
        "Estrellas Visitadas": len(visited_seq),
        "Constelaciones Únicas": len(set(star_to_constellation.get(s, "Desconocida") for s in visited_seq)),
        "Distancia Total (a-luz)": f"{total_distance:.2f}",
        "Energía Inicial": f"{initial_energy:.2f}%",
        "Energía Final": f"{final_energy:.2f}%",
        "Pasto Consumido (kg)": f"{total_grass_consumed:.2f}",
        "Vida Inicial (a-luz)": f"{getattr(log, 'initial_life', 0.0):.2f}",
        "Vida Final (a-luz)": f"{final_life:.2f}",
        "Tiempo Total Investigación": f"{total_time:.2f}",
        "Motivo de Parada": getattr(log, 'stop_reason', getattr(log, 'reason', '')),
        "¿Burro Murió?": "Sí" if died_flag else "No",
    }

    # Exportar resumen
    summary_df = pd.DataFrame(list(summary.items()), columns=["Métrica", "Valor"])
    summary_df.to_csv(Path(output_dir) / "resumen_ejecutivo.csv", index=False)

    return {
        "summary": summary,
        "stars": stars_report,
        "steps": steps_rows,
    }


def format_report_for_display(report: Dict) -> str:
    """
    Formatea el reporte para mostrar en un QMessageBox o similar.
    """
    lines = ["=" * 70, "REPORTE DE VIAJE DEL BURRO ESPACIAL", "=" * 70, ""]
    
    summary = report.get("summary", {})
    for key, value in summary.items():
        lines.append(f"{key:.<40} {value}")
    
    lines.append("")
    lines.append("=" * 70)
    lines.append("ESTRELLAS VISITADAS:")
    lines.append("=" * 70)
    lines.append("")
    
    stars = report.get("stars", [])
    for star in stars:
        lines.append(f"  {star['Orden']:2}. {star['ID Estrella']:>4} - "
                    f"Constelación: {star['Constelación']:.<20} "
                    f"Pasto: {star['Pasto Consumido (kg)']:>6}")
    
    return "\n".join(lines)
