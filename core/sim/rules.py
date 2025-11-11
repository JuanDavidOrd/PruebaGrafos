# sim/rules.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
from core.models.enums import Health

_UI2ENUM = {
    "Excelente": Health.EXCELLENT,
    "Buena":     Health.REGULAR,
    "Mala":      Health.BAD,
    "Moribundo": "moribundo",
    "Muerto":    "muerto",
}

# costo por a-luz según salud (puedes recalibrar si lo deseas)
_HEALTH_ENERGY_FACTOR = {
    Health.EXCELLENT: 1.0,
    Health.REGULAR:   1.2,
    Health.BAD:       1.5,
}

# ganancia de energía por kg según salud
_GAIN_PER_KG = {
    Health.EXCELLENT: 5.0,
    Health.REGULAR:   3.0,
    Health.BAD:       2.0,
}

@dataclass
class RouteResult:
    path: List[str]
    edges: List[Tuple[str, str]]
    visited: List[str]
    remaining_energy: float
    remaining_life: float
    reason: str
    hay_left: float = 0.0    # 👈 añadido para Paso 3

def _norm_id(x: Any) -> str:
    return str(x)

def _parse_health(txt: str):
    return _UI2ENUM.get(txt, Health.EXCELLENT)

def compute_route_step2(G, origin_id: str, health_txt: str,
                        energy_pct: float, hay_kg: float, life_ly: float) -> RouteResult:
    # ... (tu implementación actual del paso 2, sin cambios) ...
    ...

def _get_star(u, sid: str):
    # ‘u.stars’ puede ser lista de modelos o dicts
    for s in getattr(u, "stars", []):
        _id = str(getattr(s, "id", s.get("id") if isinstance(s, dict) else None))
        if _id == sid:
            return s
    return None

def _get_research(star) -> Dict[str, float]:
    """Lee research compatible con modelo o dict."""
    if star is None:
        return {}
    r = getattr(star, "research", None)
    if r is None and isinstance(star, dict):
        r = star.get("research")
    if r is None:
        return {}
    # soporta pydantic model o dict
    def g(o, k, d=0.0): 
        return getattr(o, k, d) if not isinstance(o, dict) else o.get(k, d)
    return {
        "x_time_per_kg":      float(g(r, "x_time_per_kg", 1.0) or 1.0),
        "invest_energy_per_x":float(g(r, "invest_energy_per_x", 0.0) or 0.0),
        "disease_life_delta": float(g(r, "disease_life_delta", 0.0) or 0.0),
    }

def compute_route_step3(G, u, origin_id: str, health_txt: str,
                        energy_pct: float, hay_kg: float, life_ly: float) -> RouteResult:
    """
    Heurística voraz + estadía por estrella:
    - Si energía < 50%, come kg hasta el límite de tiempo (máx 50% de la estadía).
    - Ganancia por kg depende de la salud.
    - El 50% restante se usa para “investigar”: energía -= invest_energy_per_x * 0.5.
    - Vida += disease_life_delta (puede ser ±).
    - Movimiento: vecino más cercano no visitado con coste de energía/vida.
    """
    origin = _norm_id(origin_id)
    health = _parse_health(health_txt)

    if health in ("muerto",):
        return RouteResult([origin], [], [origin], energy_pct, life_ly, "Burro muerto", hay_left=hay_kg)

    factor = 2.0 if health == "moribundo" else _HEALTH_ENERGY_FACTOR.get(health, 1.3)
    gain_per_kg = _GAIN_PER_KG.get(health if health in _GAIN_PER_KG else Health.BAD, 2.0)

    energy = float(energy_pct)
    life   = float(life_ly)
    hay    = float(hay_kg)

    if origin not in G.G.nodes:
        return RouteResult([], [], [], energy, life, "Origen inexistente en el grafo", hay_left=hay)

    visited = set([origin])
    path: List[str] = [origin]
    edges_path: List[Tuple[str, str]] = []
    current = origin

    while True:
        # —— Estancia en estrella actual ——
        star = _get_star(u, current)
        r = _get_research(star)
        x_time = max(1e-9, r.get("x_time_per_kg", 1.0))
        invest_e_per_x = r.get("invest_energy_per_x", 0.0)
        life_delta = r.get("disease_life_delta", 0.0)

        # comer si <50%
        if energy < 50.0 and hay > 0:
            max_kg_time = 0.5 / x_time         # 50% del tiempo solo comer
            kg_to_eat = min(hay, max_kg_time)
            if kg_to_eat > 0:
                energy = min(100.0, energy + kg_to_eat * gain_per_kg)
                hay -= kg_to_eat

        # investigación en el 50% restante
        energy -= invest_e_per_x * 0.5
        life   += life_delta

        if energy <= 0 or life <= 0:
            reason = "Sin energía/vida tras estadía"
            break

        # —— Movimiento voraz ——
        candidates: List[Tuple[float, str, float, float]] = []
        for v in G.G.neighbors(current):
            v_id = _norm_id(v)
            if v_id in visited:
                continue
            e = G.G[current][v]
            if e.get("blocked", False):
                continue
            d = float(e.get("distance", 0.0))
            life_cost   = d
            energy_cost = d * factor
            if life - life_cost <= 0 or energy - energy_cost <= 0:
                continue
            candidates.append((d, v_id, energy_cost, life_cost))

        if not candidates:
            reason = "Sin vecinos viables (vida/energía insuficientes o todo visitado)"
            break

        candidates.sort(key=lambda t: t[0])
        d, nxt, e_cost, l_cost = candidates[0]
        life   -= l_cost
        energy -= e_cost

        edges_path.append((current, nxt))
        path.append(nxt)
        visited.add(nxt)
        current = nxt

    return RouteResult(
        path=path,
        edges=edges_path,
        visited=list(visited),
        remaining_energy=max(0.0, energy),
        remaining_life=max(0.0, life),
        reason=reason,
        hay_left=hay
    )
