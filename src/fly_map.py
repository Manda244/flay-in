"""Graph of zones and connections for the Fly-in project."""

from src.connection import Connection
from src.zone import Zone


class FlyMap:
    """The whole map: zones, connections and who is next to whom."""

    def __init__(
        self,
        nb_drones: int,
        start: Zone,
        end: Zone,
        zones: dict[str, Zone],
        connections: list[Connection],
    ) -> None:
        """Store the map and build the adjacency lists.

        Args:
            nb_drones: Number of drones to route.
            start: The start zone.
            end: The end zone.
            zones: All zones, indexed by name.
            connections: All connections of the map.
        """
        self.nb_drones: int = nb_drones
        self.start: Zone = start
        self.end: Zone = end
        self.zones: dict[str, Zone] = zones
        self.connections: list[Connection] = connections
        self.adjacency: dict[str, list[Connection]] = {
            name: [] for name in zones
        }
        for connection in connections:
            self.adjacency[connection.zone_a.name].append(connection)
            self.adjacency[connection.zone_b.name].append(connection)

    def connections_of(self, zone: Zone) -> list[Connection]:
        """Return the connections that touch a zone.

        Args:
            zone: The zone to look at.

        Returns:
            The list of connections of this zone.
        """
        return self.adjacency[zone.name]

    def neighbors(self, zone: Zone) -> list[Zone]:
        """Return the zones directly connected to a zone.

        Args:
            zone: The zone to look at.

        Returns:
            The neighbor zones (blocked zones included).
        """
        return [
            connection.other_end(zone)
            for connection in self.adjacency[zone.name]
        ]

    def get_connection(
        self, zone_a: Zone, zone_b: Zone
    ) -> Connection | None:
        """Return the connection between two zones, if there is one.

        Args:
            zone_a: First zone.
            zone_b: Second zone.

        Returns:
            The connection linking the two zones, or None.
        """
        for connection in self.adjacency[zone_a.name]:
            if connection.other_end(zone_a) is zone_b:
                return connection
        return None
