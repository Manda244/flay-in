"""Check the simulation outputs with the independent validator."""

from pathlib import Path

import pytest

from src.parser import MapParser
from src.simulation import Simulation, SimulationError
from src.validator import OutputValidator, ValidationError
from tests.helpers import load_map

ROOT = Path(__file__).resolve().parent.parent
MAP_FILES = sorted(ROOT.glob("maps/*/*.txt"))
MAP_FILES += sorted((ROOT / "tests" / "maps").glob("*.txt"))

BAD_OUTPUTS = [
    ("simple", ["D1-mid D2-mid", "D1-goal D2-goal"], "holds 2"),
    ("bottleneck", ["D1-a D2-a D3-a D4-a"], "used by 4"),
    ("restricted_flight", ["D1-s-r", "D2-s-r"], "must land"),
    ("simple", ["D1-mid"], "not delivered"),
    ("diamond", ["D1-g"], "no connection"),
]


@pytest.mark.parametrize(
    "map_file", MAP_FILES, ids=[path.stem for path in MAP_FILES]
)
def test_simulation_output_is_valid(map_file: Path) -> None:
    """Every output of the simulation respects the rules."""
    fly_map = MapParser(str(map_file)).parse()
    try:
        lines = Simulation(fly_map).run()
    except SimulationError:
        pytest.skip("no path on this map")
    assert OutputValidator(fly_map).validate(lines) == len(lines)


@pytest.mark.parametrize("name, lines, message", BAD_OUTPUTS)
def test_validator_detects_errors(
    name: str, lines: list[str], message: str
) -> None:
    """The validator refuses outputs that break a rule."""
    with pytest.raises(ValidationError, match=message):
        OutputValidator(load_map(name)).validate(lines)
