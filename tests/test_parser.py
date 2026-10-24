"""Tests for the map parser."""

from pathlib import Path

import pytest

from src.parser import MapParser, ParseError
from src.zone import ZoneType
from tests.helpers import write_map

VALID_MAP = (
    "# a small map\n"
    "nb_drones: 2\n"
    "start_hub: s 0 0 [color=green]\n"
    "end_hub: g 2 0\n"
    "hub: a 1 0 [zone=restricted max_drones=2]\n"
    "connection: s-a [max_link_capacity=3]\n"
    "connection: a-g\n"
)

INVALID_MAPS = [
    (
        "start_hub: s 0 0\nend_hub: e 1 0\n",
        "first line must define nb_drones",
    ),
    (
        "nb_drones: 0\nstart_hub: s 0 0\nend_hub: e 1 0\n",
        "must be positive",
    ),
    (
        "nb_drones: 1\nstart_hub: s 0 0\nstart_hub: t 1 0\n",
        "only one start_hub",
    ),
    (
        "nb_drones: 1\nstart_hub: s 0 0\nhub: a 1 0\n",
        "end_hub is missing",
    ),
    (
        "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 2 0\nhub: s 1 0\n",
        "already defined",
    ),
    (
        "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 0\n"
        "connection: s-e\nconnection: e-s\n",
        "already defined",
    ),
    (
        "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 0\n"
        "connection: s-ghost\n",
        "unknown zone 'ghost'",
    ),
]


def test_valid_map(tmp_path: Path) -> None:
    """A valid map is read correctly."""
    fly_map = MapParser(write_map(tmp_path, VALID_MAP)).parse()
    assert fly_map.nb_drones == 2
    assert fly_map.start.name == "s"
    assert fly_map.start.color == "green"
    assert fly_map.end.name == "g"
    zone = fly_map.zones["a"]
    assert zone.zone_type == ZoneType.RESTRICTED
    assert zone.max_drones == 2
    assert len(fly_map.connections) == 2
    assert fly_map.connections[0].max_link_capacity == 3
    assert fly_map.connections[1].max_link_capacity == 1


@pytest.mark.parametrize("content, message", INVALID_MAPS)
def test_invalid_map(tmp_path: Path, content: str, message: str) -> None:
    """Each broken map raises a ParseError with a clear cause."""
    with pytest.raises(ParseError, match=message):
        MapParser(write_map(tmp_path, content)).parse()


def test_missing_file(tmp_path: Path) -> None:
    """A file that does not exist raises a ParseError."""
    with pytest.raises(ParseError, match="cannot read"):
        MapParser(str(tmp_path / "nope.txt")).parse()
