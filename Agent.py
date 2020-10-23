from dataclasses import dataclass
from typing import Tuple

@dataclass
class Agent:
    _symbol: str = ''
    _position: Tuple[int, int] = (0, 0)

    def get_position(self) -> Tuple[int, int]:
        return self._position

    def get_position_row(self) -> int:
        return self._position[0]

    def get_position_column(self) -> int:
        return self._position[1]

    def set_position(self, x: int, y: int) -> None:
        self._position = (x, y)

    def __str__(self) -> str:
        return self._symbol
