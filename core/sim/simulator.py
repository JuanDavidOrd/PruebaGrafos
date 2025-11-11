# core/sim/simulator.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

from core.sim.rules import (
    compute_route_step3,         # por si quieres usar el cálculo "completo" directo
    _get_star,
    _get_research,
    _UI2ENUM,
    _HEALTH_ENERGY_FACTOR,
    _GAIN_PER_KG,
    _norm_id,
    _parse_health,
)

# ---------------------------------------------------------------------
# MODELOS DE SIMULACIÓN
# ---------------------------------------------------------------------

@dataclass
class Step:
    """Un paso: estancia en 'from_star' + salto a 'to_star' (si existe)."""
    from_star: str
    to_star: Optional[str]           # None si no hubo movimiento
    distance: float                  # 0.0 si no hubo movimiento
    energy_before: float
    energy_after: float
    grass_before: float
    grass_after: float
    life_before: float
    life_after: float

@dataclass
class RunLog:
    """Bitácora de la simulación completa."""
    steps: List[Step] = field(default_factory=list)
    visited_order: List[str] = field(default_factory=list)   # orden de visita (IDs)
    stop_reason: str = ""                                    # por qué se detuvo
    final_energy: float = 0.0
    final_grass: float = 0.0
    final_life: float = 0.0

    def to_rows(self) -> List[Dict]:
        """Convierte los pasos a filas (útil para CSV/tabla)."""
        rows: List[Dict] = []
        for s in self.steps:
            rows.append({
                "from_star": s.from_star,
                "to_star": s.to_star if s.to_star is not None else "",
                "distance": s.distance,
                "energy_before": s.energy_before,
                "energy_after": s.energy_after,
                "grass_before": s.grass_before,
                "grass_after": s.grass_after,
                "life_before": s.life_before,
                "life_after": s.life_after,
            })
        return rows

    def edges(self) -> List[Tuple[str, str]]:
        """Devuelve las aristas realmente recorridas, para pintar overlay."""
        out: List[Tuple[str, str]] = []
        for s in self.steps:
            if s.to_star:
                out.append((s.from_star, s.to_star))
        return out

# ---------------------------------------------------------------------
# SIMULACIÓN PASO A PASO (Paso 3)
# ---------------------------------------------------------------------

