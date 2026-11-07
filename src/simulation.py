"""Turn-by-turn simulation for the Fly-in project."""

from src.drone import Drone
from src.fly_map import FlyMap
from src.pathfinder import PathFinder
from src.zone import Zone, ZoneType

Plan = tuple[int | None, bool]


class SimulationError(Exception):
    """Raised when the simulation cannot be completed."""


class Simulation:
    """Move all the drones from the start zone to the end zone."""

    PLANS: tuple[Plan, ...] = ((None, False), (2, True), (6, True), (20, True))

    def __init__(self, fly_map: FlyMap) -> None:
        """Create the drones, all waiting in the start zone.

        Args:
            fly_map: The map to simulate.
        """
        self.fly_map: FlyMap = fly_map
        self.drones: list[Drone] = []
        self.turn: int = 0
        self.history: list[list[tuple[str, str | None]]] = []
        self.reset()

    def reset(self) -> None:
        """Put all the drones back in the start zone."""
        self.drones = [
            Drone(number, self.fly_map.start)
            for number in range(1, self.fly_map.nb_drones + 1)
        ]
        self.turn = 0
        self.history = []

    def prepare(
        self, penalty: int | None = None, spacing_aware: bool = False
    ) -> bool:
        """Give a path to every drone.

        Args:
            penalty: The extra cost of the zones already used by another
                path, or None to forbid sharing zones.
            spacing_aware: True to estimate the turns between two drones.

        Returns:
            True if a path exists, False otherwise.
        """
        finder = PathFinder(self.fly_map)
        plan = finder.plan_paths(len(self.drones), penalty, spacing_aware)
        if not plan:
            return False
        for drone in self.drones:
            drone.assign_path(plan[drone.drone_id - 1])
        return True

    def all_delivered(self) -> bool:
        """Return True when every drone has reached the end zone."""
        return all(
            drone.position is self.fly_map.end for drone in self.drones
        )

    def count_occupancy(self) -> dict[str, int]:
        """Count the drones in each zone.

        A drone in flight is counted in the zone it is flying to, so
        its place is reserved.

        Returns:
            The number of drones for each zone name.
        """
        occupancy: dict[str, int] = {}
        for drone in self.drones:
            place = drone.position
            if drone.in_transit_to is not None:
                place = drone.in_transit_to
            occupancy[place.name] = occupancy.get(place.name, 0) + 1
        return occupancy

    def can_enter(self, zone: Zone, occupancy: dict[str, int]) -> bool:
        """Tell whether a zone has room for one more drone.

        Args:
            zone: The zone a drone wants to enter.
            occupancy: Number of drones in each zone right now.

        Returns:
            True if the drone may enter.
        """
        if zone is self.fly_map.start or zone is self.fly_map.end:
            return True
        return occupancy.get(zone.name, 0) < zone.max_drones

    def link_is_free(
        self,
        source: Zone,
        target: Zone,
        link_usage: dict[frozenset[str], int],
    ) -> bool:
        """Tell whether a connection can carry one more drone this turn.

        Args:
            source: The zone the drone leaves.
            target: The zone the drone enters.
            link_usage: Drones already using each connection this turn.

        Returns:
            True if the connection exists and is not full.
        """
        connection = self.fly_map.get_connection(source, target)
        if connection is None:
            return False
        key = frozenset((source.name, target.name))
        return link_usage.get(key, 0) < connection.max_link_capacity

    def snapshot(self) -> list[tuple[str, str | None]]:
        """Return where each drone is.

        Returns:
            For each drone, its zone name and the name of the zone it
            is flying to (None if it is not in flight).
        """
        result: list[tuple[str, str | None]] = []
        for drone in self.drones:
            flying_to: str | None = None
            if drone.in_transit_to is not None:
                flying_to = drone.in_transit_to.name
            result.append((drone.position.name, flying_to))
        return result

    def step(self) -> list[str]:
        """Play one turn, respecting zone and connection capacities.

        Returns:
            The movements of the turn, such as ["D1-a", "D2-s-r"].
        """
        occupancy = self.count_occupancy()
        link_usage: dict[frozenset[str], int] = {}
        moves: list[tuple[int, str]] = []
        done: set[int] = set()
        for drone in self.drones:
            landing = drone.in_transit_to
            if landing is None:
                continue
            key = frozenset((drone.position.name, landing.name))
            link_usage[key] = link_usage.get(key, 0) + 1
            drone.advance()
            drone.in_transit_to = None
            done.add(drone.drone_id)
            moves.append((drone.drone_id, f"{drone.name}-{landing.name}"))
        ordered = sorted(
            self.drones, key=lambda d: (-d.path_index, d.drone_id)
        )
        for drone in ordered:
            if drone.drone_id in done:
                continue
            target = drone.next_zone()
            if target is None:
                continue
            source = drone.position
            if not self.can_enter(target, occupancy):
                continue
            if not self.link_is_free(source, target, link_usage):
                continue
            key = frozenset((source.name, target.name))
            link_usage[key] = link_usage.get(key, 0) + 1
            occupancy[source.name] -= 1
            occupancy[target.name] = occupancy.get(target.name, 0) + 1
            if target.zone_type == ZoneType.RESTRICTED:
                drone.in_transit_to = target
                text = f"{drone.name}-{source.name}-{target.name}"
            else:
                drone.advance()
                text = f"{drone.name}-{target.name}"
            moves.append((drone.drone_id, text))
        self.turn += 1
        moves.sort()
        return [text for _, text in moves]

    def play(
        self, penalty: int | None = None, spacing_aware: bool = False
    ) -> list[str]:
        """Play a whole simulation with one way of choosing the paths.

        Args:
            penalty: See prepare.
            spacing_aware: See prepare.

        Returns:
            One line of text per turn.

        Raises:
            SimulationError: If there is no path, or if no drone can move.
        """
        self.reset()
        if not self.prepare(penalty, spacing_aware):
            raise SimulationError("no path from start to end")
        lines: list[str] = []
        self.history = [self.snapshot()]
        while not self.all_delivered():
            moves = self.step()
            if not moves:
                raise SimulationError("deadlock: no drone can move")
            lines.append(" ".join(moves))
            self.history.append(self.snapshot())
        return lines

    def run(self) -> list[str]:
        """Try several ways of choosing the paths and keep the fastest.

        The first way is the one that never shares a zone between paths.
        In case of a tie, the earliest way is kept.

        Returns:
            One line of text per turn.

        Raises:
            SimulationError: If there is no path, or if no way works.
        """
        best: list[str] | None = None
        kept = (self.drones, self.history)
        first_error: SimulationError | None = None
        for penalty, spacing_aware in self.PLANS:
            try:
                lines = self.play(penalty, spacing_aware)
            except SimulationError as error:
                if str(error).startswith("no path"):
                    raise
                if first_error is None:
                    first_error = error
                continue
            if best is None or len(lines) < len(best):
                best = lines
                kept = (self.drones, self.history)
        if best is None:
            if first_error is not None:
                raise first_error
            raise SimulationError("no plan worked")
        self.drones, self.history = kept
        self.turn = len(best)
        return best
