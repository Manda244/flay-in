"""Entry point of the Fly-in project."""

import sys
from pathlib import Path

from parser import MapParser, ParseError
from renderer import TerminalRenderer
from simulation import Simulation, SimulationError

OPTIONS = ("--gui",)
USAGE = "Usage: python3 main.py <map_file> [--gui]"


def main() -> None:
    """Read a map, run the simulation and print the turns."""
    arguments = sys.argv[1:]
    flags = [arg for arg in arguments if arg.startswith("--")]
    files = [arg for arg in arguments if not arg.startswith("--")]
    if any(flag not in OPTIONS for flag in flags) or len(files) != 1:
        print(USAGE)
        sys.exit(1)
    renderer = TerminalRenderer(sys.stdout.isatty())
    try:
        fly_map = MapParser(files[0]).parse()
        simulation = Simulation(fly_map)
        lines = simulation.run()
    except (ParseError, SimulationError) as error:
        print(f"Error: {error}")
        sys.exit(1)
    for line in lines:
        print(renderer.color_line(line, fly_map))
    if "--gui" in flags:
        try:
            from gui import GraphicRenderer

            GraphicRenderer(fly_map).play(
                simulation.history, Path(files[0]).stem
            )
        except ImportError:
            print("Pygame not installed")
        except BaseException:
            pass


if __name__ == "__main__":
    main()
