from src.fly_map import FlyMap
from src.connection import Connection
from src.zone import Zone, ZoneType


class ParseError(Exception):
    """Raised when a map file cannot be parsed.

    Attributes:
        message: Error description.
        line_number: Optional line number where the parsing error occurred.
    """

    def __init__(self, message: str, line_number: int | None = None) -> None:
        """Initialize the parsing error.

        Args:
            message: Human-readable description of the parsing issue.
            line_number: Optional source line number associated with the error.
        """
        if line_number is not None:
            message = f"line {line_number}: {message}"
        super().__init__(message)
        self.line_number: int | None = line_number


class MapParser:
    """Parse map descriptions from text files.

    Attributes:
        file_name: Name of the file being parsed.
    """

    def __init__(self, file_name: str) -> None:
        """Initialize the parser for a given file.

        Args:
            file_name: Path or name of the map file to parse.
        """
        self.file_name: str = file_name
        self.nb_drones: int = 0
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.link_keys: set[frozenset[str]] = set()
        self.start: Zone | None = None
        self.end: Zone | None = None

    def split_metadata(
            self, text: str, line_number: int
    ) -> tuple[str, dict[str, str]]:
        """Split a line into its main content and metadata dictionary.

        Args:
            text: Raw text to parse.
            line_number: Source line number for error reporting.

        Returns:
            A tuple containing the cleaned main content and a mapping of
            metadata keys to values.

        Raises:
            ParseError: If the metadata block is malformed or contains invalid
                tokens.
        """
        if "[" not in text:
            if "]" in text:
                raise ParseError("unexpected ']'", line_number)
            return text.strip(), {}
        main, _, rest = text.partition("[")
        rest = rest.strip()
        if not rest.endswith("]"):
            raise ParseError("metadata must end with ']'", line_number)
        inner = rest[:-1]
        if "[" in inner or "]" in inner:
            raise ParseError("too many brackets in metadata", line_number)
        metadata: dict[str, str] = {}
        for token in inner.split():
            key, separator, value = token.partition("=")
            if not separator or not key or not value:
                raise ParseError(
                    f"invalid metadata '{token}' (expected key=value)",
                    line_number,
                )
            if key in metadata:
                raise ParseError(
                    f"duplicate metadata key '{key}'", line_number
                )
            metadata[key] = value
        return main.strip(), metadata

    def to_int(self, value: str, label: str, line_number: int) -> int:
        """Convert a text to an integer.

        Args:
            value: The text to convert, such as "12".
            label: Name of the value, used in the error message.
            line_number: Line number, used in error messages.

        Returns:
            The integer value.

        Raises:
            ParseError: If the text is not a valid integer.
        """
        try:
            return int(value)
        except ValueError:
            raise ParseError(
                f"{label} must be an integer, got '{value}'", line_number
            ) from None

    def to_positive_int(
        self, value: str, label: str, line_number: int
    ) -> int:
        """Convert a text to an integer greater than zero.

        Args:
            value: The text to convert, such as "2".
            label: Name of the value, used in the error message.
            line_number: Line number, used in error messages.

        Returns:
            The positive integer value.

        Raises:
            ParseError: If the text is not an integer or is not positive.
        """
        number = self.to_int(value, label, line_number)
        if number <= 0:
            raise ParseError(
                f"{label} must be positive, got {number}", line_number
            )
        return number

    def parse_zone(self, text: str, line_number: int) -> Zone:
        """Build a Zone from a line such as "roof1 3 4 [zone=restricted]".

        Args:
            text: The line, without its "hub:" prefix.
            line_number: Line number, used in error messages.

        Returns:
            The zone described by the line.

        Raises:
            ParseError: If the name, coordinates or metadata are invalid.
        """
        main, metadata = self.split_metadata(text, line_number)
        parts = main.split()
        if len(parts) != 3:
            raise ParseError(
                "a zone needs a name, x and y (example: roof1 3 4)",
                line_number,
            )
        name = parts[0]
        if "-" in name:
            raise ParseError(
                f"zone name '{name}' must not contain '-'", line_number
            )
        x = self.to_int(parts[1], "x", line_number)
        y = self.to_int(parts[2], "y", line_number)
        zone_type = ZoneType.NORMAL
        color: str | None = None
        max_drones = 1
        for key, value in metadata.items():
            if key == "zone":
                try:
                    zone_type = ZoneType(value)
                except ValueError:
                    raise ParseError(
                        f"unknown zone type '{value}'", line_number
                    ) from None
            elif key == "color":
                color = value
            elif key == "max_drones":
                max_drones = self.to_positive_int(value, key, line_number)
            else:
                raise ParseError(
                    f"unknown zone metadata '{key}'", line_number
                )
        return Zone(name, x, y, zone_type, color, max_drones)

    def parse_connection(
        self, text: str, line_number: int, zones: dict[str, Zone]
    ) -> Connection:
        """Build a Connection from a line such as "hub-roof1 [...]".

        Args:
            text: The line, without its "connection:" prefix.
            line_number: Line number, used in error messages.
            zones: The zones already read, indexed by name.

        Returns:
            The connection described by the line.

        Raises:
            ParseError: If the format, a zone name or the metadata is
                invalid.
        """
        main, metadata = self.split_metadata(text, line_number)
        names = main.split("-")
        if len(main.split()) != 1 or len(names) != 2:
            raise ParseError(
                "a connection must look like zone1-zone2 (no spaces)",
                line_number,
            )
        for name in names:
            if name not in zones:
                raise ParseError(f"unknown zone '{name}'", line_number)
        capacity = 1
        for key, value in metadata.items():
            if key == "max_link_capacity":
                capacity = self.to_positive_int(value, key, line_number)
            else:
                raise ParseError(
                    f"unknown connection metadata '{key}'", line_number
                )
        return Connection(zones[names[0]], zones[names[1]], capacity)

    def add_zone(self, prefix: str, text: str, line_number: int) -> None:
        """Read a zone line and store the zone.

        Args:
            prefix: "start_hub", "end_hub" or "hub".
            text: The line, without its prefix.
            line_number: Line number, used in error messages.

        Raises:
            ParseError: If the zone is invalid or already defined.
        """
        zone = self.parse_zone(text, line_number)
        if zone.name in self.zones:
            raise ParseError(
                f"zone '{zone.name}' is already defined", line_number
            )
        if prefix == "start_hub":
            if self.start is not None:
                raise ParseError("only one start_hub is allowed", line_number)
            self.start = zone
        elif prefix == "end_hub":
            if self.end is not None:
                raise ParseError("only one end_hub is allowed", line_number)
            self.end = zone
        self.zones[zone.name] = zone

    def add_connection(self, text: str, line_number: int) -> None:
        """Read a connection line and store the connection.

        Args:
            text: The line, without its "connection:" prefix.
            line_number: Line number, used in error messages.

        Raises:
            ParseError: If the connection is invalid or already defined.
        """
        link = self.parse_connection(text, line_number, self.zones)
        key = frozenset((link.zone_a.name, link.zone_b.name))
        if key in self.link_keys:
            raise ParseError(
                "connection already defined (a-b and b-a are the same)",
                line_number,
            )
        self.link_keys.add(key)
        self.connections.append(link)

    def parse_line(self, line: str, line_number: int) -> None:
        """Read one meaningful line of the file.

        Args:
            line: The line, already stripped, not empty, not a comment.
            line_number: Line number, used in error messages.

        Raises:
            ParseError: If the line is invalid.
        """
        prefix, separator, rest = line.partition(":")
        prefix = prefix.strip()
        rest = rest.strip()
        if not separator:
            raise ParseError("expected '<keyword>: <value>'", line_number)
        if prefix != "nb_drones" and self.nb_drones == 0:
            raise ParseError(
                "the first line must define nb_drones", line_number
            )
        if prefix == "nb_drones":
            if self.nb_drones != 0:
                raise ParseError("nb_drones is defined twice", line_number)
            self.nb_drones = self.to_positive_int(
                rest, "nb_drones", line_number
            )
        elif prefix in ("start_hub", "end_hub", "hub"):
            self.add_zone(prefix, rest, line_number)
        elif prefix == "connection":
            self.add_connection(rest, line_number)
        else:
            raise ParseError(f"unknown keyword '{prefix}'", line_number)

    def parse(self) -> FlyMap:
        """Read the whole map file and fill the parser attributes.

        Raises:
            ParseError: If the file cannot be read or contains an error.
        """
        try:
            with open(self.file_name, encoding="utf-8") as file:
                lines = file.read().splitlines()
        except (OSError, UnicodeDecodeError) as error:
            raise ParseError(f"cannot read the file: {error}") from None
        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            self.parse_line(line, line_number)
        if self.nb_drones == 0:
            raise ParseError("nb_drones is missing")
        if self.start is None:
            raise ParseError("start_hub is missing")
        if self.end is None:
            raise ParseError("end_hub is missing")
        return FlyMap(
            self.nb_drones, self.start, self.end, self.zones, self.connections
        )
