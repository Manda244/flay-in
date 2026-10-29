"""The maps of the maps folder, to change the map while the program runs."""

from pathlib import Path

from src.fly_map import FlyMap
from src.menu import LevelMenu
from src.parser import MapParser, ParseError
from src.simulation import Simulation, SimulationError

History = list[list[tuple[str, str | None]]]


class MapLibrary:
    """Keep the list of the maps and load the next or the previous one."""

    def __init__(self, maps_dir: Path, current: str) -> None:
        """Build the list of the maps.

        Args:
            maps_dir: The "maps" folder.
            current: The map file the program was started with.
        """
        paths = [path.resolve() for path in LevelMenu(maps_dir).all_maps()]
        start = Path(current).resolve()
        if start not in paths:
            paths.insert(0, start)
        self.paths: list[Path] = paths
        self.index: int = paths.index(start)

    def title(self) -> str:
        """Return the name and the position of the current map."""
        name = self.paths[self.index].stem
        return f"{name} ({self.index + 1}/{len(self.paths)})"

    def load(self, path: Path) -> tuple[FlyMap, History]:
        """Read a map and run its simulation.

        Args:
            path: The map file.

        Returns:
            The map and the positions of the drones after each turn.

        Raises:
            ParseError: If the map is invalid.
            SimulationError: If the simulation cannot finish.
        """
        fly_map = MapParser(str(path)).parse()
        simulation = Simulation(fly_map)
        simulation.run()
        return fly_map, simulation.history

    def switch(self, step: int) -> tuple[FlyMap, History, str] | None:
        """Load the next (step 1) or the previous (step -1) working map.

        Args:
            step: 1 for the next map, -1 for the previous one.

        Returns:
            The map, its history and its title, or None if no map works.
        """
        for _ in range(len(self.paths)):
            self.index = (self.index + step) % len(self.paths)
            try:
                fly_map, history = self.load(self.paths[self.index])
            except (ParseError, SimulationError):
                continue
            return fly_map, history, self.title()
        return None

    def names(self) -> list[str]:
        """Return a label such as "easy / 01_linear_path" for each map."""
        return [f"{path.parent.name} / {path.stem}" for path in self.paths]

    def select(self, index: int) -> tuple[FlyMap, History, str] | None:
        """Load the map number `index`.

        Args:
            index: The position of the map in the list.

        Returns:
            The map, its history and its title, or None if it cannot be
            loaded (the current map is then kept).
        """
        try:
            fly_map, history = self.load(self.paths[index])
        except (ParseError, SimulationError):
            return None
        self.index = index
        return fly_map, history, self.title()
