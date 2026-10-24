"""Drone class for the Fly-in project."""

from src.zone import Zone


class Drone:
    """A drone that travels from the start zone to the end zone."""

    def __init__(self, drone_id: int, start: Zone) -> None:
        """Create a drone waiting in the start zone.

        Args:
            drone_id: Number of the drone (1 gives the name "D1").
            start: The start zone, where every drone begins.
        """
        self.drone_id: int = drone_id
        self.name: str = f"D{drone_id}"
        self.position: Zone = start
        self.path: list[Zone] = []
        self.path_index: int = 0
        self.in_transit_to: Zone | None = None

    def assign_path(self, path: list[Zone]) -> None:
        """Give the drone a path to follow, starting from its position.

        Args:
            path: The zones to visit, from start to end.
        """
        self.path = path
        self.path_index = 0

    def next_zone(self) -> Zone | None:
        """Return the next zone of the path.

        Returns:
            The next zone, or None if the path is finished.
        """
        if self.path_index + 1 < len(self.path):
            return self.path[self.path_index + 1]
        return None

    def advance(self) -> None:
        """Move the drone to the next zone of its path.

        Raises:
            ValueError: If the drone has no next zone.
        """
        next_zone = self.next_zone()
        if next_zone is None:
            raise ValueError(f"{self.name} has no next zone")
        self.path_index += 1
        self.position = next_zone

    def __repr__(self) -> str:
        """Return a readable representation of the drone."""
        return f"Drone({self.name}, at {self.position.name})"
