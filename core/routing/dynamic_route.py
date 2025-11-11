from dataclasses import dataclass
from typing import List, Tuple
import heapq
from core.graph.space_graph import SpaceGraph
from core.models.donkey import Donkey
from core.models.enums import StarType
from core.sim.rules import eat_energy_gain


@dataclass
class State:
    node: str
    life: float
    energy: float
    grass: float
    visited: frozenset[str]
    score: float
    path: Tuple[str, ...]


BEAM = 10
ALPHA, BETA, GAMMA = 0.1, 0.01, 0.01


def simulate_visit(G: SpaceGraph, node: str, energy: float, grass: float, life: float, health) -> tuple[float, float, float]:
    """Aplica reglas de comer/investigar y retorna (energy, grass, life) actualizados."""
    n = G.G.nodes[node]
    r = n["research"]
    # comer si <50%
    eat_time_budget = 0.0
    if energy < 50.0:
        eat_time_budget = 0.5 # 50% del tiempo de estadía relativo (escala abstracta)
        # kg posibles por tiempo disponible
        # usamos x_time_per_kg como costo temporal absoluto y su presupuesto relativo 0.5
        # aquí, por simplicidad, 1 unidad total de estadía => kg_max = 0.5 / x_time_per_kg
        kg_max = max(0.0, 0.5 / max(r.x_time_per_kg, 1e-9))
        kg = min(kg_max, grass)
        energy += eat_energy_gain(health, kg)
        grass -= kg
    # investigación consume sobre el tiempo restante 0.5
    invest_time = 0.5
    energy -= r.invest_energy_per_x * invest_time
    # enfermedades/beneficios
    life += r.disease_life_delta
    return energy, grass, life


def route_dynamic_beam(G: SpaceGraph, start: str, donkey: Donkey) -> List[str]:
    start_state = State(
        node=start,
        life=donkey.life_ly,
        energy=donkey.energy_pct,
        grass=donkey.grass_kg,
        visited=frozenset([start]),
        score=0.0,
        path=(start,)
    )
    beam: list[State] = [start_state]

    best = start_state


    while beam:
        cand: list[State] = []
        for s in beam:
        # expandir vecinos
            for v, dist in G.neighbors(s.node):
                if v in s.visited:
                    continue
                life = s.life - dist
                if life <= 0:
                    continue
                energy = s.energy
                grass = s.grass
                # aplicar efecto hiper-gigante si corresponde
                if G.G.nodes[v]["type"] == StarType.HYPERGIANT:
                    energy *= 1.5
                    grass *= 2.0
                # simular visita
                energy, grass, life = simulate_visit(G, v, energy, grass, life, donkey.health)
                if energy <= 0 or life <= 0:
                    continue
                path = s.path + (v,)
                visited = s.visited | {v}
                stars = len(visited)
                cost = (donkey.life_ly - life)
                score = stars - ALPHA*cost + BETA*life + GAMMA*energy
                ns = State(v, life, energy, grass, frozenset(visited), score, path)
                cand.append(ns)
                if stars > len(best.visited) or (stars == len(best.visited) and ns.score > best.score):
                    best = ns
        if not cand:
            break
        # seleccionar top BEAM por score
        beam = heapq.nlargest(BEAM, cand, key=lambda x: x.score)
    return list(best.path)