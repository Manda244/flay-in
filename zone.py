from enum import Enum


class ZoneType(Enum):
    """Supported zone states used to describe a zone's behavior."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    """Represent a zone on the map.

    Attributes:
        name: Display name of the zone.
        x: X coordinate of the zone.
        y: Y coordinate of the zone.
        zone_type: Type of the zone.
        color: Optional display color.
        max_drones: Maximum number of drones allowed in the zone.
    """

    def __init__(self, name: str, x: int, y: int,
                 zone_type: ZoneType = ZoneType.NORMAL,
                 color: str | None = None,
                 max_drones: int = 1) -> None:
        """Initialize a zone.

        Args:
            name: Name of the zone.
            x: X coordinate.
            y: Y coordinate.
            zone_type: Zone behavior type.
            color: Optional color used to render the zone.
            max_drones: Maximum number of drones allowed in the zone.
        """
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones

    def is_blocked(self) -> bool:
        """Return whether the zone is blocked."""
        return self.zone_type == ZoneType.BLOCKED

    def __repr__(self) -> str:
        """Return a readable representation of the zone."""
        return f"Zone(name={self.name}, x={self.x}, y={self.y}, " \
            f"zone_type={self.zone_type}, color={self.color}, " \
            f"max_drones={self.max_drones})"

    def cost(self) -> int:
        """Return the number of turns needed to enter this zone.

        Returns:
            2 for a restricted zone, 1 for the other enterable zones.

        Raises:
            ValueError: If the zone is blocked (nobody can enter it).
        """
        if self.zone_type == ZoneType.BLOCKED:
            raise ValueError(f"zone '{self.name}' is blocked")
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        return 1
