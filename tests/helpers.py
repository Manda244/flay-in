"""Helpers shared by the tests."""

from pathlib import Path

from src.fly_map import FlyMap
from src.parser import MapParser

MAPS = Path(__file__).resolve().parent / "maps"


def write_map(tmp_path: Path, content: str) -> str:
    """Write a map file in a temporary folder.

    Args:
        tmp_path: Temporary folder given by pytest.
        content: The text of the map.

    Returns:
        The path of the new file.
    """
    path = tmp_path / "map.txt"
    path.write_text(content, encoding="utf-8")
    return str(path)


def load_map(name: str) -> FlyMap:
    """Read a map of the "maps" folder.

    Args:
        name: The file name without ".txt", such as "simple".

    Returns:
        The map read from the file.
    """
    return MapParser(str(MAPS / f"{name}.txt")).parse()
