"""Graphical display (pygame) for the Fly-in project."""

import math

import pygame

from src.fly_map import FlyMap
from src.zone import Zone, ZoneType

Color = tuple[int, int, int]
Point = tuple[float, float]
Snapshot = list[tuple[str, str | None]]


class GraphicRenderer:
    """Draw the map in a window, like a beehive."""

    WIDTH: int = 1920
    HEIGHT: int = 1080
    MARGIN: int = 90
    RADIUS: int = 30
    BACKGROUND: Color = (45, 30, 15)
    HONEY: Color = (240, 180, 40)
    COLORS: dict[str, Color] = {
        "red": (220, 60, 60),
        "green": (80, 190, 90),
        "blue": (70, 130, 220),
        "yellow": (245, 220, 70),
        "gray": (130, 130, 130),
        "grey": (130, 130, 130),
        "orange": (240, 140, 40),
        "purple": (150, 90, 200),
        "pink": (240, 130, 190),
        "brown": (140, 90, 50),
        "black": (30, 30, 30),
        "white": (240, 240, 240),
        "cyan": (70, 200, 210),
        "magenta": (210, 70, 190),
    }
    BORDERS: dict[ZoneType, Color] = {
        ZoneType.NORMAL: (90, 60, 20),
        ZoneType.PRIORITY: (255, 215, 0),
        ZoneType.RESTRICTED: (200, 30, 30),
        ZoneType.BLOCKED: (0, 0, 0),
    }

    def __init__(self, fly_map: FlyMap) -> None:
        """Compute the scale that fits the map in the window.

        Args:
            fly_map: The map to draw.
        """
        self.fly_map: FlyMap = fly_map
        xs = [zone.x for zone in fly_map.zones.values()]
        ys = [zone.y for zone in fly_map.zones.values()]
        self.min_x: int = min(xs)
        self.min_y: int = min(ys)
        span_x = max(max(xs) - self.min_x, 1)
        span_y = max(max(ys) - self.min_y, 1)
        width = self.WIDTH - 2 * self.MARGIN
        height = self.HEIGHT - 2 * self.MARGIN
        self.scale: float = min(width / span_x, height / span_y)
        self.offset_x: float = (self.WIDTH - span_x * self.scale) / 2
        self.offset_y: float = (self.HEIGHT - span_y * self.scale) / 2

    def to_screen(self, zone: Zone) -> tuple[int, int]:
        """Convert the map coordinates of a zone into pixels.

        Args:
            zone: The zone to place.

        Returns:
            The (x, y) position of the zone center, in pixels.
        """
        pixel_x = self.offset_x + (zone.x - self.min_x) * self.scale
        pixel_y = self.offset_y + (zone.y - self.min_y) * self.scale
        return int(pixel_x), int(pixel_y)

    def hexagon(self, center: tuple[int, int]) -> list[tuple[float, float]]:
        """Return the six corners of a hexagon.

        Args:
            center: The center of the hexagon, in pixels.

        Returns:
            The corners, as (x, y) pairs.
        """
        points: list[tuple[float, float]] = []
        for index in range(6):
            angle = math.radians(60 * index + 30)
            points.append((
                center[0] + self.RADIUS * math.cos(angle),
                center[1] + self.RADIUS * math.sin(angle),
            ))
        return points

    def zone_color(self, zone: Zone) -> Color:
        """Return the fill color of a zone (honey if unknown)."""
        return self.COLORS.get((zone.color or "").lower(), self.HONEY)

    def draw_map(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the background, the connections and the zones.

        Args:
            screen: The window surface.
            font: The font used for the zone names.
        """
        screen.fill(self.BACKGROUND)
        for connection in self.fly_map.connections:
            thickness = min(2 + 2 * connection.max_link_capacity, 12)
            pygame.draw.line(
                screen,
                (200, 160, 80),
                self.to_screen(connection.zone_a),
                self.to_screen(connection.zone_b),
                thickness,
            )
        for zone in self.fly_map.zones.values():
            center = self.to_screen(zone)
            points = self.hexagon(center)
            pygame.draw.polygon(screen, self.zone_color(zone), points)
            pygame.draw.polygon(
                screen, self.BORDERS[zone.zone_type], points, 4
            )
            label = font.render(zone.name, True, (255, 255, 255))
            position = (center[0], center[1] + self.RADIUS + 14)
            screen.blit(label, label.get_rect(center=position))

    def run(self) -> None:
        """Open the window and draw until it is closed (or Escape)."""
        pygame.init()
        try:
            screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
            pygame.display.set_caption("Fly-in")
            font = pygame.font.Font(None, 22)
            clock = pygame.time.Clock()
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif (event.type == pygame.KEYDOWN
                          and event.key == pygame.K_ESCAPE):
                        running = False
                self.draw_map(screen, font)
                pygame.display.flip()
                clock.tick(30)
        finally:
            pygame.quit()

    def positions(self, snapshot: Snapshot) -> list[Point | None]:
        """Compute where each drone is drawn, in pixels.

        Args:
            snapshot: For each drone, its zone and the zone it flies to.

        Returns:
            One point per drone, or None for a delivered drone.
        """
        counters: dict[str, int] = {}
        points: list[Point | None] = []
        for place, flying_to in snapshot:
            zone = self.fly_map.zones[place]
            if zone is self.fly_map.end:
                points.append(None)
                continue
            center = self.to_screen(zone)
            if flying_to is not None:
                other = self.to_screen(self.fly_map.zones[flying_to])
                points.append((
                    (center[0] + other[0]) / 2,
                    (center[1] + other[1]) / 2,
                ))
                continue
            rank = counters.get(place, 0)
            counters[place] = rank + 1
            radius = 4.5 * math.sqrt(rank)
            angle = rank * 2.4
            points.append((
                center[0] + radius * math.cos(angle),
                center[1] + radius * math.sin(angle),
            ))
        return points

    def draw_drone(self, screen: pygame.Surface, point: Point) -> None:
        """Draw one small bee.

        Args:
            screen: The window surface.
            point: The center of the bee, in pixels.
        """
        x, y = int(point[0]), int(point[1])
        wings = (230, 240, 255)
        pygame.draw.circle(screen, wings, (x - 5, y - 8), 5)
        pygame.draw.circle(screen, wings, (x + 5, y - 8), 5)
        pygame.draw.circle(screen, (20, 20, 20), (x, y), 10)
        pygame.draw.circle(screen, (255, 210, 40), (x, y), 8)
        pygame.draw.line(screen, (20, 20, 20), (x - 6, y), (x + 6, y), 2)

    def draw_drones(
        self,
        screen: pygame.Surface,
        history: list[Snapshot],
        index: int,
        progress: float,
    ) -> None:
        """Draw the bees between turn `index` and the next one.

        Args:
            screen: The window surface.
            history: The positions of the drones after each turn.
            index: The turn being shown.
            progress: How far the animation is toward the next turn (0-1).
        """
        current = self.positions(history[index])
        following = self.positions(history[min(index + 1, len(history) - 1)])
        end_center = self.to_screen(self.fly_map.end)
        ease = progress * progress * (3 - 2 * progress)
        for before, after in zip(current, following):
            if before is None:
                continue
            goal = after
            if goal is None:
                goal = (float(end_center[0]), float(end_center[1]))
            x = before[0] + (goal[0] - before[0]) * ease
            y = before[1] + (goal[1] - before[1]) * ease
            self.draw_drone(screen, (x, y))

    def draw_status(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        history: list[Snapshot],
        index: int,
    ) -> None:
        """Write the turn number and the delivered drones.

        Args:
            screen: The window surface.
            font: The font used for the text.
            history: The positions of the drones after each turn.
            index: The turn being shown.
        """
        end_name = self.fly_map.end.name
        delivered = sum(1 for place, _ in history[index] if place == end_name)
        text = (
            f"Turn {index}/{len(history) - 1}   "
            f"Delivered {delivered}/{len(history[index])}   "
            f"SPACE: pause   RIGHT: next turn   ESC: quit"
        )
        screen.blit(font.render(text, True, (255, 255, 255)), (15, 12))

    def play(
        self, history: list[Snapshot], seconds_per_turn: float = 0.8
    ) -> None:
        """Open the window and replay the simulation.

        Args:
            history: The positions of the drones after each turn.
            seconds_per_turn: The duration of one turn on screen.
        """
        pygame.init()
        try:
            screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
            pygame.display.set_caption("Fly-in")
            font = pygame.font.Font(None, 22)
            title_font = pygame.font.Font(None, 28)
            clock = pygame.time.Clock()
            last = len(history) - 1
            index = 0
            progress = 0.0
            playing = True
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key == pygame.K_SPACE:
                            playing = not playing
                        elif event.key == pygame.K_RIGHT and index < last:
                            index += 1
                            progress = 0.0
                seconds = clock.tick(60) / 1000
                if playing and index < last:
                    progress += seconds / seconds_per_turn
                    if progress >= 1.0:
                        index += 1
                        progress = 0.0
                self.draw_map(screen, font)
                self.draw_drones(screen, history, index, progress)
                self.draw_status(screen, title_font, history, index)
                pygame.display.flip()
        finally:
            pygame.quit()
