"""Colored terminal display for the Fly-in project."""

from fly_map import FlyMap


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
