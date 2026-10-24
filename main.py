"""Entry point of the Fly-in project."""

import sys

from src.parser import MapParser, ParseError
from src.renderer import TerminalRenderer
from src.simulation import Simulation, SimulationError

OPTIONS = ("--visual", "--gui")


def main() -> None:
    """Read a map, run the simulation and print the turns."""
    arguments = sys.argv[1:]
    options = [arg for arg in arguments if arg.startswith("--")]
    files = [arg for arg in arguments if not arg.startswith("--")]
    if len(files) != 1 or any(option not in OPTIONS for option in options):
        print("Usage: python3 main.py <map_file> [--visual] [--gui]")
        sys.exit(1)
    renderer = TerminalRenderer(sys.stdout.isatty())
    try:
        fly_map = MapParser(files[0]).parse()
        simulation = Simulation(fly_map)
        lines = simulation.run()
    except (ParseError, SimulationError) as error:
        print(f"Error: {error}")
        sys.exit(1)
    if "--visual" in options:
        renderer.show_map(fly_map)
        print()
    for line in lines:
        print(renderer.color_line(line, fly_map))
    if "--gui" in options:
        from src.gui import GraphicRenderer

        GraphicRenderer(fly_map).play(simulation.history)


if __name__ == "__main__":
    main()
