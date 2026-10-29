"""Level menu to pick one of the maps of the maps folder."""

from pathlib import Path


class MenuError(Exception):
    """Raised when the level or the chosen number is not valid."""


class LevelMenu:
    """List the maps of a level and pick one of them."""

    LEVELS: tuple[str, ...] = ("easy", "medium", "hard", "challenger")

    def __init__(self, maps_dir: Path) -> None:
        """Store the folder that contains one sub-folder per level.

        Args:
            maps_dir: The "maps" folder.
        """
        self.maps_dir: Path = maps_dir

    def maps_of(self, level: str) -> list[Path]:
        """Return the map files of a level, sorted by name.

        Args:
            level: One of the names in LEVELS.

        Returns:
            The paths of the ".txt" files of this level.

        Raises:
            MenuError: If the level is unknown or has no map.
        """
        if level not in self.LEVELS:
            raise MenuError(
                f"unknown level '{level}' "
                f"(choose from {', '.join(self.LEVELS)})"
            )
        maps = sorted((self.maps_dir / level).glob("*.txt"))
        if not maps:
            raise MenuError(f"no map found for level '{level}'")
        return maps

    def describe(self, level: str) -> list[str]:
        """Return the numbered list of the maps of a level.

        Args:
            level: One of the names in LEVELS.

        Returns:
            Lines such as "1. 01_linear_path".
        """
        return [
            f"{number}. {path.stem}"
            for number, path in enumerate(self.maps_of(level), start=1)
        ]

    def pick(self, level: str, answer: str) -> Path:
        """Return the map matching the number typed by the user.

        Args:
            level: One of the names in LEVELS.
            answer: The text typed by the user, such as "2".

        Returns:
            The path of the chosen map.

        Raises:
            MenuError: If the answer is not a valid number.
        """
        maps = self.maps_of(level)
        try:
            number = int(answer)
        except ValueError:
            number = 0
        if not 1 <= number <= len(maps):
            raise MenuError(f"choose a number between 1 and {len(maps)}")
        return maps[number - 1]

    def all_maps(self) -> list[Path]:
        """Return the maps of every level, in the order of LEVELS.

        Returns:
            The paths of all the ".txt" maps found.
        """
        found: list[Path] = []
        for level in self.LEVELS:
            found.extend(sorted((self.maps_dir / level).glob("*.txt")))
        return found
