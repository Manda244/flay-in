"""Tests for the simulation."""

import pytest

from src.simulation import Simulation, SimulationError
from tests.helpers import load_map


def run(name: str) -> list[str]:
    """Run the simulation on a map of the "maps" folder."""
    return Simulation(load_map(name)).run()


def test_zone_capacity_makes_drones_wait() -> None:
    """A zone of capacity 1 lets the drones pass one by one."""
    assert run("simple") == ["D1-mid", "D1-goal D2-mid", "D2-goal"]


def test_link_capacity_limits_departures() -> None:
    """A link of capacity 2 lets only two drones leave per turn."""
    lines = run("bottleneck")
    assert lines[0] == "D1-a D2-a"
    assert len(lines) == 3


def test_pipeline_turns() -> None:
    """Five drones on a chain take 2 + (5 - 1) turns."""
    assert len(run("chain5")) == 6


def test_restricted_zone_takes_two_turns() -> None:
    """A drone flies one turn on the link, then lands."""
    assert run("restricted_flight") == [
        "D1-s-r",
        "D1-r",
        "D1-g D2-s-r",
        "D2-r",
        "D2-g",
    ]


def test_two_paths_are_faster() -> None:
    """Using two paths reduces the number of turns."""
    assert len(run("diamond")) == 3
    assert len(run("subject_example")) == 6


def test_no_path_raises() -> None:
    """A map without any path raises a SimulationError."""
    with pytest.raises(SimulationError, match="no path"):
        run("blocked")
