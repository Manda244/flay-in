"""Entry point of the Fly-in project."""

import sys
from pathlib import Path

from src.library import MapLibrary
from src.menu import LevelMenu, MenuError
from src.parser import MapParser, ParseError
from src.renderer import TerminalRenderer
from src.simulation import Simulation, SimulationError

OPTIONS = ("--visual", "--gui")
USAGE = (
    "Usage: python3 main.py <map_file> [--visual] [--gui]\n"
    "       python3 main.py --level=<easy|medium|hard|challenger> "
    "[--visual] [--gui]"
)


def pick_level_map(level: str) -> str:
    """Show the maps of a level and ask which one to run.

    Args:
        level: The level name, such as "easy".

    Returns:
        The path of the chosen map file.

    Raises:
        MenuError: If the level or the choice is not valid.
    """
    menu = LevelMenu(Path(__file__).resolve().parent / "maps")
    print(f"Maps of level '{level}':")
    for line in menu.describe(level):
        print(f"  {line}")
    try:
        answer = input("Choose a map number: ")
    except EOFError:
        raise MenuError("no choice given") from None
    return str(menu.pick(level, answer.strip()))


def main() -> None:
    """Read a map, run the simulation and print the turns."""
    arguments = sys.argv[1:]
    options = [arg for arg in arguments if arg.startswith("--")]
    files = [arg for arg in arguments if not arg.startswith("--")]
    levels = [opt[8:] for opt in options if opt.startswith("--level=")]
    flags = [opt for opt in options if not opt.startswith("--level=")]
    if any(flag not in OPTIONS for flag in flags):
        print(USAGE)
        sys.exit(1)
    if len(files) + len(levels) != 1:
        print(USAGE)
        sys.exit(1)
    renderer = TerminalRenderer(sys.stdout.isatty())
    try:
        map_file = files[0] if files else pick_level_map(levels[0])
        fly_map = MapParser(map_file).parse()
        simulation = Simulation(fly_map)
        lines = simulation.run()
    except (ParseError, SimulationError, MenuError) as error:
        print(f"Error: {error}")
        sys.exit(1)
    if "--visual" in flags:
        renderer.show_map(fly_map)
        print()
    for line in lines:
        print(renderer.color_line(line, fly_map))
    if "--gui" in flags:
        from src.gui import GraphicRenderer

        maps_dir = Path(__file__).resolve().parent / "maps"
        library = MapLibrary(maps_dir, map_file)
        GraphicRenderer(fly_map).play(simulation.history, library)


if __name__ == "__main__":
    main()
