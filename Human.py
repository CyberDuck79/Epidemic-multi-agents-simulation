from dataclasses import dataclass, field
from Agent import Agent

@dataclass
class Human(Agent):
    _state: int = 0

    SYMBOL: str = field(default='X ')
    SYMBOL_SICK: str = field(default='O ')

    def __post_init__(self):
        self._symbol = Human.SYMBOL

    def contamine(self) -> None:
        self._state = 1

    def is_sick(self) -> bool:
        return self._state != 0

    def get_state(self) -> int:
        return self._state

    def increment_state(self) -> None:
        self._state += 1

    def __str__(self) -> str:
        if self.is_sick():
            return Human.SYMBOL_SICK
        else:
            return self._symbol
