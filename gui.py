"""Graphical display (pygame) for the Fly-in project.

The file has two classes:
- Replay: which turn is shown and how the animation moves;
- GraphicRenderer: draws everything and reads the keyboard.
"""

import math
from pathlib import Path

import pygame

from fly_map import FlyMap
from zone import Zone, ZoneType

Color = tuple[int, int, int]
Point = tuple[float, float]
Snapshot = list[tuple[str, str | None]]
Fonts = tuple[pygame.font.Font, pygame.font.Font]


class Replay:
    """Remember which turn is shown and how the animation moves."""

    def __init__(
        self, history: list[Snapshot], seconds_per_turn: float = 0.8
    ) -> None:
        """Start the replay at turn 0.

        Args:
            history: The positions of the drones after each turn.
            seconds_per_turn: The duration of one turn on screen.
        """
        self.history: list[Snapshot] = history
        self.seconds_per_turn: float = seconds_per_turn
        self.index: int = 0
        self.progress: float = 0.0
        self.moving: bool = False
        self.auto: bool = False

    def step(self) -> None:
        """Start the move to the next turn (key SPACE)."""
        if self.index < len(self.history) - 1:
            self.moving = True

    def toggle_auto(self) -> None:
        """Start or stop the automatic replay (key A)."""
        self.auto = not self.auto
        self.moving = self.moving or self.progress > 0

    def restart(self) -> None:
        """Go back to turn 0 (key R)."""
        self.index = 0
        self.progress = 0.0
        self.moving = False
        self.auto = False

    def update(self, seconds: float) -> None:
        """Advance the animation.

        Args:
            seconds: The time since the last image.
        """
        last = len(self.history) - 1
        if not (self.moving or self.auto) or self.index >= last:
            return
        self.progress += seconds / self.seconds_per_turn
        if self.progress >= 1.0:
            self.index += 1
            self.progress = 0.0
            self.moving = False
            if self.index >= last:
                self.auto = False


