from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Step:
    from_star: str
    to_star: str
    distance: float
    energy_before: float
    energy_after: float
    grass_before: float
    grass_after: float
    life_before: float
    life_after: float


@dataclass
class RunLog:
    steps: List[Step] = field(default_factory=list)
    visited_order: List[str] = field(default_factory=list)


    def to_rows(self) -> List[Dict]:
        out = []
        for s in self.steps:
            out.append(s.__dict__)
        return out
    
    # sim/simulator.py
from sim.rules import compute_route_step2, compute_route_step3

def run_step3(u, G, origin, health, energy, hay, life):
    res = compute_route_step3(G, u, origin, health, energy, hay, life)
    msg = (
        f"Visitas: {len(res.visited)}\n"
        f"Recorrido: {' → '.join(res.path)}\n"
        f"Energía restante: {res.remaining_energy:.2f}%\n"
        f"Vida restante: {res.remaining_life:.2f} a-luz\n"
        f"Pasto restante: {res.hay_left:.2f} kg\n"
        f"Motivo de parada: {res.reason}"
    )
    return res.edges, msg
