*This project has been created as part of the 42 curriculum by marasolo.*

# Fly-in

## Description

Fly-in routes a fleet of drones from a start zone to an end zone through a
network of connected zones, in as few simulation turns as possible.

The program reads a map file, builds the graph by hand (no graph library),
finds paths, and simulates the flight turn by turn. A zone has a type
(`normal`, `priority`, `restricted` or `blocked`) and a capacity
(`max_drones`). A connection is bidirectional and has a capacity
(`max_link_capacity`). Entering a `restricted` zone costs 2 turns: the drone
is in flight on the connection during the first turn and must land during
the second one.

The project is written in Python 3.10+ (developed with 3.13), is fully
object-oriented, passes `flake8`, and is type-checked with `mypy`.

## Instructions

Requirements: Python 3.10 or later and `pip`.

~~~
make install                      # install flake8, mypy and pytest
make run                          # run on maps/subject_example.txt
make run MAP=maps/diamond.txt     # choose another map
make run ARGS=--visual            # describe the map before the turns
make run ARGS=--gui                 # open the pygame window
make level LEVEL=easy              # pick a map of a level
make test                         # run the unit tests (pytest)
make lint                         # flake8 and mypy
make lint-strict                  # flake8 and mypy --strict (optional)
make debug                        # run with the Python debugger (pdb)
make clean                        # remove caches
~~~

Without `make`: `python3 main.py <map_file> [--visual]`.

### Map file format

~~~
nb_drones: 5
start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: corridorA 4 3 [zone=priority max_drones=2]
connection: hub-roof1
connection: hub-corridorA [max_link_capacity=2]
~~~

Metadata in brackets is optional. Lines starting with `#` are comments. Zone
names cannot contain dashes or spaces. Any error stops the program with a
message giving the line and the cause.

## Algorithm choices and implementation strategy

**Parsing.** `MapParser` reads the file line by line and checks every rule
of the subject (first line, unique start and end, unique names, integer
coordinates, positive capacities, no duplicate connection, valid zone types).
Errors are raised as `ParseError` with the line number.

**Graph.** `FlyMap` stores the zones, the connections and an adjacency list:
a dictionary that gives, for each zone name, the connections touching it.
It is built once. The neighbors of a zone are found with
`Connection.other_end`, in time proportional to the number of its
connections.

**Pathfinding.** `PathFinder.find_cheapest_path` is a Dijkstra search with a
priority queue (`heapq`). The cost of a move is the number of turns needed
to enter the destination zone (1, or 2 for `restricted`). Blocked zones are
never entered. A priority zone costs 1 turn like a normal one, but when two
paths take the same number of turns, the one with more priority zones wins
(the heap compares the pair `(turns, score)`). Complexity: O((V + E) log V)
time and O(V) memory. A simple BFS (`find_path`) is also kept: it counts
steps, not turns, so it can choose a slower path when a restricted zone is
involved.

**Several paths.** To avoid a traffic jam on a single path,
`PathFinder.find_paths` finds the cheapest path, bans its intermediate zones,
and searches again, until no path is left. `plan_paths` then assigns each
drone to the path where it is expected to arrive first (path cost plus the
number of drones already sent on it). This greedy method is simple and
fast, O(k (V + E) log V + N k) for k paths and N drones, but it is not always
optimal: the first path is chosen alone. A maximum-flow algorithm would be
the rigorous improvement.

**Simulation.** `Simulation.step` plays one turn:
1. drones already in flight land (they cannot wait on a connection);
2. the other drones are examined from the most advanced to the least
   advanced, so a drone that leaves a zone frees its place in the same turn;
3. a move is accepted only if the destination zone and the connection both
   have room; counters are updated as moves are accepted;
4. a drone going to a `restricted` zone takes off, and its place in the
   destination zone is reserved immediately;
5. if no drone can move while some are not delivered, a `SimulationError`
   is raised (deadlock guard).

Paths are computed once before the simulation, not at every turn. The
per-turn counters are rebuilt each turn in O(N).

## Visual representation

The output is colored in the terminal with ANSI codes: each movement takes
the `color` of its destination zone, so it is easy to see where each drone
goes. With `--visual`, the program first prints a description of the map
(zones with type, capacity and position; connections with capacity).
Colors are disabled automatically when the output is not a terminal
(file, pipe), so the text always follows the format of the subject. A color
name that is not known is printed without color.

### Graphical mode

