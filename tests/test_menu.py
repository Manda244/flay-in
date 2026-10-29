"""Tests for the level menu."""

from pathlib import Path

import pytest

from src.menu import LevelMenu, MenuError


def make_menu(tmp_path: Path) -> LevelMenu:
    """Create a menu on a folder that holds two easy maps."""
    easy = tmp_path / "easy"
    easy.mkdir()
    (easy / "02_fork.txt").write_text("x", encoding="utf-8")
    (easy / "01_linear.txt").write_text("x", encoding="utf-8")
    return LevelMenu(tmp_path)


def test_maps_are_sorted(tmp_path: Path) -> None:
    """The maps of a level are listed in alphabetical order."""
    menu = make_menu(tmp_path)
    assert menu.describe("easy") == ["1. 01_linear", "2. 02_fork"]


def test_pick_a_map(tmp_path: Path) -> None:
    """A valid number gives the matching map."""
    assert make_menu(tmp_path).pick("easy", "2").name == "02_fork.txt"


@pytest.mark.parametrize("answer", ["0", "3", "abc", ""])
def test_invalid_choice(tmp_path: Path, answer: str) -> None:
    """A wrong number or a text is refused with a clear message."""
    with pytest.raises(MenuError, match="between 1 and 2"):
        make_menu(tmp_path).pick("easy", answer)


def test_unknown_level(tmp_path: Path) -> None:
    """A level that does not exist is refused."""
    with pytest.raises(MenuError, match="unknown level"):
        make_menu(tmp_path).maps_of("expert")


def test_level_without_map(tmp_path: Path) -> None:
    """A known level without any map file is refused."""
    with pytest.raises(MenuError, match="no map found"):
        make_menu(tmp_path).maps_of("hard")
