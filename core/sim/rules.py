from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
from core.models.enums import Health

# Texto UI -> enum (y marcadores especiales)
_UI2ENUM = {
    "Excelente": Health.EXCELLENT,
    "Buena":     Health.REGULAR,
    "Mala":      Health.BAD,
    "Moribundo": "moribundo",
    "Muerto":    "muerto",
}

# Costo de energía por a-luz según salud
_HEALTH_ENERGY_FACTOR = {
    Health.EXCELLENT: 1.0,
    Health.REGULAR:   1.2,
    Health.BAD:       1.5,
}

# Ganancia de energía por kg según salud
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
    hay_left: float = 0.0
    died: bool = False                          # Si el burro murió
    initial_energy: float = 0.0                 # Energía inicial
    initial_hay: float = 0.0                    # Pasto inicial
    initial_life: float = 0.0                   # Vida inicial
    visited_stars_info: List[Dict] = None       # Info detallada de estrellas visitadas

def _norm_id(x: Any) -> str:
    return str(x)

def _parse_health(txt: str):
    return _UI2ENUM.get(txt, Health.EXCELLENT)

# ----- Punto 2 -----
def compute_route_step2(G, origin_id: str, health_txt: str,
                        energy_pct: float, hay_kg: float, life_ly: float) -> RouteResult:
    """
    Ruta simple (sin comer ni investigar):
    - consumo = distancia * factor
    - vida = distancia
    - movimiento voraz al vecino NO visitado más cercano
    """
    origin = _norm_id(origin_id)
    health = _parse_health(health_txt)

    # Si está muerto, devolver ruta trivial
    if health in ("muerto",):
        return RouteResult([origin], [], [origin], float(energy_pct), float(life_ly),
                        "Burro muerto", hay_left=float(hay_kg))

    # Selección del factor según salud
    factor = 2.0 if health == "moribundo" else _HEALTH_ENERGY_FACTOR.get(health, 1.3)

    energy = float(energy_pct)
    life   = float(life_ly)

    if origin not in G.G.nodes:
        return RouteResult([], [], [], energy, life,
                        "Origen inexistente en el grafo", hay_left=float(hay_kg),
                        initial_energy=energy, initial_hay=float(hay_kg), initial_life=life)

    visited = {origin}
    path = [origin]
    edges = []
    current = origin

    while True:
        candidates = []
        for v in G.G.neighbors(current):
            v_id = _norm_id(v)
            if v_id in visited:
                continue
            e = G.G[current][v]
            if e.get("blocked", False):
                continue

            d = float(e.get("distance", 0.0))
            if d <= 0:
                continue

            life_cost = d
            energy_cost = d * factor

            if life - life_cost <= 0 or energy - energy_cost <= 0:
                continue

            candidates.append((d, v_id, energy_cost, life_cost))

        if not candidates:
            reason = "Sin vecinos viables (vida/energía insuficientes o todo visitado)"
            break

        # Tomar el vecino más cercano
        candidates.sort(key=lambda t: t[0])
        d, nxt, e_cost, l_cost = candidates[0]

        life -= l_cost
        energy -= e_cost

        edges.append((current, nxt))
        path.append(nxt)
        visited.add(nxt)
        current = nxt

    return RouteResult(
        path=path,
        edges=edges,
        visited=list(visited),
        remaining_energy=max(0.0, min(100.0, energy)),
        remaining_life=max(0.0, life),
        reason=reason,
       hay_left=float(hay_kg),
       initial_energy=float(energy_pct),
       initial_hay=float(hay_kg),
       initial_life=float(life_ly),
    )

# Helpers robustos para leer estrellas e investigación
def _get_star(u, sid: str):
    """Busca la estrella por id en u.stars (lista de modelos o dicts)."""
    for s in getattr(u, "stars", []):
        if isinstance(s, dict):
            _id = s.get("id")
        else:
            _id = getattr(s, "id", None)
        if str(_id) == str(sid):
            return s
    return None

