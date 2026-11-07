import itertools
import json
from pathlib import Path
import unittest

from planner import NoSchedule, Robot, read_scenario, route, schedule

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'


def load(name):
    return read_scenario(json.loads((EXAMPLES / f'{name}.json').read_text()))


def check_timeline(test, scenario, result):
    """Independent replay: inspect actual pairs, never use reservations."""
    paths = []
    for robot in scenario.robots:
        path = result[robot.name]
        test.assertEqual(path[0], robot.start)
        test.assertEqual(path[-1], robot.goal)
        test.assertLessEqual(len(path) - 1, scenario.horizon)
        test.assertTrue(all(cell in scenario.cells for cell in path))
        for before, after in zip(path, path[1:]):
            test.assertLessEqual(sum(abs(a - b) for a, b in zip(before, after)), 1)
        paths.append(path + [robot.goal] * (scenario.horizon + 1 - len(path)))
    for a, b in itertools.combinations(paths, 2):
        for t in range(scenario.horizon + 1):
            test.assertNotEqual(a[t], b[t], f'shared cell at {t}')
            if t:
                test.assertFalse((a[t - 1], b[t - 1]) == (b[t], a[t]), f'edge swap into {t}')


class PlannerTests(unittest.TestCase):
    def test_crossing_requires_wait_and_replays(self):
        s = load('crossing')
        result = schedule(s)
        check_timeline(self, s, result)
        self.assertEqual(result['B'], [(1, 0), (1, 0), (1, 1), (1, 2)])

    def test_tick_bound_one_short(self):
        s = load('crossing')
        with self.assertRaises(NoSchedule):
            schedule(type(s)(s.cells, s.robots, 2))
        check_timeline(self, type(s)(s.cells, s.robots, 3), schedule(type(s)(s.cells, s.robots, 3)))

    def test_two_distinct_end_cells_do_not_make_swap_legal(self):
        west, east = (0, 0), (1, 0)
        self.assertIsNone(route(frozenset((west, east)), Robot('B', east, west), 1, [[west, east]]))

    def test_passing_through_future_goal_does_not_park_early(self):
        # B starts at its eventual goal, but A must pass through it at tick 1.
        scenario = read_scenario({'grid':['#.#','...'], 'horizon':5, 'robots':[
            {'name':'A','start':[0,1],'goal':[2,1]}, {'name':'B','start':[1,1],'goal':[1,1]}]})
        paths = schedule(scenario)
        check_timeline(self, scenario, paths)
        self.assertEqual(paths['B'], [(1, 1), (1, 0), (1, 1)])

    def test_parked_goal_and_priority_reversal(self):
        with self.assertRaisesRegex(NoSchedule, '^B:'):
            schedule(load('parked-dock'))
        good = load('dock-priority')
        check_timeline(self, good, schedule(good))

    def test_fixed_order_can_fail_despite_valid_joint_plan(self):
        s = load('aisle-swap')
        with self.assertRaises(NoSchedule):
            schedule(s)
        with self.assertRaises(NoSchedule):
            schedule(type(s)(s.cells, tuple(reversed(s.robots)), s.horizon))
        witness = {'A': [(0,1),(1,1),(1,0),(1,1),(2,1)], 'B': [(2,1),(2,1),(1,1),(0,1)]}
        check_timeline(self, s, witness)

    def test_bad_cell(self):
        with self.assertRaisesRegex(ValueError, 'blocked'):
            load('bad-map')

    def test_duplicate_start_and_bool_coordinate(self):
        robot = {'name':'B','start':[0,0],'goal':[1,0]}
        data = {'grid':['..'],'horizon':3,'robots':[{'name':'A','start':[0,0],'goal':[0,0]},robot]}
        with self.assertRaisesRegex(ValueError, 'start values must be distinct'):
            read_scenario(data)
        robot['start'] = [True, 0]
        with self.assertRaisesRegex(ValueError, 'integer coordinates'):
            read_scenario(data)

    def test_zero_tick_parking(self):
        s = read_scenario({'grid':['.'],'horizon':0,'robots':[{'name':'A','start':[0,0],'goal':[0,0]}]})
        check_timeline(self, s, schedule(s))
        self.assertEqual(schedule(s), {'A': [(0, 0)]})


if __name__ == '__main__':
    unittest.main()
