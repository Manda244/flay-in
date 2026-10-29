"""Graphical display (pygame) for the Fly-in project."""

import math
from pathlib import Path

import pygame

from src.fly_map import FlyMap
from src.library import MapLibrary
from src.zone import Zone, ZoneType

Color = tuple[int, int, int]
Point = tuple[float, float]
Snapshot = list[tuple[str, str | None]]
Loaded = tuple[FlyMap, list[Snapshot], str]
Fonts = tuple[pygame.font.Font, pygame.font.Font]


class GraphicRenderer:
    """Draw the map in a resizable, zoomable window, like a beehive."""

    WIDTH: int = 1000
    HEIGHT: int = 700
    MARGIN: int = 90
    RADIUS: int = 30
    BEE_WIDTH: int = 46
    QUEEN_HEIGHT: int = 110
    MIN_ZOOM: float = 0.3
    MAX_ZOOM: float = 8.0
    MENU_ROW: int = 28
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
        self.bee_source: pygame.Surface | None = None
        self.queen_source: pygame.Surface | None = None
        self.bee_left: pygame.Surface | None = None
        self.bee_right: pygame.Surface | None = None
        self.queen: pygame.Surface | None = None
        self.sprite_ui: float | None = None
        self.label_fonts: dict[int, pygame.font.Font] = {}
        self.set_map(fly_map)

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
        self.longest_name: int = max(len(name) for name in fly_map.zones)
        self.zoom: float = 1.0
        self.pan_x: float = 0.0
        self.pan_y: float = 0.0

    def view_scale(self) -> float:
        """Return the size factor given by the window and the zoom."""
        window = min(self.width / self.WIDTH, self.height / self.HEIGHT)
        return window * self.zoom

    def map_scale(self) -> float:
        """Return the number of pixels for one unit of the map."""
        room_x = max(self.width - 2 * self.MARGIN, 1)
        room_y = max(self.height - 2 * self.MARGIN, 1)
        fit = min(room_x / self.span_x, room_y / self.span_y)
        return fit * self.zoom

    def radius(self) -> int:
        """Return the radius of a hexagon, in pixels.

        It is limited so that the zones never touch each other.
        """
        wanted = self.RADIUS * self.view_scale()
        room = 0.36 * self.min_gap * self.map_scale()
        return max(int(min(wanted, room)), 3)

    def ui_scale(self) -> float:
        """Return the size factor of the drawings (follows the radius)."""
        return self.radius() / self.RADIUS

    def to_screen(self, zone: Zone) -> tuple[int, int]:
        """Convert the map coordinates of a zone into pixels.

        Args:
            zone: The zone to place.

        Returns:
            The (x, y) position of the zone center, in pixels.
        """
        scale = self.map_scale()
        delta_x = (zone.x - self.center_x) * scale
        delta_y = (zone.y - self.center_y) * scale
        pixel_x = self.width / 2 + self.pan_x + delta_x
        pixel_y = self.height / 2 + self.pan_y + delta_y
        return int(pixel_x), int(pixel_y)

    def zoom_at(self, factor: float, mouse: tuple[int, int]) -> None:
        """Zoom while the point under the mouse stays in place.

        Args:
            factor: The zoom multiplier (more than 1 zooms in).
            mouse: The mouse position, in pixels.
        """
        new_zoom = min(max(self.zoom * factor, self.MIN_ZOOM), self.MAX_ZOOM)
        ratio = new_zoom / self.zoom
        delta_x = mouse[0] - self.width / 2
        delta_y = mouse[1] - self.height / 2
        self.pan_x = delta_x - ratio * (delta_x - self.pan_x)
        self.pan_y = delta_y - ratio * (delta_y - self.pan_y)
        self.zoom = new_zoom
        self.clamp_pan()

    def clamp_pan(self) -> None:
        """Keep the view near the map; the view cannot move without zoom."""
        if self.zoom <= 1.0:
            self.pan_x = 0.0
            self.pan_y = 0.0
            return
        scale = self.map_scale()
        limit_x = self.span_x * scale / 2
        limit_y = self.span_y * scale / 2
        self.pan_x = min(max(self.pan_x, -limit_x), limit_x)
        self.pan_y = min(max(self.pan_y, -limit_y), limit_y)

    def hexagon(self, center: tuple[int, int]) -> list[tuple[float, float]]:
        """Return the six corners of a hexagon.

        Args:
            center: The center of the hexagon, in pixels.

        Returns:
            The corners, as (x, y) pairs.
        """
        radius = self.radius()
        points: list[tuple[float, float]] = []
        for index in range(6):
            angle = math.radians(60 * index + 30)
            points.append((
                center[0] + radius * math.cos(angle),
                center[1] + radius * math.sin(angle),
            ))
        return points

    def zone_color(self, zone: Zone) -> Color:
        """Return the fill color of a zone (honey if unknown)."""
        return self.COLORS.get((zone.color or "").lower(), self.HONEY)

    def draw_honeycomb(self, screen: pygame.Surface) -> None:
        """Fill the window with a dark honeycomb pattern.

        Args:
            screen: The window surface.
        """
        screen.fill(self.BACKGROUND)
        size = 34.0
        width = math.sqrt(3) * size
        row = 0
        y = 0.0
        while y < self.height + size:
            x = 0.0 if row % 2 == 0 else width / 2
            while x < self.width + width:
                points = [
                    (
                        x + size * math.cos(math.radians(60 * i + 30)),
                        y + size * math.sin(math.radians(60 * i + 30)),
                    )
                    for i in range(6)
                ]
                pygame.draw.polygon(screen, (62, 42, 20), points, 1)
                x += width
            y += size * 1.5
            row += 1

    def label_font(self) -> pygame.font.Font:
        """Return a font small enough for the zone names to fit.

        Returns:
            A font whose size follows the distance between the zones.
        """
        gap_pixels = self.min_gap * self.map_scale()
        size = int(gap_pixels / (0.38 * self.longest_name))
        size = min(max(size, 9), 22)
        if size not in self.label_fonts:
            self.label_fonts[size] = pygame.font.Font(None, size)
        return self.label_fonts[size]

    def draw_map(self, screen: pygame.Surface) -> None:
        """Draw the background, the connections and the zones.

        Args:
            screen: The window surface.
        """
        ui = self.ui_scale()
        self.draw_honeycomb(screen)
        for connection in self.fly_map.connections:
            base = min(2 + 2 * connection.max_link_capacity, 12)
            pygame.draw.line(
                screen,
                (200, 160, 80),
                self.to_screen(connection.zone_a),
                self.to_screen(connection.zone_b),
                max(int(base * ui), 1),
            )
        radius = self.radius()
        for zone in self.fly_map.zones.values():
            center = self.to_screen(zone)
            points = self.hexagon(center)
            pygame.draw.polygon(screen, self.zone_color(zone), points)
            pygame.draw.polygon(
                screen,
                self.BORDERS[zone.zone_type],
                points,
                max(int(4 * ui), 1),
            )
            label = self.label_font().render(
                zone.name, True, (255, 255, 255)
            )
            position = (center[0], center[1] + radius + 14)
            screen.blit(label, label.get_rect(center=position))

    def positions(self, snapshot: Snapshot) -> list[Point | None]:
        """Compute where each drone is drawn, in pixels.

        Args:
            snapshot: For each drone, its zone and the zone it flies to.

        Returns:
            One point per drone, or None for a delivered drone.
        """
        ui = self.ui_scale()
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
            distance = 4.5 * math.sqrt(rank) * ui
            angle = rank * 2.4
            points.append((
                center[0] + distance * math.cos(angle),
                center[1] + distance * math.sin(angle),
            ))
        return points

    def draw_drone(self, screen: pygame.Surface, point: Point) -> None:
        """Draw one small bee made of simple shapes.

        Args:
            screen: The window surface.
            point: The center of the bee, in pixels.
        """
        ui = self.ui_scale()
        x, y = int(point[0]), int(point[1])
        wings = (230, 240, 255)
        reach, lift = int(5 * ui), int(8 * ui)
        wing = max(int(5 * ui), 1)
        outer = max(int(10 * ui), 2)
        inner = max(int(8 * ui), 1)
        half = int(6 * ui)
        pygame.draw.circle(screen, wings, (x - reach, y - lift), wing)
        pygame.draw.circle(screen, wings, (x + reach, y - lift), wing)
        pygame.draw.circle(screen, (20, 20, 20), (x, y), outer)
        pygame.draw.circle(screen, (255, 210, 40), (x, y), inner)
        pygame.draw.line(
            screen, (20, 20, 20), (x - half, y), (x + half, y),
            max(int(2 * ui), 1),
        )

    def draw_bee(
        self, screen: pygame.Surface, point: Point, facing_right: bool
    ) -> None:
        """Draw the bee image, or the simple shape if there is no image.

        Args:
            screen: The window surface.
            point: The center of the bee, in pixels.
            facing_right: True if the bee flies toward the right.
        """
        image = self.bee_right if facing_right else self.bee_left
        if image is None:
            self.draw_drone(screen, point)
            return
        center = (int(point[0]), int(point[1]))
        screen.blit(image, image.get_rect(center=center))

    def draw_queen(self, screen: pygame.Surface) -> None:
        """Draw the queen standing on the end zone.

        Args:
            screen: The window surface.
        """
        if self.queen is None:
            return
        center = self.to_screen(self.fly_map.end)
        bottom = (center[0], center[1] + self.radius())
        screen.blit(self.queen, self.queen.get_rect(midbottom=bottom))

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
        self.draw_queen(screen)
        ease = progress * progress * (3 - 2 * progress)
        for before, after in zip(current, following):
            if before is None:
                continue
            goal = after
            if goal is None:
                goal = (float(end_center[0]), float(end_center[1]))
            x = before[0] + (goal[0] - before[0]) * ease
            y = before[1] + (goal[1] - before[1]) * ease
            self.draw_bee(screen, (x, y), goal[0] > before[0])

    def draw_status(
        self,
        screen: pygame.Surface,
        fonts: Fonts,
        history: list[Snapshot],
        index: int,
    ) -> None:
        """Write the map, the turn, the delivered drones and the controls.

        Args:
            screen: The window surface.
            fonts: A big font for the status and a small one for the help.
            history: The positions of the drones after each turn.
            index: The turn being shown.
        """
        end_name = self.fly_map.end.name
        delivered = sum(1 for place, _ in history[index] if place == end_name)
        status = (
            f"Map {self.title}   "
            f"Turn {index}/{len(history) - 1}   "
            f"Delivered {delivered}/{len(history[index])}   "
            f"Zoom x{self.zoom:.1f}"
        )
        help_text = (
            "SPACE: next turn   A: auto   R: restart   "
            "WHEEL or +/-: zoom   ARROWS: move when zoomed   "
            "M: maps   N/P: next map   ESC: quit"
        )
        screen.blit(fonts[0].render(status, True, (255, 255, 255)), (15, 12))
        help_image = fonts[1].render(help_text, True, (220, 200, 160))
        screen.blit(help_image, (15, 38))

    def load_image(self, name: str) -> pygame.Surface | None:
        """Load an image of the "assets" folder.

        Args:
            name: The file name, such as "bee.png".

        Returns:
            The image, or None if the file cannot be loaded.
        """
        path = Path(__file__).resolve().parent.parent / "assets" / name
        try:
            return pygame.image.load(str(path)).convert_alpha()
        except (FileNotFoundError, pygame.error):
            return None

    def load_images(self) -> None:
        """Load the bee and the queen (shapes are used if they are missing)."""
        self.bee_source = self.load_image("bee.png")
        self.queen_source = self.load_image("queen.png")
        self.sprite_ui = None

    def update_sprites(self, ui: float) -> None:
        """Rescale the bee and the queen images to the current size.

        Args:
            ui: The size factor of the drawings.
        """
        ui = min(ui, 6.0)
        if self.sprite_ui is not None and abs(ui - self.sprite_ui) < 0.01:
            return
        self.sprite_ui = ui
        if self.bee_source is not None:
            width = max(int(self.BEE_WIDTH * ui), 4)
            ratio = self.bee_source.get_height() / self.bee_source.get_width()
            self.bee_left = pygame.transform.smoothscale(
                self.bee_source, (width, max(int(width * ratio), 4))
            )
            self.bee_right = pygame.transform.flip(
                self.bee_left, True, False
            )
        if self.queen_source is not None:
            height = max(int(self.QUEEN_HEIGHT * ui), 8)
            ratio = (
                self.queen_source.get_width() / self.queen_source.get_height()
            )
            self.queen = pygame.transform.smoothscale(
                self.queen_source, (max(int(height * ratio), 4), height)
            )

    def handle_view_event(self, event: pygame.event.Event) -> None:
        """React to the zoom controls (wheel, + and -).

        Args:
            event: An event of the window.
        """
        center = (self.width // 2, self.height // 2)
        if event.type == pygame.MOUSEWHEEL:
            self.zoom_at(1.1 ** event.y, pygame.mouse.get_pos())
        elif event.type == pygame.KEYDOWN:
            typed = event.unicode
            if typed in ("+", "=") or event.key == pygame.K_KP_PLUS:
                self.zoom_at(1.25, center)
            elif typed == "-" or event.key == pygame.K_KP_MINUS:
                self.zoom_at(0.8, center)

    def menu_layout(
        self, count: int, choice: int
    ) -> tuple[pygame.Rect, int, int]:
        """Compute where the map menu is drawn.

        Args:
            count: The number of maps in the list.
            choice: The highlighted map.

        Returns:
            The panel rectangle, the number of visible rows and the number
            of the first visible map.
        """
        width = min(560, self.width - 40)
        rows = min(count, max((self.height - 220) // self.MENU_ROW, 3))
        top = max(0, min(choice - rows // 2, count - rows))
        height = rows * self.MENU_ROW + 110
        rect = pygame.Rect((self.width - width) // 2, 80, width, height)
        return rect, rows, top

    def menu_item_at(
        self, position: tuple[int, int], count: int, choice: int
    ) -> int | None:
        """Find the map under the mouse in the menu.

        Args:
            position: The mouse position, in pixels.
            count: The number of maps in the list.
            choice: The highlighted map.

        Returns:
            The number of the map, or None if the mouse is not on a map.
        """
        rect, rows, top = self.menu_layout(count, choice)
        row = (position[1] - (rect.y + 50)) // self.MENU_ROW
        if rect.collidepoint(position) and 0 <= row < rows:
            return top + row
        return None

    def menu_event(
        self, event: pygame.event.Event, library: MapLibrary, choice: int
    ) -> tuple[int | None, int, bool]:
        """React to an event while the map menu is open.

        Args:
            event: An event of the window.
            library: The maps that can be chosen.
            choice: The highlighted map.

        Returns:
            The map to load (or None), the new highlighted map, and
            whether the menu stays open.
        """
        count = len(library.paths)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_m):
                return None, choice, False
            if event.key == pygame.K_UP:
                return None, (choice - 1) % count, True
            if event.key == pygame.K_DOWN:
                return None, (choice + 1) % count, True
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return choice, choice, True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = self.menu_item_at(event.pos, count, choice)
            if clicked is not None:
                return clicked, clicked, True
        return None, choice, True

    def draw_menu(
        self,
        screen: pygame.Surface,
        fonts: Fonts,
        library: MapLibrary,
        choice: int,
        message: str,
    ) -> None:
        """Draw the list of the maps over the window.

        Args:
            screen: The window surface.
            fonts: A big font for the names and a small one for the help.
            library: The maps that can be chosen.
            choice: The highlighted map.
            message: A message to show (empty for none).
        """
        names = library.names()
        rect, rows, top = self.menu_layout(len(names), choice)
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((20, 12, 5, 225))
        screen.blit(panel, rect.topleft)
        pygame.draw.rect(screen, (200, 160, 80), rect, 2)
        heading = fonts[0].render("Choose a map", True, (255, 235, 150))
        screen.blit(heading, (rect.x + 20, rect.y + 14))
        for row in range(rows):
            number = top + row
            y = rect.y + 50 + row * self.MENU_ROW
            current = number == library.index
            if number == choice:
                bar = (rect.x + 10, y - 3, rect.width - 20, self.MENU_ROW - 2)
                pygame.draw.rect(screen, (120, 80, 20), bar)
            color = (255, 215, 0) if current else (255, 255, 255)
            label = names[number] + ("   (current)" if current else "")
            screen.blit(fonts[0].render(label, True, color), (rect.x + 20, y))
        hint = "UP/DOWN: choose   ENTER or click: open   M or ESC: close"
        hint_image = fonts[1].render(hint, True, (220, 200, 160))
        screen.blit(hint_image, (rect.x + 20, rect.bottom - 26))
        if message:
            warning = fonts[1].render(message, True, (255, 120, 120))
            screen.blit(warning, (rect.x + 20, rect.bottom - 48))

    def play(
        self,
        history: list[Snapshot],
        library: MapLibrary | None = None,
        seconds_per_turn: float = 0.8,
    ) -> None:
        """Open the window and replay the simulation.

        Args:
            history: The positions of the drones after each turn.
            library: The maps that can be chosen in the window.
            seconds_per_turn: The duration of one turn on screen.
        """
        pygame.init()
        try:
            screen = pygame.display.set_mode(
                (self.WIDTH, self.HEIGHT), pygame.RESIZABLE
            )
            pygame.display.set_caption("Fly-in")
            self.load_images()
            if library is not None:
                self.title = library.title()
            fonts = (pygame.font.Font(None, 28), pygame.font.Font(None, 20))
            clock = pygame.time.Clock()
            last = len(history) - 1
            index = 0
            progress = 0.0
            moving = False
            auto = False
            menu = False
            choice = 0
            message = ""
            running = True
            while running:
                to_load: int | None = None
                step = 0
                for event in pygame.event.get():
                    self.handle_view_event(event)
                    if event.type == pygame.QUIT:
                        running = False
                    elif menu and library is not None:
                        requested, choice, menu = self.menu_event(
                            event, library, choice
                        )
                        if requested is not None:
                            to_load = requested
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key == pygame.K_SPACE and index < last:
                            moving = True
                        elif event.key == pygame.K_a:
                            auto = not auto
                            moving = moving or progress > 0
                        elif event.key == pygame.K_r:
                            index = 0
                            progress = 0.0
                            moving = False
                            auto = False
                        elif event.key == pygame.K_m and library is not None:
                            menu = True
                            choice = library.index
                            message = ""
                        elif event.key == pygame.K_n:
                            step = 1
                        elif event.key == pygame.K_p:
                            step = -1
                loaded: Loaded | None = None
                if library is not None and to_load is not None:
                    loaded = library.select(to_load)
                    message = "" if loaded else "This map cannot be loaded"
                elif library is not None and step != 0:
                    loaded = library.switch(step)
                if loaded is not None:
                    self.set_map(loaded[0])
                    history = loaded[1]
                    self.title = loaded[2]
                    last = len(history) - 1
                    index = 0
                    progress = 0.0
                    moving = False
                    auto = False
                    menu = False
                seconds = clock.tick(60) / 1000
                if (moving or auto) and index < last:
                    progress += seconds / seconds_per_turn
                    if progress >= 1.0:
                        index += 1
                        progress = 0.0
                        moving = False
                        if index >= last:
                            auto = False
                self.width, self.height = screen.get_size()
                if not menu:
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
                self.update_sprites(self.ui_scale())
                self.draw_map(screen)
                self.draw_drones(screen, history, index, progress)
                self.draw_status(screen, fonts, history, index)
                if menu and library is not None:
                    self.draw_menu(screen, fonts, library, choice, message)
                pygame.display.flip()
        finally:
            pygame.quit()
