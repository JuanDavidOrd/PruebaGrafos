from typing import List, Set
from core.graph.space_graph import SpaceGraph
from core.models.donkey import Donkey


def route_static_max_nodes(G: SpaceGraph, start: str, donkey: Donkey) -> List[str]:
    visited: Set[str] = set([start])
    path: List[str] = [start]
    cur = start
    life = donkey.life_ly
    while True:
        options = []
        for v, d in G.neighbors(cur):
            if v in visited:
                continue
            if d <= life: # alcanzable
                options.append((1.0/d, v, d))
            if not options:
                break
        options.sort(reverse=True) # mejor ratio primero
        _, nxt, cost = options[0]
        path.append(nxt)
        visited.add(nxt)
        life -= cost
        cur = nxt
    return path