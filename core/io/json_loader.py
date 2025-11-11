from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]  # raíz de PruebaGrafos
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from pathlib import Path
from pydantic import ValidationError
from core.io.schema import UniverseIn
from tools.convert_from_original import convert_original_to_universe

def load_universe(path: str | Path) -> UniverseIn:
    """
    1) Intenta cargar como UniverseIn.
    2) Si falla, detecta formato original (constellations->starts, coordenates, linkedTo, hypergiant)
    y lo convierte en memoria.
    3) Si aún falla, levanta un error explicando qué campos faltan.
    """
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))

    # Intento 1: esquema interno
    try:
        return UniverseIn.model_validate(raw)
    except ValidationError as e1:
        # ¿Huele a formato original?
        is_original = False
        if isinstance(raw, dict):
            if "constellations" in raw:
                # mirar una constelación ejemplo
                cons = raw.get("constellations") or []
                if cons and isinstance(cons[0], dict) and "starts" in cons[0]:
                    is_original = True

        if not is_original:
            # Re-lanza error con explicación clara
            raise RuntimeError(
                "El JSON no coincide con el formato interno (UniverseIn) y no parece ser el formato original.\n"
                f"Detalle de validación:\n{e1}"
            ) from e1

        # Intento 2: convertir original -> interno
        uni_dict, warns = convert_original_to_universe(raw)

        # Si hay advertencias, lánzalas como RuntimeError suave (aparecen en QMessageBox)
        if warns:
            # No detenemos la ejecución por warnings; sólo informamos al usuario en UI si deseas.
            # Aquí las ignoramos para permitir dibujar. Puedes loguearlas en consola/archivo.
            pass

        try:
            return UniverseIn.model_validate(uni_dict)
        except ValidationError as e2:
            raise RuntimeError(
                "Se detectó el formato original y se intentó convertirlo, "
                "pero aún faltan datos obligatorios (p. ej., coordenadas de algunas estrellas). "
                "Completa las coordenadas o elimina enlaces a estrellas inexistentes.\n"
                f"Detalle:\n{e2}"
            ) from e2
