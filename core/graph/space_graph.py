import math
import networkx as nx
from core.io.schema import UniverseIn


RED_MULTI = "#d62728"


class SpaceGraph:
    def __init__(self, universe):
        import networkx as nx
        self.G = nx.Graph()

        # 1) Nodos (todos con coords)
        for s in universe.stars:
            self.G.add_node(s.id, x=s.x, y=s.y, type=s.type, galaxyId=s.galaxyId)

        # 2) Aristas (solo si ambos nodos existen)
        for e in universe.edges:
            if self.G.has_node(e.u) and self.G.has_node(e.v):
                self.G.add_edge(e.u, e.v, distance=e.distance, blocked=bool(getattr(e, "blocked", False)))
            # else: podrías loguear/avisar



    def _build(self):
        stars = {s.id: s for s in self.u.stars}
        # nodos
        for s in self.u.stars:
            self.G.add_node(s.id, x=s.x, y=s.y, galaxy=s.galaxyId, type=s.type, research=s.research)
        # aristas
        for e in self.u.edges:
            d = e.distance
            if d is None:
                a, b = stars[e.u], stars[e.v]
                d = math.hypot(a.x - b.x, a.y - b.y)
            self.G.add_edge(e.u, e.v, distance=d, blocked=e.blocked)


def neighbors(self, star_id: str):
    for v in self.G.neighbors(star_id):
        data = self.G[star_id][v]
        if not data.get("blocked", False):
            yield v, data["distance"]


def set_blocked(self, u: str, v: str, value: bool):
    if self.G.has_edge(u, v):
        self.G[u][v]["blocked"] = value


def coords(self, s: str):
    n = self.G.nodes[s]
    return n["x"], n["y"]