from dataclasses import dataclass, field
from typing import List, TextIO, Dict, Tuple
# from numpy import ndarray, empty
from Agent import Agent
from Hospital import Hospital
from Human import Human
from sys import exit
from random import randint, choice, random
from time import sleep

# refaire l'implémentation plus tard :
# - avec des tuples de position (x, y) au lieu row et column
# - optimiser......
# - revoir le déplacement -> mettre die dedans ???
# - avec numpy
# - avec séparation des éléments de world en sous-classes

@dataclass
class World:
    _size: int
    _map: Dict[int, Dict[int, Agent]] = None
    _hospitalsPosition: List[Tuple[int, int]] = None
    _humansPosition: List[Tuple[int, int]] = None
    log: bool = False
    _logfile: TextIO = None
    _iteration: int = 0
    _stats: Dict[str, int] = None

    SYMBOL_EMPTY: str = field(default='. ')
    MAX_HOSPITALS: float = field(default=0.10)
    MAX_HUMANS: float = field(default=0.05)
    DUCK_VIRUS_MORTALITY: float = field(default=0.03)
    MORTALITY_STATE: int = field(default=10)

    def __post_init__(self):
        self._hospitalsPosition = []
        self._humansPosition = []
        self._stats = {
            'dead': 0,
            'contamined': 0,
            'recovered': 0,
            'safe': 0
        }

        self._map = {}
        for row in range(self._size):
            self._map[row] = {}
            for column in range(self._size):
                self._map[row][column] = None

        if self.log:
            self._logfile = open('log.txt', 'w')

    def __exit__(self):
        if self.log:
            self._logfile.close()

    def write_log(self, msg: str) -> None:
        if self.log:
            self._logfile.write(msg)

    @staticmethod
    def pause():
        sleep(0.01)

    def display(self) -> None:
        print('\033[2j')
        for x in range(self._size):
            print('    ', end='')
            for y in range(self._size):
                if self._map[x][y] is None:
                    print(World.SYMBOL_EMPTY, end='')
                else:
                    print(self._map[x][y], end='')
            print()

    def update_stats(self, state: str) -> None:
        if state == 'recoverOrDead':
            self._stats['contamined'] -= 1
            if random() <= World.DUCK_VIRUS_MORTALITY:
                self._stats['dead'] += 1
            else:
                self._stats['recovered'] += 1
        elif state == 'dead':
            self._stats['contamined'] -= 1
            self._stats['dead'] += 1
        elif state == 'contamined':
            self._stats['safe'] -= 1
            self._stats['contamined'] += 1
        elif state == 'safe':
            self._stats['safe'] += 1

    def display_stats(self) -> None:
        print('********** STATISTICS **********')
        print(f"* Safe : {self._stats['safe']:<10}")
        print(f"* Contamined : {self._stats['contamined']:<10}")
        print(f"* Recovered : {self._stats['recovered']:<10}")
        print(f"* Dead : {self._stats['dead']:<10}")
        print('********************************')

    def is_valid(self, x: int, y: int) -> bool:
        return 0 <= x < self._size and 0 <= y < self._size

    def is_hospital(self, x: int, y: int) -> bool:
        return self.is_valid(x, y) and isinstance(self._map[x][y], Hospital)

    def is_human(self, x: int, y: int) -> bool:
        return self.is_valid(x, y) and isinstance(self._map[x][y], Human)

    def is_empty(self, x: int, y: int) -> bool:
        return self.is_valid(x, y) and self._map[x][y] is None

    def add_agents(self, ag_type: str, ag_nb: int, world_max: float, sicks: int = 0) -> None:
        max_nb: int = self._size ** 2 * world_max
        if ag_nb > max_nb:
            print(f'{ag_type}s quantity exceed maximum value allowed : {ag_nb} > {max_nb} ({world_max * 100} % of the world)')
            exit(1)
        if sicks > ag_nb:
            print(f'Sicks quantity exceed number of safe humans : {sicks} > {ag_nb}')
            exit(1)
        for i in range(ag_nb - sicks):
            x, y = randint(0, self._size - 1), randint(0, self._size - 1)
            while not self.is_empty(x, y):
                x, y = randint(0, self._size - 1), randint(0, self._size - 1)
            if ag_type == 'Hospital':
                self._map[x][y] = Hospital()
                self._hospitalsPosition.append((x, y))
                self.write_log(f'Hospital in {x, y}\n')
            else:
                self._map[x][y] = Human()
                self.update_stats('safe')
                self._humansPosition.append((x, y))
                self.write_log(f'Human (safe) in {x, y}\n')
        if ag_type == 'Human':
            for i in range(sicks):
                x, y = randint(0, self._size - 1), randint(0, self._size - 1)
                while not self.is_empty(x, y):
                    x, y = randint(0, self._size - 1), randint(0, self._size - 1)
                self._map[x][y] = Human()
                self.update_stats('safe')
                self._map[x][y].contamine()
                self.update_stats('contamined')
                self._humansPosition.append((x, y))
                self.write_log(f'Human (contamined) in {x, y}\n')

    def initialize(self, hospitals: int, humans: int, sicks: int) -> None:
        self.write_log('**** initialization ****\n')
        self.add_agents('Hospital', hospitals, World.MAX_HOSPITALS)
        self.add_agents('Human', humans, World.MAX_HUMANS, sicks)

    def _vision(self, scope: int, x: int, y: int) -> Dict[str, List[Tuple[int, int]]]:
        neighborhood = {
            'empty': [],
            'hospital': [],
            'human': []
        }
        for x_range in range(-scope, scope + 1):
            for y_range in range(-scope, scope + 1):
                if abs(x_range) == scope or abs(y_range) == scope:
                    pos_x, pos_y = x + x_range, y + y_range
                    if self.is_hospital(pos_x, pos_y):
                        neighborhood['hospital'].append((pos_x, pos_y))
                    elif self.is_human(pos_x, pos_y):
                        neighborhood['human'].append((pos_x, pos_y))
                    elif self.is_empty(pos_x, pos_y):
                        neighborhood['empty'].append((pos_x, pos_y))
        return neighborhood

    def _contamination(self, x: int, y: int) -> None:
        neighborhood = self._vision(1, x, y)
        for x, y in neighborhood['human']:
            if not self._map[x][y].is_sick():
                self._map[x][y].contamine()
                self.write_log(f'Human {x, y} is contamined\n')
                self.update_stats('contamined')

    # découper en une autre fonction pour la mort !!!
    def _human_go_from_to(self, from_x: int, from_y: int, to_x: int, to_y: int) -> None:
        self._map[to_x][to_y] = self._map[from_x][from_y]
        self._map[to_x][to_y].set_position(to_x, to_y)
        self._map[from_x][from_y] = None
        self.write_log(f'Human {from_x, from_y} go to {to_x, to_y}\n')

    def _human_go_to_hospital(self, x: int, y: int, hospital: Tuple[int, int]) -> None:
        self._map[x][y] = None
        self.write_log(f"Human {x, y} go to hospital in {hospital}\n")
        self.update_stats('recoverOrDead')

    def _human_move_or_die(self, x: int, y: int, directions: List[Tuple[int, int]]) -> Tuple[int, int]:
        pos_x, pos_y = choice(directions)
        self._contamination(pos_x, pos_y)
        if self._map[x][y].get_state() == World.MORTALITY_STATE:
            self._map[x][y] = None
            self.write_log(f"Human {x, y} die\n")
            self.update_stats('dead')
            return None
        else:
            self._human_go_from_to(x, y, pos_x, pos_y)
            return pos_x, pos_y

    def _get_hospitals_directions(self, x: int, y: int, hospitals_pos: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        hospitals_directions = []
        for hospital_x, hospital_y in hospitals_pos:
            move_x, move_y = (hospital_x - x) // 2, (hospital_y - y) // 2
            dest_x, dest_y = x + move_x, y + move_y
            if self._map[dest_x][dest_y] is None:
                hospitals_directions.append((dest_x, dest_y))
        return hospitals_directions

    # je crois qu'on peut découper cette fonction !!!!
    def _move_human(self, x: int, y: int) -> Tuple[int, int]:
        neighborhood_1 = self._vision(1, x, y)
        if self._map[x][y].is_sick():
            self._map[x][y].increment_state()
            if neighborhood_1['hospital']:
                self._human_go_to_hospital(x, y, choice(neighborhood_1['hospital']))
                return None
            else:
                neighborhood_2 = self._vision(2, x, y)
                if neighborhood_2['hospital']:
                    directions = self._get_hospitals_directions(x, y, neighborhood_2['hospital'])
                    if not directions:
                        self.write_log(f'Human {x, y} stay at the same position\n')
                        return x, y
                    else:
                        return self._human_move_or_die(x, y, directions)
                else:
                    if neighborhood_1['empty']:
                        return self._human_move_or_die(x, y, neighborhood_1['empty'])
                    else:
                        self.write_log(f"Human {x, y} stay at the same position\n")
                        return x, y
        else:
            if neighborhood_1['empty']:
                pos_x, pos_y = choice(neighborhood_1['empty'])
                self._human_go_from_to(x, y, pos_x, pos_y)
                return pos_x, pos_y
            else:
                self.write_log(f"Human {x, y} stay at the same position\n")
                return x, y

    def generate_next_state(self) -> None:
        self._iteration += 1
        newHumansPosition = []
        self.write_log(f'\n\n**** Iteration #{self._iteration} ****\n')
        for human_x, human_y in self._humansPosition:
            new_pos = self._move_human(human_x, human_y)
            if new_pos:
                self.write_log(f'[DEBUG] - adding {new_pos}\n')
                newHumansPosition.append(new_pos)
        self._humansPosition = newHumansPosition

    def start_simulation(self, max_iterations: int) -> None:
        print('\033[2j')
        for iteration in range(max_iterations):
            self.display()
            World.pause()
            self.generate_next_state()
            if not self._humansPosition:
                self.write_log(f'[STOP] No more human in the simulation !\n')
                return
        self.write_log(f'[STOP] end of the simulation !\n')
        self.display_stats()

if __name__ == '__main__':
    world = World(40, log=True)
    world.initialize(hospitals=20, humans=80, sicks=40)
    world.start_simulation(max_iterations=600)
