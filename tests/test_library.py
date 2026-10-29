"""Tests for the map library used to change the map in the window."""

from pathlib import Path

from src.library import MapLibrary

VALID_MAP = "nb_drones: 1\nstart_hub: s 0 0\nend_hub: g 1 0\nconnection: s-g\n"


def make_library(tmp_path: Path) -> MapLibrary:
    """Create a library with two good maps and one broken map."""
    files = [
        ("easy", "01_a.txt", VALID_MAP),
        ("easy", "02_bad.txt", "oops\n"),
        ("medium", "01_c.txt", VALID_MAP),
    ]
    for level, name, content in files:
        folder = tmp_path / level
        folder.mkdir(exist_ok=True)
        (folder / name).write_text(content, encoding="utf-8")
    return MapLibrary(tmp_path, str(tmp_path / "easy" / "01_a.txt"))


def test_title(tmp_path: Path) -> None:
    """The title gives the name and the position of the map."""
    assert make_library(tmp_path).title() == "01_a (1/3)"


def test_switch_skips_a_broken_map(tmp_path: Path) -> None:
    """The next map that works is loaded."""
    loaded = make_library(tmp_path).switch(1)
    assert loaded is not None
    assert loaded[2] == "01_c (3/3)"


def test_switch_wraps_around(tmp_path: Path) -> None:
    """After the last map, the first one comes back."""
    library = make_library(tmp_path)
    library.switch(1)
    loaded = library.switch(1)
    assert loaded is not None
    assert loaded[2] == "01_a (1/3)"


def test_previous_map(tmp_path: Path) -> None:
    """The previous map of the first one is the last one."""
    loaded = make_library(tmp_path).switch(-1)
    assert loaded is not None
    assert loaded[2] == "01_c (3/3)"


def test_names(tmp_path: Path) -> None:
    """Each map has a label with its level."""
    assert make_library(tmp_path).names() == [
        "easy / 01_a",
        "easy / 02_bad",
        "medium / 01_c",
    ]


def test_select(tmp_path: Path) -> None:
    """A map can be chosen by its position."""
    loaded = make_library(tmp_path).select(2)
    assert loaded is not None
    assert loaded[2] == "01_c (3/3)"


def test_select_broken_map(tmp_path: Path) -> None:
    """A broken map is refused and the current map is kept."""
    library = make_library(tmp_path)
    assert library.select(1) is None
    assert library.index == 0
