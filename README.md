# Warehouse Robot Navigation: Reserve Aisles by Time

Two shortest paths can cross at the same cell or exchange cells in a single tick. This Python lab plans a route for each robot in order, then demonstrates a case where the chosen priority rule misses a valid schedule.

Full lesson: https://wifarobotics.com/learn/warehouse-robot-navigation/

## Get started

1. Install Python 3.12 from https://www.python.org/downloads/ (on Windows, enable the Python launcher if offered).
2. Clone `https://github.com/williamfarokhzad/wifa-warehouse-robot-navigation.git` and open the folder in a terminal. Without Git, download and unzip the repository ZIP. The terminal should be in the folder containing `planner.py`.
3. Run the commands below with `python3` on Linux/macOS, or replace `python3` with `py -3.12` on Windows. No packages, ROS, hardware, or account are needed to run the code.

```sh
python3 --version
python3 planner.py examples/crossing.json
python3 planner.py examples/dock-priority.json
python3 -m unittest discover -s tests -v
```

For the crossing case:

```text
A arrival=2: 0:(0,1) 1:(1,1) 2:(2,1)
B arrival=3: 0:(1,0) 1:(1,0) 2:(1,1) 3:(1,2)
Makespan: 3 ticks; all goals held through tick 6
```

`dock-priority.json` parks both robots by tick 2. Try the following one command at a time:

```sh
python3 planner.py examples/parked-dock.json
python3 planner.py examples/aisle-swap.json
python3 planner.py examples/bad-map.json
```

The first two exit 1 and issue no schedule; the bad map exits 2 and reports a blocked start. For a valid schedule, the program exits 0. In Bash inspect the code with `echo $?`; in PowerShell use `$LASTEXITCODE` immediately after the command. The unit tests include an independently replayed joint schedule for the aisle case that both fixed priority orders miss.

## Edit a scenario

Each row uses `.` for free cells and `#` for blocked cells. The top left is `[0,0]`; x increases to the right and y down. Each tick lets each robot wait or move one cell horizontally or vertically. The first robot in the list is planned first. Starts, goals, and names are each distinct. The search includes `horizon` itself. A parked robot stays at its goal through that tick. The program rejects same cell occupancy and opposite traversals of the same edge. Following one cell behind is permitted by the model.

If `planner.py` cannot be found, use `ls` or `dir` to check your folder. If a route misses the horizon, try a larger value on the crossing case; increasing the horizon cannot remove a permanently occupied goal. If the first robot's route causes a deadlock in the lab, changing priority sometimes helps, but the side bay case needs a joint plan. The CLI never returns a partial schedule.

`diagrams/render.py` regenerates the diagrams from the example planner output. To edit illustrations, install Pillow in a separate environment and run `python3 diagrams/render.py` from this directory. Diagram rendering is optional and unrelated to the simulator's runtime.

## Model boundaries

These are synthetic point robots and unit ticks. There is no robot footprint, pose uncertainty, braking, sensing, network timing, or people in the model. A tick is not a real time guarantee. Do not send these waypoints to a robot. Real deployments need a separate traffic, control and safety design.

References: [MAPF terminology and target policies](https://publications.ri.cmu.edu/multi-agent-pathfinding-definitions-variants-and-benchmarks), [Nav2 Route Server documentation](https://api.nav2.org/nav2-rolling/html/md_nav2_route_README.html), [Python deque](https://docs.python.org/3.12/library/collections.html#collections.deque).
