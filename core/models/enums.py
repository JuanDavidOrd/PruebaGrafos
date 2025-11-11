from enum import Enum


class Health(str, Enum):
    EXCELLENT = "excellent"
    REGULAR = "regular"
    BAD = "bad"


class StarType(str, Enum):
    NORMAL = "normal"
    HYPERGIANT = "hypergiant"