def simulate_step3(
    u,
    G,
    origin_id: str,
    health_txt: str,
    energy_pct: float,
    hay_kg: float,
    life_ly: float,
) -> Tuple[Optional[Step], Dict]:
    """
    Ejecuta **UN** paso del Paso 3 (estancia + posible movimiento).
    Devuelve:
      - Step (o None si muere durante la estancia)
      - nuevo estado: {"energy", "hay", "life", "next", "reason"}

    Lógica:
      1) Estancia en estrella actual:
         - Si energía < 50, come hasta 50% del tiempo (kg = 0.5 / x_time_per_kg)
         - En el 50% restante: energía -= invest_energy_per_x * 0.5
         - Vida += disease_life_delta
      2) Si sigue vivo, escoge **vecino más cercano** cuyo coste quepa
         en energía/vida y no esté bloqueado. Aplica movimiento.
    """
    current = _norm_id(origin_id)
    health = _parse_health(health_txt)
    energy = float(energy_pct)
    hay = float(hay_kg)
    life = float(life_ly)

    # --- datos de la estrella actual
    star = _get_star(u, current)
    r = _get_research(star)
    x_time = max(1e-9, r.get("x_time_per_kg", 1.0))
    invest_e = r.get("invest_energy_per_x", 0.0)
    life_delta = r.get("disease_life_delta", 0.0)

    # estados antes de la estancia
    energy_before = energy
    grass_before = hay
    life_before = life

    # --- estancia: comer si energía < 50
    if energy < 50.0 and hay > 0.0:
        max_kg_time = 0.5 / x_time        # 50% del tiempo comiendo
        kg_to_eat = min(hay, max_kg_time)
        if kg_to_eat > 0.0:
            gain_per_kg = _GAIN_PER_KG.get(health, 2.0)
            energy = min(100.0, energy + kg_to_eat * gain_per_kg)
            hay -= kg_to_eat

    # investigación con 50% restante del tiempo
    energy -= invest_e * 0.5
    life += life_delta

    # muerto tras estancia
    if energy <= 0.0 or life <= 0.0:
        return None, {
            "energy": max(0.0, energy),
            "hay": max(0.0, hay),
            "life": max(0.0, life),
            "next": None,
            "reason": "Muere durante la estancia",
        }

    # --- elección de vecino: más cercano quepa en presupuesto
    factor = _HEALTH_ENERGY_FACTOR.get(health, 1.3)
    candidates: List[Tuple[float, str, float, float]] = []  # (d, v_id, e_cost, l_cost)

    for v in G.G.neighbors(current):
        v_id = _norm_id(v)
        e = G.G[current][v]
        if e.get("blocked", False):
            continue
        d = float(e.get("distance", 0.0))
        life_cost = d
        energy_cost = d * factor
        if life - life_cost <= 0.0 or energy - energy_cost <= 0.0:
            continue
        candidates.append((d, v_id, energy_cost, life_cost))

    if not candidates:
        # No se puede mover: generamos un Step de "estancia sin salto"
        step = Step(
            from_star=current,
            to_star=None,
            distance=0.0,
            energy_before=energy_before,
            energy_after=energy,
            grass_before=grass_before,
            grass_after=hay,
            life_before=life_before,
            life_after=life,
        )
        return step, {
            "energy": energy,
            "hay": hay,
            "life": life,
            "next": None,
            "reason": "Sin vecinos viables",
        }

    candidates.sort(key=lambda t: t[0])  # más cercano primero
    d, nxt, e_cost, l_cost = candidates[0]

    energy_after = energy - e_cost
    life_after = life - l_cost
    hay_after = hay

    step = Step(
        from_star=current,
        to_star=nxt,
        distance=d,
        energy_before=energy_before,
        energy_after=energy_after,
        grass_before=grass_before,
        grass_after=hay_after,
        life_before=life_before,
        life_after=life_after,
    )

    return step, {
        "energy": energy_after,
        "hay": hay_after,
        "life": life_after,
        "next": nxt,
        "reason": "OK",
    }

# ---------------------------------------------------------------------
# EJECUTAR SIMULACIÓN COMPLETA (Paso 3)
# ---------------------------------------------------------------------

def run_full_step3(
    u,
    G,
    origin_id: str,
    health_txt: str,
    energy_pct: float,
    hay_kg: float,
    life_ly: float,
    max_steps: int = 1000,
) -> RunLog:
    """
    Corre la simulación del **Paso 3** hasta detenerse (sin vecinos viables o muerte).
    Devuelve un RunLog con:
      - steps (Step[])
      - visited_order
      - stop_reason
      - final_energy / final_grass / final_life
    """
    current = _norm_id(origin_id)
    energy = float(energy_pct)
    hay = float(hay_kg)
    life = float(life_ly)

    log = RunLog()
    log.visited_order.append(current)

    for _ in range(max_steps):
        step, state = simulate_step3(u, G, current, health_txt, energy, hay, life)

        if step is None:
            # murió durante la estancia
            log.stop_reason = state["reason"]
            log.final_energy = state["energy"]
            log.final_grass = state["hay"]
            log.final_life = state["life"]
            break

        # registrar el paso
        log.steps.append(step)
        energy = state["energy"]
        hay = state["hay"]
        life = state["life"]
        nxt = state["next"]

        if nxt is None:
            # no hay movimiento posible
            log.stop_reason = state["reason"]
            log.final_energy = energy
            log.final_grass = hay
            log.final_life = life
            break

        current = nxt
        log.visited_order.append(current)

    else:
        # agotó max_steps
        log.stop_reason = "Límite de pasos alcanzado"
        log.final_energy = energy
        log.final_grass = hay
        log.final_life = life

    return log
