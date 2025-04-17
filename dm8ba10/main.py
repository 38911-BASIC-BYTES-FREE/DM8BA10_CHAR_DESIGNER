import time
import sys
import math
import pygame
import pygame.freetype
from pygame.locals import *

pygame.init()
screen = pygame.display.set_mode((1180, 720), RESIZABLE)
pygame.display.set_caption("DM8BA10 Font Designer Tool")

font = pygame.freetype.SysFont("Arial", 0, True)

font_monospace = pygame.freetype.SysFont("Consolas", 0, True)
font_monospace.origin = True

values = [[True for _ in range(16)] for _ in range(256)]

help_text = """
    Toggle segments with the left mouse button.
    
    Cycle between characters with arrow keys
    or the scroll wheel.
    
    You can also press the desired character
    on your keyboard to instantly switch to it.
    
    Some helpful shortcuts:
    F1 - Toggle help information
    
    F2 - Clear the current character
    F3 - Fill the current character
    
    F4 - Copy the character map to the clipboard
    F5 - Copy the character map to the clipboard
           (with '#' comments)
    F6 - Copy the character map to the clipboard
           (with '//' comments)
"""

try:
    with open("data.txt", "r") as f:
        data = f.read().split("\n")

        for i, part in enumerate(data):
            for j, char in enumerate(part):
                values[i][j] = char == "1"
except OSError:
    pass

def s(x):
    return x / 720 * screen.height


def flipped_x(points):
    for point in points:
        yield 1.0 - point[0], point[1]


def flipped_y(points):
    for point in points:
        yield point[0], 1.0 - point[1]


class ProceduralAnim:
    __slots__ = "pos", "_vel", "target", "_prev_target", "_k1", "_k2", "_k3", "_last_update", "_snap_vel", "_snap_pos"

    def __init__(self, pos: float, target: float, frequency: float, prevent_vibration: float, initial_response: float):
        self.pos: float = pos
        self._vel: float = 0.0
        self.target: float = target
        self._prev_target: float = target
        self._k1: float = prevent_vibration / (math.pi * frequency)
        self._k2: float = 1 / ((2 * math.pi * frequency) ** 2)
        self._k3: float = initial_response * prevent_vibration / (2 * math.pi * frequency)

        self._last_update = time.perf_counter()

        self._snap_vel = 0.01
        self._snap_pos = 0.005

    def set_snapping(self, vel, pos):
        self._snap_vel = vel
        self._snap_pos = pos

    def modify_curve(self, frequency: float, prevent_vibration: float, initial_response: float):
        self._k1: float = prevent_vibration / (math.pi * frequency)
        self._k2: float = 1 / ((2 * math.pi * frequency) ** 2)
        self._k3: float = initial_response * prevent_vibration / (2 * math.pi * frequency)

    def update(self):
        t = time.perf_counter() - self._last_update

        target_vel: float = (self.target - self._prev_target) * t
        self._prev_target = self.target

        k2_s: float = max(self._k2, t * t / 2 + t * self._k1 / 2, t * self._k1)
        self.pos += self._vel * t
        self._vel += t * ((self.target - self.pos) + self._k3 * target_vel - self._vel * t - self._k1 * self._vel) / k2_s

        if abs(self._vel) < self._snap_vel and abs(self.pos - self.target) < self._snap_pos:
            self.pos = self.target
            self._vel = 0.0

        self._last_update = time.perf_counter()

        return self.pos


class ResizableSurface:
    __slots__ = "last_size", "desired_size", "original_surface", "surface"

    def __init__(self, original_surface, size):
        self.last_size = -1
        self.desired_size = size
        self.original_surface = original_surface
        self.surface = original_surface

    @property
    def get(self):
        if self.last_size != s(self.desired_size[0]):
            self.last_size = s(self.desired_size[0])

            self.surface = pygame.transform.smoothscale(self.original_surface, (s(self.desired_size[0]), s(self.desired_size[1])))
        return self.surface


