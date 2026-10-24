"""Tests for the pathfinding."""

from src.pathfinder import PathFinder
from src.zone import Zone
from tests.helpers import load_map


def names(path: list[Zone]) -> list[str]:
    """Return the zone names of a path."""
    return [zone.name for zone in path]


def test_bfs_counts_steps() -> None:
    """BFS takes the path with the fewest steps."""
    path = PathFinder(load_map("restricted_trap")).find_path()
    assert path is not None
    assert names(path) == ["s", "r1", "r2", "g"]


def test_dijkstra_counts_turns() -> None:
    """Dijkstra takes the path with the fewest turns."""
    finder = PathFinder(load_map("restricted_trap"))
    path = finder.find_cheapest_path()
    assert path is not None
    assert names(path) == ["s", "x", "y", "z", "g"]
    assert finder.path_cost(path) == 4


def test_priority_zone_is_preferred() -> None:
    """With equal turns, the path through a priority zone wins."""
    path = PathFinder(load_map("priority_tie")).find_cheapest_path()
    assert path is not None
    assert names(path) == ["s", "p", "e"]


def test_blocked_zone_gives_no_path() -> None:
    """A blocked zone cuts the only road."""
    finder = PathFinder(load_map("blocked"))
    assert finder.find_path() is None
    assert finder.find_cheapest_path() is None


def test_two_paths_on_diamond() -> None:
    """The diamond map has two paths sharing no zone."""
    paths = PathFinder(load_map("diamond")).find_paths(4)
    assert [names(path) for path in paths] == [
        ["s", "a", "g"],
        ["s", "b", "g"],
    ]


def test_subject_example_cheapest_path() -> None:
    """The cheapest path avoids the restricted zone."""
    path = PathFinder(load_map("subject_example")).find_cheapest_path()
    assert path is not None
    assert names(path) == ["hub", "corridorA", "tunnelB", "goal"]
