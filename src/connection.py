from src.zone import Zone


class Connection:
    """Represent a link between two zones.

    Attributes:
        zone_a: First zone connected by the link.
        zone_b: Second zone connected by the link.
        max_link_capacity: Maximum number of links or traffic units allowed.
    """

    def __init__(self, zone_a: Zone, zone_b: Zone,
                 max_link_capacity: int = 1) -> None:
        """Initialize a connection between two zones.

        Args:
            zone_a: The first zone in the connection.
            zone_b: The second zone in the connection.
            max_link_capacity: Maximum number of drones allowed
                to use the link at once.
        """
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity

    def other_end(self, zone: Zone) -> Zone:
        """Return the opposite end of the connection for the given zone.

        Args:
            zone: One of the two zones in the connection.

        Returns:
            The other zone in the connection.

        Raises:
            ValueError: If the provided zone is not part of this connection.
        """
        if zone == self.zone_a:
            return self.zone_b
        if zone == self.zone_b:
            return self.zone_a
        raise ValueError("Zone not part of this connection.")

    def __repr__(self) -> str:
        """Return a readable representation of the connection."""
        return f"Connection(zone_a={self.zone_a}, zone_b={self.zone_b}, " \
               f"max_link_capacity={self.max_link_capacity})"