`make run ARGS=--gui` opens a pygame window after the simulation. Each zone
is a honeycomb cell filled with its `color`. The border shows the type of the
zone (gold: priority, red: restricted, black: blocked) and the thickness of a
connection shows its capacity. The drones are robot bees that fly from cell
to cell, turn after turn, the queen waits on the end zone, and a counter shows
the delivered drones. Keys: SPACE plays the next turn, A starts or stops the automatic
replay, R restarts it, M opens a list to choose a
map (N and P load the next or the previous one), ESC quits. The mouse wheel (or + and -) zooms toward the cursor, the arrow keys move the view when it is
zoomed in, and the window can be resized.
If the images of `assets/` are missing, simple shapes are drawn
instead. `pygame` is only used for the display (`make install` installs it).

## Example input and output

Input (`maps/subject_example.txt`, 5 drones):

~~~
nb_drones: 5
start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
~~~

Output (6 turns, one line per turn; `D3-hub-roof1` means that D3 is in flight
on the connection hub-roof1):

~~~
D1-corridorA D3-hub-roof1
D1-tunnelB D2-corridorA D3-roof1
D1-goal D2-tunnelB D3-roof2 D4-corridorA D5-hub-roof1
D2-goal D3-goal D4-tunnelB D5-roof1
D4-goal D5-roof2
D5-goal
~~~

## Assumptions and limitations

The subject does not specify everything. The choices made are:
- a drone in flight is printed as `D<ID>-<zone1>-<zone2>` (the connection);
- the connection of a flight counts for both turns of the flight;
- the place in a restricted destination zone is reserved at take-off;
- unknown metadata keys are a parsing error;
- only lines that start with `#` are comments;
- `max_drones` on the start and end zones is validated like on other zones,
  although the subject says it is ignored there.

## Project structure

~~~
main.py              entry point
src/zone.py          Zone and ZoneType
src/connection.py    Connection
src/fly_map.py       FlyMap (graph with adjacency lists)
src/parser.py        MapParser and ParseError
src/pathfinder.py    PathFinder (BFS, Dijkstra, several paths)
src/drone.py         Drone
src/simulation.py    Simulation and SimulationError
src/renderer.py      TerminalRenderer
src/gui.py           GraphicRenderer (pygame window)
src/validator.py     OutputValidator (checks the outputs)
assets/              bee and queen images
maps/                example and test maps
tests/               pytest unit tests
~~~

## Resources

- Breadth-first search: https://en.wikipedia.org/wiki/Breadth-first_search
- Dijkstra's algorithm: https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
- Python `heapq`: https://docs.python.org/3/library/heapq.html
- Python `collections.deque`:
  https://docs.python.org/3/library/collections.html#collections.deque
- PEP 257, docstring conventions: https://peps.python.org/pep-0257/
- `mypy` documentation: https://mypy.readthedocs.io
- `flake8` documentation: https://flake8.pycqa.org
- `pytest` documentation: https://docs.pytest.org
- `pygame` documentation: https://www.pygame.org/docs/
- ANSI escape codes: https://en.wikipedia.org/wiki/ANSI_escape_code

### How AI was used

An AI assistant (Claude, by Anthropic) was used as a step-by-step tutor:
- to explain the subject, graphs, BFS, Dijkstra and the turn-based
  simulation with small examples;
- to propose the class architecture and to write small pieces of code, each
  explained before it was used;
- to help diagnose errors (indentation, `mypy` messages, test failures);
- to draft the tests, the `Makefile`, the output validator, the
  pygame display and this README;
- to remove the background of the two images of `assets/`, which
  were provided by the author.

Every piece of code was run and checked with `flake8`, `mypy` and `pytest`,
and was read and understood by the author before being kept.

## Performance

Number of turns on the maps given with the subject (target in parentheses):

| Level | Map | Drones | Target | Result |
|---|---|---|---|---|
| Easy | linear_path | 2 | <= 6 | 4 |
| Easy | simple_fork | 4 | <= 8 | 6 |
| Easy | basic_capacity | 4 | <= 6 | 4 |
| Medium | dead_end_trap | 5 | <= 12 | 8 |
| Medium | circular_loop | 6 | <= 15 | 15 |
| Medium | priority_puzzle | 5 | <= 12 | 8 |
| Hard | maze_nightmare | 8 | <= 30 | 13 |
| Hard | capacity_hell | 12 | <= 35 | 16 |
| Hard | ultimate_challenge | 15 | <= 45 | 26 |
| Challenger | impossible_dream | 25 | record: 45 | 67 |

The challenger map is not solved better than the reference record: the
greedy choice of paths is not optimal, and a maximum-flow approach would be
the next improvement.
