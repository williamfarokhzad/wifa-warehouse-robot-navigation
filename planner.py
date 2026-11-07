"""Teaching simulator: fixed priority routes on a grid with integer time."""
from collections import deque
from dataclasses import dataclass
import argparse
import json
from pathlib import Path
import sys

Cell = tuple[int, int]
PathCells = list[Cell]
MOVES = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))


@dataclass(frozen=True)
class Robot:
    name: str
    start: Cell
    goal: Cell


@dataclass(frozen=True)
class Scenario:
    cells: frozenset[Cell]
    robots: tuple[Robot, ...]
    horizon: int


class NoSchedule(Exception):
    """No result for this priority order and time bound."""


def read_scenario(data: object) -> Scenario:
    if not isinstance(data, dict):
        raise ValueError('expected a JSON object')
    grid, horizon, specs = (data.get(k) for k in ('grid', 'horizon', 'robots'))
    if not isinstance(grid, list) or not grid or not all(isinstance(r, str) for r in grid):
        raise ValueError('grid must contain strings of . and #')
    width = len(grid[0])
    if not width or any(len(r) != width or set(r) - {'.', '#'} for r in grid):
        raise ValueError('grid must be rectangular and contain only . and #')
    if type(horizon) is not int or not 0 <= horizon <= 250:
        raise ValueError('horizon must be an integer from 0 to 250')
    if width * len(grid) * (horizon + 1) > 250_000:
        raise ValueError('grid area times horizon plus one exceeds the lab limit (250,000 states)')
    cells = frozenset((x, y) for y, row in enumerate(grid) for x, symbol in enumerate(row) if symbol == '.')
    if not isinstance(specs, list) or not 1 <= len(specs) <= 16:
        raise ValueError('robots must contain 1 to 16 entries in priority order')

    def cell(value: object, label: str) -> Cell:
        if not isinstance(value, list) or len(value) != 2 or any(type(x) is not int for x in value):
            raise ValueError(f'{label}: expected two integer coordinates [x,y]')
        xy = (value[0], value[1])
        if xy not in cells:
            raise ValueError(f'{label}: cell is outside the grid or blocked')
        return xy

    robots = []
    for item in specs:
        if not isinstance(item, dict) or not isinstance(item.get('name'), str) or not item['name'].strip():
            raise ValueError('each robot needs a nonempty name')
        name = item['name']
        robots.append(Robot(name, cell(item.get('start'), f'{name} start'), cell(item.get('goal'), f'{name} goal')))
    for key in ('name', 'start', 'goal'):
        if len({getattr(robot, key) for robot in robots}) != len(robots):
            raise ValueError(f'robot {key} values must be distinct')
    return Scenario(cells, tuple(robots), horizon)


def position(path: PathCells, tick: int) -> Cell:
    return path[min(tick, len(path) - 1)]


def route(cells: frozenset[Cell], robot: Robot, horizon: int, earlier: list[PathCells]) -> PathCells | None:
    """Breadth first search over (cell, tick). Hold each earlier goal to horizon."""
    vertices = set()
    edges = set()
    last_occupied = {}
    for path in earlier:
        for tick in range(horizon + 1):
            here = position(path, tick)
            vertices.add((here, tick))
            last_occupied[here] = max(tick, last_occupied.get(here, -1))
            if tick < horizon:
                edges.add((here, position(path, tick + 1), tick))
    start = (robot.start, 0)
    if start in vertices:
        return None
    parent = {start: None}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        here, tick = state
        if here == robot.goal and last_occupied.get(here, -1) < tick:
            path = []
            while state is not None:
                path.append(state[0])
                state = parent[state]
            return path[::-1]
        if tick == horizon:
            continue
        for dx, dy in MOVES:
            there = (here[0] + dx, here[1] + dy)
            nxt = (there, tick + 1)
            if there not in cells or nxt in parent or nxt in vertices or (there, here, tick) in edges:
                continue
            parent[nxt] = state
            queue.append(nxt)
    return None


def schedule(scenario: Scenario) -> dict[str, PathCells]:
    paths = {}
    for robot in scenario.robots:
        path = route(scenario.cells, robot, scenario.horizon, list(paths.values()))
        if path is None:
            raise NoSchedule(f'{robot.name}: no route by tick {scenario.horizon} with this priority order; no schedule issued')
        paths[robot.name] = path
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scenario', type=Path, help='JSON input, e.g. examples/crossing.json')
    args = parser.parse_args()
    try:
        scenario = read_scenario(json.loads(args.scenario.read_text(encoding='utf-8')))
        paths = schedule(scenario)
    except NoSchedule as exc:
        print(exc, file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f'Invalid input: {exc}', file=sys.stderr)
        return 2
    for name, path in paths.items():
        waypoints = ' '.join(f'{tick}:({x},{y})' for tick, (x, y) in enumerate(path))
        print(f'{name} arrival={len(path)-1}: {waypoints}')
    print(f'Makespan: {max(map(len, paths.values())) - 1} ticks; all goals held through tick {scenario.horizon}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