def _get_research(star) -> Dict[str, float]:
    """Lee research compatible con modelo o dict; devuelve dict simple con defaults."""
    if star is None:
        return {}
    r = None
    if isinstance(star, dict):
        r = star.get("research")
    else:
        r = getattr(star, "research", None)
    if r is None:
        return {}
    def g(o, k, d=0.0):
        return (o.get(k, d) if isinstance(o, dict) else getattr(o, k, d))
    # x_time_per_kg = "X tiempo por kg"
    # invest_energy_per_x = "energía por X tiempo"
    return {
        "x_time_per_kg":       float(g(r, "x_time_per_kg", 1.0) or 1.0),
        "invest_energy_per_x": float(g(r, "invest_energy_per_x", 0.0) or 0.0),
        "disease_life_delta":  float(g(r, "disease_life_delta", 0.0) or 0.0),
    }

def compute_route_step3(G, u, origin_id: str, health_txt: str,
                        energy_pct: float, hay_kg: float, life_ly: float) -> RouteResult:
    """
    Heurística voraz con estancia por estrella:
    - 50% del tiempo: comer si energía < 50% (kg = min(hay, 0.5 / X))
    * ganancia_energía = kg * gain_per_kg (cap a 100%)
    - 50% restante: investigación (gasto) => energía -= (0.5 / X) * invest_energy_per_x
    - efecto salud/vida de la estrella: vida += disease_life_delta (puede ser ±)
    - movimiento: vecino no visitado más cercano que quepa en vida/energía
    """
    origin = _norm_id(origin_id)
    health = _parse_health(health_txt)

    if health in ("muerto",):
        return RouteResult([origin], [], [origin], float(energy_pct), float(life_ly),
                            "Burro muerto", hay_left=float(hay_kg), died=True,
                            initial_energy=float(energy_pct), initial_hay=float(hay_kg), 
                            initial_life=float(life_ly))

    factor = 2.0 if health == "moribundo" else _HEALTH_ENERGY_FACTOR.get(health, 1.3)
    gain_per_kg = _GAIN_PER_KG.get(health if isinstance(health, Health) else Health.BAD, 2.0)

    energy = float(energy_pct)
    life   = float(life_ly)
    hay    = float(hay_kg)
    
    # Guardar valores iniciales
    initial_energy = energy
    initial_hay = hay
    initial_life = life

    if origin not in G.G.nodes:
        return RouteResult([], [], [], energy, life, "Origen inexistente en el grafo", hay_left=hay,
                          initial_energy=initial_energy, initial_hay=initial_hay, initial_life=initial_life)

    visited = {origin}
    path: List[str] = [origin]
    edges_path: List[Tuple[str, str]] = []
    current = origin
    died = False
    reason = "OK"

    while True:
        # ----- Estancia en estrella actual -----
        r = _get_research(_get_star(u, current))
        x_time = max(1e-6, r.get("x_time_per_kg", 1.0))         # evita división por cero
        invest_e_per_x = max(0.0, r.get("invest_energy_per_x", 0.0))
        life_delta     = float(r.get("disease_life_delta", 0.0))

        # Comer (solo si energía < 50%)
        if energy < 50.0 and hay > 0.0:
            max_kg_by_time = 0.5 / x_time     # 50% del tiempo disponible para comer
            kg_to_eat = max(0.0, min(hay, max_kg_by_time))
            if kg_to_eat > 0.0:
                gained = kg_to_eat * gain_per_kg
                energy = min(100.0, energy + gained)
                hay -= kg_to_eat

        # Investigación en el 50% restante del tiempo:
        # gasto correcto: (0.5 / X) * (energía por X)
        energy -= (0.5 / x_time) * invest_e_per_x

        # Efecto vida de la estrella
        life += life_delta

        # corte si muere o queda sin energía tras la estancia
        if energy <= 0.0 or life <= 0.0:
            reason = "Burro murió durante la estancia"
            died = True
            break

        # ----- Movimiento voraz -----
        candidates: List[Tuple[float, str, float, float]] = []  # (dist, v, e_cost, l_cost)
        for v in G.G.neighbors(current):
            v_id = _norm_id(v)
            if v_id in visited:
                continue
            e = G.G[current][v]
            if e.get("blocked", False):
                continue
            d = float(e.get("distance", 0.0))
            if d <= 0.0:
                continue
            life_cost   = d
            energy_cost = d * factor
            if life - life_cost <= 0.0 or energy - energy_cost <= 0.0:
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
        remaining_energy=max(0.0, min(100.0, energy)),
        remaining_life=max(0.0, life),
        reason=reason,
        hay_left=max(0.0, hay),
        died=died,
        initial_energy=initial_energy,
        initial_hay=initial_hay,
        initial_life=initial_life,
    )
