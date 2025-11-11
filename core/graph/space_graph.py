import math
import networkx as nx

RED_MULTI = "#d62728"


class SpaceGraph:
    def __init__(self, universe):
        """
        Construye un grafo no dirigido con:
        - nodos: id, x, y, type, galaxyId
        - aristas: distance, blocked
        'universe.stars' y 'universe.edges' deben existir.
        """
        self.G = nx.Graph()

        # --- Nodos ---
        for s in universe.stars:
            self.G.add_node(
                str(s.id),
                x=float(s.x) if s.x is not None else None,
                y=float(s.y) if s.y is not None else None,
                type=getattr(s, "type", None),
                galaxyId=getattr(s, "galaxyId", None),
            )

        # --- Aristas ---
        for e in universe.edges:
            u = str(e.u)
            v = str(e.v)
            if not (self.G.has_node(u) and self.G.has_node(v)):
                continue

            # distancia: usa la del JSON o calcula por coordenadas
            d = getattr(e, "distance", None)
            if d is None:
                nx_u = self.G.nodes[u]
                nx_v = self.G.nodes[v]
                if nx_u.get("x") is not None and nx_v.get("x") is not None:
                    d = math.hypot(nx_u["x"] - nx_v["x"], nx_u["y"] - nx_v["y"])
                else:
                    d = 0.0

            blocked = bool(getattr(e, "blocked", False))
            self.G.add_edge(u, v, distance=float(d), blocked=blocked)

    # ---------- API de ayuda ----------

    def neighbors(self, star_id: str):
        """Vecinos no bloqueados de 'star_id' con su distancia."""
        sid = str(star_id)
        if not self.G.has_node(sid):
            return
        for v in self.G.neighbors(sid):
            data = self.G[sid][v]
            if not data.get("blocked", False):
                yield str(v), float(data.get("distance", 0.0))

    def set_blocked(self, u: str, v: str, value: bool):
        """Marca/desmarca una arista como bloqueada."""
        uu, vv = str(u), str(v)
        if self.G.has_edge(uu, vv):
            self.G[uu][vv]["blocked"] = bool(value)

    def coords(self, s: str):
        """Devuelve (x, y) del nodo 's'."""
        sid = str(s)
        n = self.G.nodes[sid]
        return n.get("x"), n.get("y")
