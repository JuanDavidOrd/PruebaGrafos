from pydantic import BaseModel, Field
from typing import List, Optional
from core.models.enums import StarType


class GalaxyIn(BaseModel):
    id: str
    name: str


class ConstellationIn(BaseModel):
    id: str
    name: str
    galaxyId: str
    color: str


class ResearchIn(BaseModel):
    x_time_per_kg: float
    invest_energy_per_x: float
    disease_life_delta: float = 0.0


class StarIn(BaseModel):
    id: str
    name: str
    galaxyId: str
    x: float
    y: float
    type: StarType = StarType.NORMAL
    research: ResearchIn


class MembershipIn(BaseModel):
    starId: str
    constellationId: str


class EdgeIn(BaseModel):
    u: str
    v: str
    distance: Optional[float] = None
    blocked: bool = False


class HyperlaneIn(BaseModel):
    starId: str
    toGalaxyId: str


class UniverseIn(BaseModel):
    galaxies: List[GalaxyIn]
    constellations: List[ConstellationIn]
    stars: List[StarIn]
    memberships: List[MembershipIn]
    edges: List[EdgeIn] = Field(default_factory=list)
    hyperlanes: List[HyperlaneIn] = Field(default_factory=list)