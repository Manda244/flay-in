"""Colored terminal display for the Fly-in project."""

from src.fly_map import FlyMap
from src.zone import Zone


class TerminalRenderer:
    """Print the map and the simulation turns, in color if possible."""

    RESET: str = "\033[0m"
    COLORS: dict[str, str] = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "gray": "\033[90m",
        "grey": "\033[90m",
        "orange": "\033[38;5;208m",
        "purple": "\033[38;5;93m",
        "pink": "\033[38;5;213m",
        "brown": "\033[38;5;94m",
    }

    def __init__(self, use_color: bool) -> None:
        """Create a renderer.

        Args:
            use_color: True to print colors, False for plain text.
        """
        self.use_color: bool = use_color

    def colorize(self, text: str, color: str | None) -> str:
        """Wrap a text with the ANSI code of a color.

        Args:
            text: The text to color.
            color: The color name, or None.

        Returns:
            The colored text, or the text unchanged if colors are
            disabled or the color name is unknown.
        """
        if not self.use_color or color is None:
            return text
        code = self.COLORS.get(color.lower())
        if code is None:
            return text
        return f"{code}{text}{self.RESET}"

    def color_line(self, line: str, fly_map: FlyMap) -> str:
        """Color each movement of a turn by its destination zone.

        Args:
            line: A turn line such as "D1-a D2-s-r".
            fly_map: The map, used to find the zone colors.

        Returns:
            The same line, with colored movements.
        """
        words: list[str] = []
        for move in line.split():
            _, _, rest = move.partition("-")
            zone = fly_map.zones.get(rest.split("-")[-1])
            color = zone.color if zone is not None else None
            words.append(self.colorize(move, color))
        return " ".join(words)

    def describe_zone(self, zone: Zone, fly_map: FlyMap) -> str:
        """Return a one-line description of a zone.

        Args:
            zone: The zone to describe.
            fly_map: The map, used to know the start and end zones.

        Returns:
            A text such as "hub (start): normal, unlimited, at (0, 0)".
        """
        name = self.colorize(zone.name, zone.color)
        role = ""
        capacity = f"max_drones={zone.max_drones}"
        if zone is fly_map.start:
            role = " (start)"
            capacity = "unlimited"
        elif zone is fly_map.end:
            role = " (end)"
            capacity = "unlimited"
        return (
            f"{name}{role}: {zone.zone_type.value}, {capacity}, "
            f"at ({zone.x}, {zone.y})"
        )

    def show_map(self, fly_map: FlyMap) -> None:
        """Print the zones and the connections of the map.

        Args:
            fly_map: The map to describe.
        """
        print(f"Drones: {fly_map.nb_drones}")
        print("Zones:")
        for zone in fly_map.zones.values():
            print(f"  {self.describe_zone(zone, fly_map)}")
        print("Connections:")
        for connection in fly_map.connections:
            first = self.colorize(
                connection.zone_a.name, connection.zone_a.color
            )
            second = self.colorize(
                connection.zone_b.name, connection.zone_b.color
            )
            limit = connection.max_link_capacity
            print(f"  {first} - {second} (capacity {limit})")