up_left = (0.375, 0.125)
down_left = (0.375, 0.875)
up_right = (0.625, 0.125)
down_right = (0.625, 0.875)

left_up = (0.125, 0.375)
left_down = (0.125, 0.625)
right_up = (0.875, 0.375)
right_down = (0.875, 0.625)

max_val = 1.2
min_val = -0.2

polygons = [
    [  # 0
        (0.5, 1.0),
        down_right,
        (1.0, 1.0),
        (max_val, max_val),
        (0.5, max_val)
    ],
    [  # 1
        (1.0, 0.5),
        right_down,
        (1.0, 1.0),
        (max_val, max_val),
        (max_val, 0.5)
    ],
    [  # 2
        (0.5, 0.5),
        right_down,
        (1.0, 1.0),
        down_right
    ],
    [  # 3
        (1.0, 0.5),
        right_down,
        (0.5, 0.5),
        right_up
    ],
    [  # 4
        (0.5, 0.5),
        right_up,
        (1.0, 0.0),
        up_right
    ],
    [  # 5
        (1.0, 0.5),
        right_up,
        (1.0, 0.0),
        (max_val, min_val),
        (max_val, 0.5)
    ],
    [  # 6
        (0.5, 0.0),
        up_left,
        (0.5, 0.5),
        up_right
    ],
    [  # 7
        (0.5, 0.0),
        up_right,
        (1.0, 0.0),
        (max_val, min_val),
        (0.5, min_val)
    ],
    [  # 8
        (0.5, 1.0),
        down_left,
        (0.0, 1.0),
        (min_val, max_val),
        (0.5, max_val)
    ],
    [  # 9
        (0.0, 0.5),
        left_down,
        (0.0, 1.0),
        (min_val, max_val),
        (min_val, 0.5)
    ],
    [  # 10
        (0.5, 1.0),
        down_left,
        (0.5, 0.5),
        down_right
    ],
    [  # 11
        (0.5, 0.5),
        left_down,
        (0.0, 1.0),
        down_left
    ],
    [  # 12
        (0.0, 0.5),
        left_down,
        (0.5, 0.5),
        left_up
    ],
    [  # 14
        (0.0, 0.5),
        left_up,
        (0.0, 0.0),
        (min_val, min_val),
        (min_val, 0.5)
    ],
    [  # 13
        (0.5, 0.5),
        left_up,
        (0.0, 0.0),
        up_left
    ],
    [  # 15
        (0.5, 0.0),
        up_left,
        (0.0, 0.0),
        (min_val, min_val),
        (0.5, min_val)
    ],
]

lcd_bar_vertical = (
    (0.44, 0.145),
    (0.56, 0.145),
    (0.56, 0.405),
    (0.5, 0.45),
    (0.44, 0.405)
)

lcd_bar_horizontal = (
    (0.47, 0.5),
    (0.41, 0.54),
    (0.13, 0.54),
    (0.07, 0.5),
    (0.13, 0.46),
    (0.41, 0.46)
)

lcd_bar_side = (
    (0.0, 0.05),
    (0.1, 0.09),
    (0.1, 0.4),
    (0.0, 0.475)
)

lcd_bar_top = (
    (0.1, 0.0),
    (0.08, 0.0075),
    (0.05, 0.025),
    (0.2, 0.08),
    (0.475, 0.08),
    (0.475, 0.0)
)

lcd_bar_diagonal = (
    (0.17, 0.145),
    (0.37, 0.29),
    (0.37, 0.39),
    (0.17, 0.245),
)

disp_polygons = (
    tuple(flipped_x(flipped_y(lcd_bar_top))),
    tuple(flipped_x(flipped_y(lcd_bar_side))),
    tuple(flipped_x(flipped_y(lcd_bar_diagonal))),
    tuple(flipped_x(lcd_bar_horizontal)),
    tuple(flipped_x(lcd_bar_diagonal)),
    tuple(flipped_x(lcd_bar_side)),
    lcd_bar_vertical,
    tuple(flipped_x(lcd_bar_top)),
    tuple(flipped_y(lcd_bar_top)),
    tuple(flipped_y(lcd_bar_side)),
    tuple(flipped_y(lcd_bar_vertical)),
    tuple(flipped_y(lcd_bar_diagonal)),
    lcd_bar_horizontal,
    lcd_bar_side,
    lcd_bar_diagonal,
    lcd_bar_top
)


