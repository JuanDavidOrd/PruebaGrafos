import json, math, sys
from pathlib import Path

PALETTE = ["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
            "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf"]

def _num(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

def convert_original_to_universe(src_dict: dict) -> tuple[dict, list[str]]:
    """
    Convierte tu formato original a UniverseIn (interno).
    Retorna (universe_dict, warnings_list).
    """
    warnings: list[str] = []
    galaxies = [{"id": "G1", "name": "ViaLactea"}]

    constellations_out = []
    stars_catalog: dict[str, dict] = {}
    memberships_out = []
    edges_out = []
    hyperlanes_out = []

    # Detecta constelaciones del JSON original
    orig_consts = src_dict.get("constellations") or []
    for i, c in enumerate(orig_consts, start=1):
        cid = str(c.get("id") or f"C{i}")
        cname = c.get("name") or f"Constelación {i}"
        color = c.get("color") or PALETTE[(i-1) % len(PALETTE)]
        constellations_out.append({
            "id": cid, "name": cname, "galaxyId": "G1", "color": color
        })

        # Estrellas en esa constelación
        for s in (c.get("starts") or []):
            sid = str(s.get("id") or "").strip()
            if not sid:
                warnings.append(f"[CONST {cid}] estrella sin id: se ignora")
                continue

            # Coordenadas
            coord = s.get("coordenates") or {}
            x = _num(coord.get("x"))
            y = _num(coord.get("y"))
            if x is None or y is None:
                warnings.append(f"[STAR {sid}] sin coordenadas: no se puede dibujar ni calcular distancias")
                # Igualmente registramos la membresía (para detectar multi-pertenencia)
                memberships_out.append({"starId": sid, "constellationId": cid})
                continue

            # Tipo e investigación
            hyper = bool(s.get("hypergiant"))
            tte = _num(s.get("timeToEat"), 1.0) or 1.0  # X por kg
            research = {
                "x_time_per_kg": float(tte),
                "invest_energy_per_x": 0.0,
                "disease_life_delta": 0.0,
            }

            # Crear/merge de la estrella en el catálogo global
            if sid in stars_catalog:
                old = stars_catalog[sid]
                if (abs(old["x"] - float(x)) > 1e-9) or (abs(old["y"] - float(y)) > 1e-9):
                    warnings.append(
                        f"[STAR {sid}] aparece en varias constelaciones con coords distintas; "
                        f"se mantienen ({old['x']}, {old['y']}) y se ignoran ({x}, {y})"
                    )
            else:
                stars_catalog[sid] = {
                    "id": sid,
                    "name": s.get("label") or s.get("name") or f"Star {sid}",
                    "galaxyId": "G1",
                    "x": float(x), "y": float(y),
                    "type": "hypergiant" if hyper else "normal",
                    "research": research,
                }

            # Registrar membresía (puede pertenecer a varias constelaciones)
            memberships_out.append({"starId": sid, "constellationId": cid})

            # Aristas (acepta starId o id)
            for lk in (s.get("linkedTo") or []):
                vid_raw = lk.get("starId", lk.get("id"))
                if vid_raw is None:
                    continue
                vid = str(vid_raw).strip()
                if not vid:
                    continue

                dist = _num(lk.get("distance"))

                # Orden para evitar duplicados u-v / v-u
                u, v = sorted([sid, vid])

                edges_out.append({
                    "u": u,
                    "v": v,
                    "distance": float(dist or 0.0),  # completamos si es 0 en segunda pasada
                    "blocked": False
                })

            # Hyperlanes (placeholder a G1; si usas varias galaxias, cámbialo)
            if hyper:
                hyperlanes_out.append({"starId": sid, "toGalaxyId": "G1"})

    # Segunda pasada: completa distancias si ambas coords existen
    for e in edges_out:
        if not e["distance"]:
            a, b = stars_catalog.get(e["u"]), stars_catalog.get(e["v"])
            if a and b:
                e["distance"] = float(math.hypot(a["x"] - b["x"], a["y"] - b["y"]))
            else:
                warnings.append(f"[EDGE {e['u']}-{e['v']}] sin distancia y sin coords del vecino")

    # Quitar duplicados exactos u-v
    seen = set()
    dedup = []
    for e in edges_out:
        key = (e["u"], e["v"])
        if key in seen:
            continue
        seen.add(key)
        dedup.append(e)
    edges_out = dedup

    universe = {
        "galaxies": galaxies,
        "constellations": constellations_out,
        "stars": list(stars_catalog.values()),
        "memberships": memberships_out,
        "edges": edges_out,
        "hyperlanes": hyperlanes_out,
    }
    return universe, warnings


def main(src_path: str, dst_path: str):
    src = json.loads(Path(src_path).read_text(encoding="utf-8"))
    uni, warns = convert_original_to_universe(src)
    Path(dst_path).write_text(json.dumps(uni, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: {dst_path}")
    if warns:
        print("\nADVERTENCIAS:")
        for w in warns:
            print(" -", w)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python tools/convert_from_original.py <src_original.json> <dst_normalized.json>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
