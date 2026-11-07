"""Tests for the choice of several paths that share zones."""

from src.pathfinder import PathFinder
from src.simulation import Simulation
from tests.helpers import load_map


def test_banning_zones_gives_one_path() -> None:
    """Every path crosses the same two zones, so only one path remains."""
    finder = PathFinder(load_map("rows"))
    assert len(finder.find_paths(6)) == 1


def test_sharing_zones_gives_three_paths() -> None:
    """With a penalty, the three parallel rows are all found."""
    finder = PathFinder(load_map("rows"))
    assert len(finder.find_paths(6, 6)) == 3


def test_shared_paths_are_faster() -> None:
    """Using the three rows needs fewer turns than using only one."""
    fly_map = load_map("rows")
    baseline = len(Simulation(fly_map).play(None, False))
    shared = len(Simulation(fly_map).play(6, True))
    assert shared < baseline
    assert len(Simulation(fly_map).run()) <= shared
