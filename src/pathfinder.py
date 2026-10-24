"""Pathfinding for the Fly-in project."""

import heapq
from collections import deque

from src.fly_map import FlyMap
from src.zone import Zone, ZoneType


class PathFinder:
    """Find paths from the start zone to the end zone."""

    def __init__(self, fly_map: FlyMap) -> None:
        """Store the map to search in.

        Args:
            fly_map: The map containing zones and connections.
        """
        self.fly_map: FlyMap = fly_map
        self.banned: set[str] = set()

    def find_path(self) -> list[Zone] | None:
        """Find the path with the fewest steps from start to end.

        Blocked zones are never used.

        Returns:
            The zones from start to end, or None if no path exists.
        """
        start = self.fly_map.start
        end = self.fly_map.end
        queue: deque[Zone] = deque([start])
        came_from: dict[str, Zone | None] = {start.name: None}
        while queue:
            current = queue.popleft()
            if current is end:
                return self.rebuild_path(came_from, end)
            for neighbor in self.fly_map.neighbors(current):
                if neighbor.is_blocked() or neighbor.name in self.banned:
                    continue
                if neighbor.name in came_from:
                    continue
                came_from[neighbor.name] = current
                queue.append(neighbor)
        return None

    def rebuild_path(
        self, came_from: dict[str, Zone | None], end: Zone
    ) -> list[Zone]:
        """Walk back from the end zone to the start zone.

        Args:
            came_from: For each zone name, the zone we came from.
            end: The zone where the search finished.

        Returns:
            The zones in order, from start to end.
        """
        path: list[Zone] = []
        current: Zone | None = end
        while current is not None:
            path.append(current)
            current = came_from[current.name]
        path.reverse()
        return path

    def find_cheapest_path(self) -> list[Zone] | None:
        """Find the path with the fewest turns from start to end.

        Entering a restricted zone costs 2 turns, the others cost 1.
        Blocked zones are never used. When two paths take the same
        number of turns, the one with more priority zones is preferred.

        Returns:
            The zones from start to end, or None if no path exists.
        """
        start = self.fly_map.start
        end = self.fly_map.end
        best: dict[str, tuple[int, int]] = {start.name: (0, 0)}
        came_from: dict[str, Zone | None] = {start.name: None}
        heap: list[tuple[int, int, str]] = [(0, 0, start.name)]
        while heap:
            turns, score, name = heapq.heappop(heap)
            if (turns, score) > best[name]:
                continue
            current = self.fly_map.zones[name]
            if current is end:
                return self.rebuild_path(came_from, end)
            for neighbor in self.fly_map.neighbors(current):
                if neighbor.is_blocked() or neighbor.name in self.banned:
                    continue
                new_turns = turns + neighbor.cost()
                new_score = score
                if neighbor.zone_type == ZoneType.PRIORITY:
                    new_score -= 1
                new_cost = (new_turns, new_score)
                if neighbor.name in best and best[neighbor.name] <= new_cost:
                    continue
                best[neighbor.name] = new_cost
                came_from[neighbor.name] = current
                heapq.heappush(heap, (new_turns, new_score, neighbor.name))
        return None

    def path_cost(self, path: list[Zone]) -> int:
        """Return the number of turns a drone needs to follow a path.

        Args:
            path: The zones of the path, from start to end.

        Returns:
            The sum of the costs of the zones entered.
        """
        return sum(zone.cost() for zone in path[1:])

    def find_paths(self, max_paths: int) -> list[list[Zone]]:
        """Find paths that share no intermediate zone.

        The cheapest path is found first, then its zones are banned
        and the next cheapest path is searched, and so on.

        Args:
            max_paths: The maximum number of paths to return.

        Returns:
            The paths, from the cheapest to the costliest.
        """
        paths: list[list[Zone]] = []
        self.banned = set()
        while len(paths) < max_paths:
            path = self.find_cheapest_path()
            if path is None:
                break
            paths.append(path)
            if len(path) <= 2:
                break
            for zone in path[1:-1]:
                self.banned.add(zone.name)
        self.banned = set()
        return paths

    def plan_paths(self, nb_drones: int) -> list[list[Zone]]:
        """Choose a path for each drone.

        Each drone takes the path where it is expected to arrive first,
        counting the drones already sent on that path.

        Args:
            nb_drones: The number of drones to route.

        Returns:
            One path per drone (drone n uses item n - 1), or an empty
            list if there is no path.
        """
        paths = self.find_paths(nb_drones)
        if not paths:
            return []
        costs = [self.path_cost(path) for path in paths]
        sent = [0] * len(paths)
        plan: list[list[Zone]] = []
        for _ in range(nb_drones):
            best = min(range(len(paths)), key=lambda i: costs[i] + sent[i])
            sent[best] += 1
            plan.append(paths[best])
        return plan
