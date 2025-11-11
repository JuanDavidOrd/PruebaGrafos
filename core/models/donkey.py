from dataclasses import dataclass
from core.models.enums import Health


@dataclass
class Donkey:
    health: Health
    age: float # años
    energy_pct: float # 1..100
    grass_kg: float
    life_ly: float # años luz restantes


    def is_dead(self) -> bool:
        return self.life_ly <= 0 or self.energy_pct <= 0