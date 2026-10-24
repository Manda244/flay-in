"""Independent checker of simulation outputs."""

from src.connection import Connection
from src.fly_map import FlyMap
from src.zone import Zone, ZoneType


class ValidationError(Exception):
    """Raised when an output breaks a rule of the subject."""


class OutputValidator:
    """Replay an output turn by turn and check the rules."""

    def __init__(self, fly_map: FlyMap) -> None:
        """Store the map used to check the output.

        Args:
            fly_map: The map the output was produced for.
        """
        self.fly_map: FlyMap = fly_map

    def zone(self, name: str, turn: int) -> Zone:
        """Return a zone by name, or raise if it does not exist."""
        found = self.fly_map.zones.get(name)
        if found is None:
            raise ValidationError(f"turn {turn}: unknown zone '{name}'")
        return found

    def find_link(self, turn: int, first: str, second: str) -> Connection:
        """Return the connection between two zones, or raise."""
        connection = self.fly_map.get_connection(
            self.zone(first, turn), self.zone(second, turn)
        )
        if connection is None:
            raise ValidationError(
                f"turn {turn}: no connection between {first} and {second}"
            )
        return connection

    def use_link(
        self, first: str, second: str, link_usage: dict[frozenset[str], int]
    ) -> None:
        """Count one more drone on a connection for this turn."""
        key = frozenset((first, second))
        link_usage[key] = link_usage.get(key, 0) + 1

    def validate(self, lines: list[str]) -> int:
        """Check a whole output.

        Args:
            lines: One line per turn, as printed by the program.

        Returns:
            The number of turns.

        Raises:
            ValidationError: If a rule of the subject is broken.
        """
        start = self.fly_map.start.name
        place: dict[str, str] = {
            f"D{number}": start
            for number in range(1, self.fly_map.nb_drones + 1)
        }
        flying: dict[str, str] = {}
        for turn, line in enumerate(lines, start=1):
            self.check_turn(turn, line, place, flying)
        end = self.fly_map.end.name
        late = [d for d, zone in place.items() if zone != end or d in flying]
        if late:
            raise ValidationError(f"{len(late)} drones not delivered")
        return len(lines)

    def check_turn(
        self,
        turn: int,
        line: str,
        place: dict[str, str],
        flying: dict[str, str],
    ) -> None:
        """Replay one turn and check its rules."""
        link_usage: dict[frozenset[str], int] = {}
        was_flying = set(flying)
        moved: set[str] = set()
        for token in line.split():
            parts = token.split("-")
            drone = parts[0]
            if drone not in place:
                raise ValidationError(f"turn {turn}: unknown drone '{drone}'")
            if drone in moved:
                raise ValidationError(f"turn {turn}: {drone} moves twice")
            moved.add(drone)
            if len(parts) == 2:
                self.move(turn, drone, parts[1], place, flying, link_usage)
            elif len(parts) == 3:
                self.take_off(
                    turn, drone, (parts[1], parts[2]), place, flying,
                    link_usage,
                )
            else:
                raise ValidationError(f"turn {turn}: bad movement '{token}'")
        for drone in sorted(was_flying):
            if drone in flying:
                raise ValidationError(
                    f"turn {turn}: {drone} must land in {flying[drone]}"
                )
        self.check_capacities(turn, place, flying, link_usage)

    def move(
        self,
        turn: int,
        drone: str,
        target_name: str,
        place: dict[str, str],
        flying: dict[str, str],
        link_usage: dict[frozenset[str], int],
    ) -> None:
        """Check a move to a zone (a normal move or a landing)."""
        source_name = place[drone]
        target = self.zone(target_name, turn)
        if drone in flying:
            if flying[drone] != target_name:
                raise ValidationError(
                    f"turn {turn}: {drone} must land in {flying[drone]}"
                )
            del flying[drone]
        else:
            if source_name == self.fly_map.end.name:
                raise ValidationError(
                    f"turn {turn}: {drone} is already delivered"
                )
            self.find_link(turn, source_name, target_name)
            if target.is_blocked():
                raise ValidationError(f"turn {turn}: {target_name} is blocked")
            if target.zone_type == ZoneType.RESTRICTED:
                raise ValidationError(
                    f"turn {turn}: {target_name} is restricted, "
                    f"the drone must fly there"
                )
        self.use_link(source_name, target_name, link_usage)
        place[drone] = target_name

    def take_off(
        self,
        turn: int,
        drone: str,
        route: tuple[str, str],
        place: dict[str, str],
        flying: dict[str, str],
        link_usage: dict[frozenset[str], int],
    ) -> None:
        """Check a take-off toward a restricted zone."""
        source_name, target_name = route
        if drone in flying:
            raise ValidationError(f"turn {turn}: {drone} must land first")
        if place[drone] != source_name:
            raise ValidationError(
                f"turn {turn}: {drone} is not in {source_name}"
            )
        self.find_link(turn, source_name, target_name)
        if self.zone(target_name, turn).zone_type != ZoneType.RESTRICTED:
            raise ValidationError(
                f"turn {turn}: {target_name} is not a restricted zone"
            )
        flying[drone] = target_name
        self.use_link(source_name, target_name, link_usage)

    def check_capacities(
        self,
        turn: int,
        place: dict[str, str],
        flying: dict[str, str],
        link_usage: dict[frozenset[str], int],
    ) -> None:
        """Check zone and connection capacities at the end of a turn."""
        counts: dict[str, int] = {}
        for drone, name in place.items():
            if drone not in flying:
                counts[name] = counts.get(name, 0) + 1
        for name, count in counts.items():
            zone = self.zone(name, turn)
            if zone is self.fly_map.start or zone is self.fly_map.end:
                continue
            if count > zone.max_drones:
                raise ValidationError(
                    f"turn {turn}: zone '{name}' holds {count} drones "
                    f"(max {zone.max_drones})"
                )
        for key, used in link_usage.items():
            ordered = sorted(key)
            first, second = ordered[0], ordered[-1]
            connection = self.find_link(turn, first, second)
            if used > connection.max_link_capacity:
                raise ValidationError(
                    f"turn {turn}: connection {first}-{second} used by "
                    f"{used} drones (max {connection.max_link_capacity})"
                )