def dist(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def area_triangle(p1, p2, p3):
    a = dist(p1, p2)
    b = dist(p2, p3)
    c = dist(p1, p3)
    s = (a + b + c) / 2

    return (s * (s - a) * (s - b) * (s - c)) ** 0.5


def get_value(x: list[bool]):
    numeric_value: int = 0

    for i, val in enumerate(x):
        if val:
            numeric_value += 2 ** i

    return numeric_value


button_animators = [ProceduralAnim(0.0, 0.0, 5, 0.4, 0.0) for _ in range(4)]
button_color_animators = [ProceduralAnim(0.0, 0.0, 0.9, 1.0, 0.0) for _ in range(4)]
button_texts = [
    "Copy all ('//' comments)",
    "Copy all ('#' comments)",
    "Copy all hex values",
    "Clear/fill character"
]

temp_surf = pygame.Surface((2, 2))
temp_surf.set_at((0, 0), (12, 187, 245))
temp_surf.set_at((1, 0), (2, 173, 230))
temp_surf.set_at((0, 1), (2, 225, 245))
temp_surf.set_at((1, 1), (18, 249, 252))

neon_bg: ResizableSurface = ResizableSurface(temp_surf, (screen.height * 0.8, screen.height))

ascii_id = ProceduralAnim(65, 65, 4, 1, 0)

show_help: bool = False
help_animator = ProceduralAnim(0.0, 0.0, 3, 0.4, 0.0)
help_animator.set_snapping(0.0001, 0.0001)

outline_animator = ProceduralAnim(0.0, 0.0, 6.5, 1.0, 0.0)
outline_animator.set_snapping(0.0001, 0.0001)

while True:
    screen.fill((24, 24, 24))

    rect: pygame.Rect = Rect(screen.height * 0.15, screen.height * 0.15, screen.height * 0.5, screen.height * 0.7)
    bg_rect: pygame.Rect = Rect(0, 0, screen.height * 0.8, screen.height)

    button_rects = [
        Rect(s(666), s(612) - s(60), s(420), s(60)),
        Rect(s(666), s(612) - s(135), s(420), s(60)),
        Rect(s(666), s(612) - s(210), s(420), s(60)),
        Rect(s(666), s(612) - s(285), s(420), s(60))
    ]

    for event in pygame.event.get():
        if event.type == QUIT:
            with open("data.txt", "w") as f:
                data = f.write("\n".join((
                    "".join(map(lambda a: "1" if a else "0", val)) for val in values
                )))

            sys.exit()

        elif event.type == MOUSEWHEEL:
            ascii_id.target += event.y
            ascii_id.target %= 256

            show_help = False
            help_animator.target = 0.0

        if event.type == KEYDOWN:
            if event.key == K_LEFT or event.key == K_DOWN:
                ascii_id.target -= 1
                ascii_id.target %= 256
            elif event.key == K_RIGHT or event.key == K_UP:
                ascii_id.target += 1
                ascii_id.target %= 256
            elif event.key == K_F1 or event.key == K_ESCAPE:
                show_help = not show_help
                help_animator.target = 1.0 if show_help else 0.0
            elif event.key == K_F2:
                values[int(ascii_id.target)] = [False for _ in range(16)]
                button_animators[3].pos = 1.0
                button_color_animators[3].pos = 1.0
            elif event.key == K_F3:
                values[int(ascii_id.target)] = [True for _ in range(16)]
                button_animators[3].pos = 1.0
                button_color_animators[3].pos = 1.0
            elif event.key == K_F4:
                text = "\n".join("0x" + hex(get_value(val))[2:].upper().rjust(4, "0") for val in values)
                pygame.scrap.put_text(text)
                button_animators[2].pos = 1.0
                button_color_animators[2].pos = 1.0
            elif event.key == K_F5:
                text = "\n".join("0x" + hex(get_value(val))[2:].upper().rjust(4, "0") + ",  # " + str(chr(max(32, i))) for i, val in enumerate(values))
                pygame.scrap.put_text(" ".join(text.rsplit(",", 1)))
                button_animators[1].pos = 1.0
                button_color_animators[1].pos = 1.0
            elif event.key == K_F6:
                text = "\n".join("0x" + hex(get_value(val))[2:].upper().rjust(4, "0") + ",  // " + str(chr(max(32, i))) for i, val in enumerate(values))
                pygame.scrap.put_text(" ".join(text.rsplit(",", 1)))
                button_animators[0].pos = 1.0
                button_color_animators[0].pos = 1.0
            else:
                try:
                    ascii_id.target = ord(event.unicode)
                except TypeError:
                    pass
            if event.key != K_F1 and event.key != K_ESCAPE and show_help:
                show_help = False
                help_animator.target = 0.0

        elif event.type == MOUSEBUTTONDOWN:
            if event.button != 1:
                continue
            if event.pos[0] < screen.height * 0.8:
                if show_help:
                    continue
                if event.pos[0] < rect.left + min_val * rect.width:
                    continue
                if event.pos[0] > rect.left + max_val * rect.width:
                    continue
                if event.pos[1] < rect.top + min_val * rect.height:
                    continue
                if event.pos[1] > rect.top + max_val * rect.height:
                    continue

                winner: int = 0

                for i, polygon in enumerate(polygons):
                    click_point: tuple[float, float] = (
                        pygame.math.remap(rect.left, rect.right, 0.0, 1.0, event.pos[0]),
                        pygame.math.remap(rect.top, rect.bottom, 0.0, 1.0, event.pos[1])
                    )

                    area: float = 0.0
                    click_area: float = 0.0

                    if len(polygon) == 5:
                        area += area_triangle(polygon[0], polygon[1], polygon[2])
                        area += area_triangle(polygon[0], polygon[2], polygon[3])
                        area += area_triangle(polygon[0], polygon[3], polygon[4])
                        click_area += area_triangle(click_point, polygon[0], polygon[1])
                        click_area += area_triangle(click_point, polygon[1], polygon[2])
                        click_area += area_triangle(click_point, polygon[2], polygon[3])
                        click_area += area_triangle(click_point, polygon[3], polygon[4])
                        click_area += area_triangle(click_point, polygon[4], polygon[0])

                    if len(polygon) == 4:
                        area += area_triangle(polygon[0], polygon[1], polygon[2])
                        area += area_triangle(polygon[0], polygon[3], polygon[2])
                        click_area += area_triangle(click_point, polygon[0], polygon[1])
                        click_area += area_triangle(click_point, polygon[1], polygon[2])
                        click_area += area_triangle(click_point, polygon[2], polygon[3])
                        click_area += area_triangle(click_point, polygon[3], polygon[0])

                    if click_area < area + 0.001:
                        winner = i
                        break

                values[int(ascii_id.target)][winner] = not values[int(ascii_id.target)][winner]
            else:
                for i, (button, anim, anim2) in enumerate(zip(button_rects, button_animators, button_color_animators)):
                    if button.collidepoint(event.pos):
                        show_help = False
                        help_animator.target = 0.0
                        anim.pos = 1.0
                        anim2.pos = 1.0
                        match i:
                            case 0:
                                text = "\n".join("0x" + hex(get_value(val))[2:].upper().rjust(4, "0") + ",  // " + str(chr(max(32, i))) for i, val in enumerate(values))
                                pygame.scrap.put_text(" ".join(text.rsplit(",", 1)))
                            case 1:
                                text = "\n".join("0x" + hex(get_value(val))[2:].upper().rjust(4, "0") + ",  # " + str(chr(max(32, i))) for i, val in enumerate(values))
                                pygame.scrap.put_text(" ".join(text.rsplit(",", 1)))
                            case 2:
                                text = "\n".join("0x" + hex(get_value(val))[2:].upper().rjust(4, "0") for val in values)
                                pygame.scrap.put_text(text)
                            case 3:
                                all_empty = True
                                for val in values[int(ascii_id.target)]:
                                    all_empty = all_empty and not val

                                values[int(ascii_id.target)] = [all_empty for _ in range(16)]

    ascii_id.update()
    help_animator.update()

    outline_animator.target = 1.0 if pygame.mouse.get_pos()[0] < screen.height * 0.8 else 0.0
    outline_animator.update()

    screen.blit(neon_bg.get, (0, 0))

    for polygon, val in zip(disp_polygons, values[int(ascii_id.target)]):
        points = tuple(map(lambda a: (rect.left + a[0] * rect.width, rect.top + a[1] * rect.height - screen.height * help_animator.pos), polygon))
        if val:
            pygame.draw.polygon(screen, (0, 24, 204), points)
        elif outline_animator.pos > 0.0001:
            avg_x: float = 0.0
            avg_y: float = 0.0

            for point in polygon:
                avg_x += point[0]
                avg_y += point[1]

            avg_x /= len(polygon)
            avg_y /= len(polygon)

            p = tuple(map(lambda a: (
                rect.left + pygame.math.lerp(avg_x, a[0], outline_animator.pos) * rect.width,
                rect.top + pygame.math.lerp(avg_y, a[1], outline_animator.pos) * rect.height - screen.height * help_animator.pos
            ), polygon))

            pygame.draw.aalines(screen, (2, 173, 230), True, p)

    font_monospace.size = s(48)
    font.size = s(24)

    text_x = bg_rect.left + s(6)
    text_y = bg_rect.top + s(20)

    for line in help_text.split("\n"):
        font.render_to(screen, (text_x, text_y + screen.height * (1 - help_animator.pos)), line, (0, 24, 204))
        text_y += s(32)

    text_x = bg_rect.right + 90
    text_y = rect.top

    font.render_to(screen, (text_x + s(2), text_y), "Binary", (128, 128, 128))
    text_y += s(56)

    text = bin(get_value(values[int(ascii_id.target)]))[2::].rjust(16, "0")
    font_monospace.render_to(screen, (text_x, text_y), text, (225, 225, 225))
    text_y += s(16)

    font.render_to(screen, (text_x + s(2), text_y), "Hexadecimal", (128, 128, 128))
    font.render_to(screen, (text_x + s(172), text_y), "Ascii", (128, 128, 128))
    font.render_to(screen, (text_x + s(282), text_y), "Symbol", (128, 128, 128))
    text_y += s(56)

    text = hex(get_value(values[int(ascii_id.target)]))[2::].rjust(4, "0").upper()
    font_monospace.render_to(screen, (text_x, text_y), text, (255, 255, 255))
    font_monospace.render_to(screen, (text_x + s(170), text_y), str(int(round(ascii_id.pos))), (255, 255, 255))
    font_monospace.render_to(screen, (text_x + s(280), text_y), chr(int(ascii_id.target)), (255, 255, 255))
    text_y += s(16)

    for rect, anim, anim2, text in zip(button_rects, button_animators, button_color_animators, button_texts):
        anim.update()
        anim2.update()

        font.size = s(24) + s(5) * anim.pos

        pygame.draw.rect(screen, Color(225, 225, 225).lerp(Color(74, 247, 152), max(0.0, min(1.0, anim2.pos))), rect.inflate(anim.pos * s(40), anim.pos * s(40)), int(s(4)))

        surf, r = font.render(text, Color(225, 225, 225).lerp(Color(74, 247, 152), max(0.0, min(1.0, anim2.pos))))

        r.center = rect.center
        screen.blit(surf, r)

    font.size = s(16)
    font.render_to(screen, (s(10), s(10)), "F1 - Help", (2, 225, 245))

    pygame.display.flip()