class GraphicRenderer:
    """Draw the map in a resizable window."""

    WIDTH: int = 1000
    HEIGHT: int = 700
    MARGIN: int = 90
    RADIUS: int = 30
    DRONE_WIDTH: int = 46
    MAX_ZOOM: float = 8.0
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
        """Prepare the window state and the view of a map.

        Args:
            fly_map: The map to draw.
        """
        self.fly_map: FlyMap = fly_map
        self.width: int = self.WIDTH
        self.height: int = self.HEIGHT
        self.title: str = ""
        self.drone_source: pygame.Surface | None = None
        self.font_cache: dict[int, pygame.font.Font] = {}
        self.running: bool = True
        self.set_map(fly_map)

    # ----- the view: where each zone is on the screen -----

    def set_map(self, fly_map: FlyMap) -> None:
        """Prepare the view of a map (also used to change the map).

        Args:
            fly_map: The map to draw.
        """
        self.fly_map = fly_map
        xs = [zone.x for zone in fly_map.zones.values()]
        ys = [zone.y for zone in fly_map.zones.values()]
        self.center_x: float = (min(xs) + max(xs)) / 2
        self.center_y: float = (min(ys) + max(ys)) / 2
        self.span_x: int = max(max(xs) - min(xs), 1)
        self.span_y: int = max(max(ys) - min(ys), 1)
        points = [(zone.x, zone.y) for zone in fly_map.zones.values()]
        self.min_gap: float = min(
            (
                math.dist(first, second)
                for index, first in enumerate(points)
                for second in points[index + 1:]
                if first != second
            ),
            default=2.0,
        )
        self.zoom: float = 1.0
        self.pan_x: float = 0.0
        self.pan_y: float = 0.0

    def scale(self) -> float:
        """Return the number of pixels for one unit of the map."""
        room_x = max(self.width - 2 * self.MARGIN, 1)
        room_y = max(self.height - 2 * self.MARGIN, 1)
        fit = min(room_x / self.span_x, room_y / self.span_y)
        return fit * self.zoom

    def radius(self) -> int:
        """Return the radius of a hexagon, in pixels.

        It grows with the window and the zoom, but never so much that two
        zones touch each other.
        """
        window = min(self.width / self.WIDTH, self.height / self.HEIGHT)
        wanted = self.RADIUS * window * self.zoom
        room = 0.36 * self.min_gap * self.scale()
        return max(int(min(wanted, room)), 3)

    def size_factor(self) -> float:
        """Return how big the drawings are compared to the normal size."""
        return self.radius() / self.RADIUS

    def to_screen(self, zone: Zone) -> tuple[int, int]:
        """Convert the map coordinates of a zone into pixels.

        Args:
            zone: The zone to place.

        Returns:
            The (x, y) position of the zone center, in pixels.
        """
        pixel_x = self.width / 2 + self.pan_x
        pixel_y = self.height / 2 + self.pan_y
        pixel_x += (zone.x - self.center_x) * self.scale()
        pixel_y += (zone.y - self.center_y) * self.scale()
        return int(pixel_x), int(pixel_y)

    def font(self, size: int) -> pygame.font.Font:
        """Return a font of the given size (fonts are kept for later)."""
        if size not in self.font_cache:
            self.font_cache[size] = pygame.font.Font(None, size)
        return self.font_cache[size]

    # ----- zoom and move -----

    def zoom_by(self, factor: float) -> None:
        """Zoom in (factor above 1) or out, between x1 and x8.

        Args:
            factor: The zoom multiplier.
        """
        self.zoom = min(max(self.zoom * factor, 1.0), self.MAX_ZOOM)
        self.clamp_pan()

    def clamp_pan(self) -> None:
        """Keep the view near the map (no move at all without zoom)."""
        limit = (self.zoom - 1) * max(self.width, self.height) / 2
        self.pan_x = min(max(self.pan_x, -limit), limit)
        self.pan_y = min(max(self.pan_y, -limit), limit)

    def move_with_arrows(self, seconds: float) -> None:
        """Move the view while an arrow key is held.

        Args:
            seconds: The time since the last image.
        """
        keys = pygame.key.get_pressed()
        amount = 700 * seconds
        if keys[pygame.K_LEFT]:
            self.pan_x += amount
        if keys[pygame.K_RIGHT]:
            self.pan_x -= amount
        if keys[pygame.K_UP]:
            self.pan_y += amount
        if keys[pygame.K_DOWN]:
            self.pan_y -= amount
        self.clamp_pan()

    # ----- images -----

    def load_images(self) -> None:
        """Load the drone image (circles are used if it is missing)."""
        self.drone_source = self.load_image(Path("drone.png"))

    def load_image(self, path: Path) -> pygame.Surface | None:
        """Load one image, or return None if the file cannot be loaded."""
        try:
            return pygame.image.load(str(path)).convert_alpha()
        except (FileNotFoundError, pygame.error):
            return None

    def drone_image(self) -> pygame.Surface | None:
        """Return the drone image at the right size.

        Returns:
            The image, or None if there is no drone image.
        """
        if self.drone_source is None:
            return None
        width = max(int(self.DRONE_WIDTH * self.size_factor()), 4)
        ratio = self.drone_source.get_height() / self.drone_source.get_width()
        size = (width, max(int(width * ratio), 4))
        return pygame.transform.smoothscale(self.drone_source, size)

    # ----- drawing -----

    def draw(
        self, screen: pygame.Surface, replay: Replay, fonts: Fonts
    ) -> None:
        """Draw one image of the window.

        Args:
            screen: The window surface.
            replay: The turn shown and the animation.
            fonts: A big font and a small font.
        """
        screen.fill(self.BACKGROUND)
        self.draw_connections(screen)
        for zone in self.fly_map.zones.values():
            self.draw_zone(screen, zone)
        self.draw_drones(screen, replay)
        self.draw_status(screen, replay, fonts)
        pygame.display.flip()

    def draw_connections(self, screen: pygame.Surface) -> None:
        """Draw the connections (thicker when the capacity is bigger)."""
        for connection in self.fly_map.connections:
            base = min(2 + 2 * connection.max_link_capacity, 12)
            pygame.draw.line(
                screen,
                (200, 160, 80),
                self.to_screen(connection.zone_a),
                self.to_screen(connection.zone_b),
                max(int(base * self.size_factor()), 1),
            )

    def draw_zone(self, screen: pygame.Surface, zone: Zone) -> None:
        """Draw one zone: hexagon, border, name and capacity.

        Args:
            screen: The window surface.
            zone: The zone to draw.
        """
        center = self.to_screen(zone)
        radius = self.radius()
        corners = [
            (
                center[0] + radius * math.cos(math.radians(60 * i + 30)),
                center[1] + radius * math.sin(math.radians(60 * i + 30)),
            )
            for i in range(6)
        ]
        color = self.COLORS.get((zone.color or "").lower(), self.HONEY)
        pygame.draw.polygon(screen, color, corners)
        border = self.BORDERS[zone.zone_type]
        pygame.draw.polygon(screen, border, corners, max(radius // 8, 1))
        name_font = self.font(min(max(int(radius * 0.45), 9), 22))
        name = name_font.render(zone.name, True, (255, 255, 255))
        position = (center[0], center[1] + radius + 14)
        screen.blit(name, name.get_rect(center=position))
        self.draw_capacity(screen, zone, center, radius)

    def draw_capacity(
        self,
        screen: pygame.Surface,
        zone: Zone,
        center: tuple[int, int],
        radius: int,
    ) -> None:
        """Draw a badge with the number of drones the zone can hold.

        The start zone, the end zone and the blocked zones have no badge.

        Args:
            screen: The window surface.
            zone: The zone to describe.
            center: The center of the zone, in pixels.
            radius: The radius of the hexagon, in pixels.
        """
        if zone.is_blocked():
            return
        if zone is self.fly_map.start or zone is self.fly_map.end:
            return
        badge = max(int(radius * 0.32), 7)
        x = center[0] + int(radius * 0.5)
        y = center[1] - int(radius * 0.5)
        pygame.draw.circle(screen, (30, 20, 10), (x, y), badge)
        pygame.draw.circle(screen, (255, 235, 150), (x, y), badge, 1)
        font = self.font(max(int(badge * 1.7), 10))
        number = font.render(str(zone.max_drones), True, (255, 255, 255))
        screen.blit(number, number.get_rect(center=(x, y)))

    def positions(self, snapshot: Snapshot) -> list[Point | None]:
        """Compute where each drone is drawn, in pixels.

        Args:
            snapshot: For each drone, its zone and the zone it flies to.

        Returns:
            One point per drone, or None for a delivered drone.
        """
        factor = self.size_factor()
        counters: dict[str, int] = {}
        points: list[Point | None] = []
        for place, flying_to in snapshot:
            zone = self.fly_map.zones[place]
            x, y = self.to_screen(zone)
            if flying_to is not None:
                other_x, other_y = self.to_screen(
                    self.fly_map.zones[flying_to]
                )
                points.append(((x + other_x) / 2, (y + other_y) / 2))
                continue
            rank = counters.get(place, 0)
            counters[place] = rank + 1
            spread = 9.0 if zone is self.fly_map.end else 4.5
            distance = spread * math.sqrt(rank) * factor
            angle = rank * 2.4
            points.append((
                x + distance * math.cos(angle),
                y + distance * math.sin(angle),
            ))
        return points

    def draw_drones(self, screen: pygame.Surface, replay: Replay) -> None:
        """Draw the drones between two turns.

        Args:
            screen: The window surface.
            replay: The turn shown and the animation.
        """
        history = replay.history
        after_index = min(replay.index + 1, len(history) - 1)
        now = self.positions(history[replay.index])
        later = self.positions(history[after_index])
        end_x, end_y = self.to_screen(self.fly_map.end)
        smooth = replay.progress * replay.progress * (3 - 2 * replay.progress)
        drone = self.drone_image()
        for index, (before, after) in enumerate(zip(now, later)):
            if before is None:
                continue
            goal = after if after is not None else (float(end_x), float(end_y))
            x = before[0] + (goal[0] - before[0]) * smooth
            y = before[1] + (goal[1] - before[1]) * smooth
            bob = math.sin(pygame.time.get_ticks() / 250 + index) * 4
            center = (int(x), int(y + bob * self.size_factor()))
            if drone is None:
                radius = max(int(10 * self.size_factor()), 3)
                pygame.draw.circle(screen, (20, 20, 20), center, radius)
                pygame.draw.circle(screen, (255, 210, 40), center, radius - 2)
            else:
                screen.blit(drone, drone.get_rect(center=center))

    def draw_status(
        self, screen: pygame.Surface, replay: Replay, fonts: Fonts
    ) -> None:
        """Write the map, the turn, the delivered drones and the keys.

        Args:
            screen: The window surface.
            replay: The turn shown and the animation.
            fonts: A big font and a small font.
        """
        shown = replay.history[replay.index]
        end_name = self.fly_map.end.name
        delivered = sum(1 for place, _ in shown if place == end_name)
        status = (
            f"Map {self.title}   "
            f"Turn {replay.index}/{len(replay.history) - 1}   "
            f"Delivered {delivered}/{len(shown)}   "
            f"Zoom x{self.zoom:.1f}"
        )
        help_text = (
            "SPACE: next turn   A: auto   R: restart   "
            "WHEEL or +/-: zoom   ARROWS: move when zoomed   "
            "ESC: quit"
        )
        screen.blit(fonts[0].render(status, True, (255, 255, 255)), (15, 12))
        help_image = fonts[1].render(help_text, True, (220, 200, 160))
        screen.blit(help_image, (15, 38))

    # ----- keyboard, mouse and the main loop -----

    def handle_event(self, event: pygame.event.Event, replay: Replay) -> None:
        """React to one event of the window.

        Args:
            event: The event.
            replay: The turn shown and the animation.
        """
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.MOUSEWHEEL:
            self.zoom_by(1.1 ** event.y)
        elif event.type == pygame.KEYDOWN:
            key = event.key
            if key == pygame.K_ESCAPE:
                self.running = False
            elif key == pygame.K_SPACE:
                replay.step()
            elif key == pygame.K_a:
                replay.toggle_auto()
            elif key == pygame.K_r:
                replay.restart()
            elif event.unicode in ("+", "=") or key == pygame.K_KP_PLUS:
                self.zoom_by(1.25)
            elif event.unicode == "-" or key == pygame.K_KP_MINUS:
                self.zoom_by(0.8)

    def play(self, history: list[Snapshot], title: str = "") -> None:
        """Open the window and replay the simulation.

        Args:
            history: The positions of the drones after each turn.
            title: The name of the map, shown in the window.
        """
        pygame.init()
        try:
            screen = pygame.display.set_mode(
                (self.WIDTH, self.HEIGHT), pygame.RESIZABLE
            )
            pygame.display.set_caption("Fly-in")
            self.load_images()
            self.title = title
            replay = Replay(history)
            fonts = (self.font(28), self.font(20))
            clock = pygame.time.Clock()
            self.running = True
            while self.running:
                for event in pygame.event.get():
                    self.handle_event(event, replay)
                seconds = clock.tick(60) / 1000
                replay.update(seconds)
                self.width, self.height = screen.get_size()
                self.move_with_arrows(seconds)
                self.draw(screen, replay, fonts)
        finally:
            pygame.quit()
