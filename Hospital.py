from dataclasses import dataclass, field
from Agent import Agent

@dataclass
class Hospital(Agent):
    SYMBOL: str = field(default='H ')

    def __post_init__(self):
        self._symbol = Hospital.SYMBOL
